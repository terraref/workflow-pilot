#!/usr/bin/python

import argparse
import logging
import json
import numpy as np
from PIL import Image, ImageFilter

from terrautils.spatial import geojson_to_tuples
from terrautils.formats import create_geotiff


logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger("nrmac")

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--left", required=True, help="Input left tif file")
parser.add_argument("-r", "--right", required=True, help="Input right tif file")
parser.add_argument("-m", "--meta", required=True, help="Input clean_metadata.json file")
parser.add_argument("--out_l", required=True, help="Left output")
parser.add_argument("--out_r", required=True, help="Right output")
parser.add_argument("--out_j", required=True, help="JSON output")
parser.add_argument("-v", "--verbose", help="Debug logging", action="store_true")

args = parser.parse_args()
if args.verbose:
    logger.setLevel(logging.DEBUG)

def MAC(im1,im2, im): # main function: Multiscale Autocorrelation (MAC)
    h, v, c = im1.shape
    if c>1:
        im  = np.matrix.round(rgb2gray(im))
        im1 = np.matrix.round(rgb2gray(im1))
        im2 = np.matrix.round(rgb2gray(im2))
        # multiscale parameters
    scales = np.array([2, 3, 5])
    FM = np.zeros(len(scales))
    for s in range(len(scales)):
        im1[0: h-1,:] = im[1:h,:]
        im2[0: h-scales[s], :]= im[scales[s]:h,:]
        dif = im*(im1 - im2)
        FM[s] = np.mean(dif)
    NRMAC = np.mean(FM)
    return NRMAC

def rgb2gray(rgb):
    r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray

def nrmac(imgfile):
    img = Image.open(imgfile)
    img = np.array(img)

    NRMAC = MAC(img, img, img)

    return NRMAC


with open(args.meta, 'r') as mdfile:
    md = json.load(mdfile)

lbounds = geojson_to_tuples(md['spatial_metadata']['left']['bounding_box'])
rbounds = geojson_to_tuples(md['spatial_metadata']['right']['bounding_box'])

logger.debug("Calculating quality scores")
left_qual = nrmac(args.left)
right_qual = nrmac(args.right)

# Create geoTIFF with left image quality score
logger.debug("Saving quality scores as rasters")
create_geotiff(np.array([[left_qual,left_qual],[left_qual,left_qual]]), lbounds, args.out_l)
create_geotiff(np.array([[right_qual,right_qual],[right_qual,right_qual]]), rbounds, args.out_r)

with open(args.out_j, 'w') as o:
    o.write(json.dumps({
        "quality_score": {
            "left": left_qual,
            "right": right_qual
        }
    }))
