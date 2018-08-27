#!/usr/bin/python

import argparse
import logging
import json




logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger("nrmac")

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", required=True, help="Input geo CSV file")
parser.add_argument("-t", "--type", required=True, help="Type of trait in geo CSV")
parser.add_argument("-v", "--verbose", help="Debug logging", action="store_true")

args = parser.parse_args()
if args.verbose:
    logger.setLevel(logging.DEBUG)


logger.debug("Cleaning metadata.json contents")
with open(args.meta, 'r') as mdfile:
    j = json.load(mdfile)
    md = clean_metadata(j, "stereoTop")

lbounds = geojson_to_tuples(md['spatial_metadata']['left']['bounding_box'])

logger.debug("Calculating quality scores")
left_qual = nrmac(args.left)
right_qual = nrmac(args.right)

# Create geoTIFF with left image quality score
logger.debug("Saving left quality score as raster")
create_geotiff(np.array([[left_qual,left_qual],[left_qual,left_qual]]), lbounds, args.out_l)

with open(args.out_j, 'w') as o:
    o.write(json.dumps({
        "quality_score": {
            "left": left_qual,
            "right": right_qual
        }
    }))
