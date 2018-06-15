#!/usr/bin/python

import argparse
import glob
import logging
import numpy as np
import os
from PIL import Image
import requests
import sys

from terrautils.metadata import get_terraref_metadata
from terrautils.spatial import geojson_to_tuples
from terrautils.formats import create_geotiff, create_image
import bin_to_geotiff as bin2tiff
import utils as utils

from terrautils.sensors import Sensors

#
# Simple example of bin2tif process.  Given an input stereoTop directory for a
# given time, generate output geotiffs. This still has a dependency on 
# Clowder to retrieve dataset metadata, which is undesirable.
#
# python bin2tif.py -i /data/terraref/sites/ua-mac/raw_data/stereoTop/2018-05-01/2018-05-01__09-08-02-749 -o output
#

logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger("bin2tif")

parser = argparse.ArgumentParser()

parser.add_argument("-i", "--input", required=True, help="Input directory")
parser.add_argument("-o", "--output", required=True, help="Output directory")
parser.add_argument("-k", "--key", required=True, help="Clowder API key") #
parser.add_argument("-v", "--verbose", help="Debug logging", action="store_true")

args = parser.parse_args()

if args.verbose:
    logger.setLevel(logging.DEBUG)

key = args.key 

if not os.path.exists(args.input):
    logger.error("Input directory does not exist.")
    sys.exit(1)
    
files = glob.glob(args.input + "/*.json")
if len(files) != 1:
    logger.error("Expected one metadata.json file, found %d" % len(files))
    sys.exit(1)
    
metadata_file = files[0]
timestamp = metadata_file[args.input.rfind("/")+1:len(args.input)]
logger.debug("Timestamp %s" % timestamp)

id = metadata_file[metadata_file.rfind("/")+1:metadata_file.rfind("_")]
if not id:
    logger.error("Unable to get daw ID from filename %s" % metadata_file)
    sys.exit(1)
else:      
    logger.debug("Raw ID: %s" % id)

logger.debug("Getting final sensor metadata from Clowder")
metadata = utils.get_clowder_metadata(key, timestamp)

img_left = args.input + "/" + id + "_left.bin"
if not os.path.exists(img_left):
    logger.error("Left image %s not found" % img_left)
    sys.exit(1)

img_right = args.input + "/" + id + "_right.bin"
if not os.path.exists(img_right):
    logger.error("Left image %s not found" % img_right)
    sys.exit(1)
    
logger.debug("Processing raw image data")
left_shape = bin2tiff.get_image_shape(metadata, 'left')
right_shape = bin2tiff.get_image_shape(metadata, 'right')
left_gps_bounds = geojson_to_tuples(metadata['spatial_metadata']['left']['bounding_box'])
right_gps_bounds = geojson_to_tuples(metadata['spatial_metadata']['right']['bounding_box'])
left_image = bin2tiff.process_image(left_shape, img_left, None)
right_image = bin2tiff.process_image(right_shape, img_right, None)

logger.debug("Creating output directories")
sensors = Sensors(base=args.output, station="ua-mac", sensor="rgb_geotiff")
left_tiff = sensors.create_sensor_path(timestamp, opts=['left'])
right_tiff = sensors.create_sensor_path(timestamp, opts=['right'])

logger.debug("Generating geotiffs")
# TODO: Extractor Info is None here, which isn't good
create_geotiff(left_image, left_gps_bounds, left_tiff, None, False, None, metadata)
create_geotiff(right_image, right_gps_bounds, right_tiff, None, False, None, metadata)
