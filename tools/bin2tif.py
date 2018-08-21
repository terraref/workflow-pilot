#!/usr/bin/python

import argparse
import logging
import os
import sys
import json

from terrautils.sensors import Sensors
from terrautils.metadata import clean_metadata
from terrautils.spatial import geojson_to_tuples
import terraref.stereo_rgb


logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger("bin2tif")

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--left", required=True, help="Left bin file")
parser.add_argument("-r", "--right", required=True, help="Right bin file")
parser.add_argument("-m", "--meta", required=True, help="Metadata json file")
parser.add_argument("-t", "--timestamp", required=True, help="Dataset timestamp")
parser.add_argument("-o", "--output", required=True, help="Output directory")
parser.add_argument("-v", "--verbose", help="Debug logging", action="store_true")

args = parser.parse_args()
if args.verbose:
    logger.setLevel(logging.DEBUG)

for inputfile in [args.left, args.right, args.meta]:
    if not os.path.isfile(inputfile):
        logger.error("Input does not exist: %s" % inputfile)
        sys.exit(1)

logger.debug("Cleaning metadata.json contents")
with open(args.meta, 'r') as mdfile:
    j = json.load(mdfile)
    md = clean_metadata(j, "stereoTop")

logger.debug("Preparing embedded geotiff metadata")
experiment_names = []
for e in md["experiment_metadata"]:
    experiment_names.append(e["name"])
tif_meta = {
    "datetime": str(md["gantry_variable_metadata"]["datetime"]),
    "sensor_id": str(md["sensor_fixed_metadata"]["sensor_id"]),
    "sensor_url": str(md["sensor_fixed_metadata"]["url"]),
    "experiment_name": ", ".join(experiment_names),
    "extractor_name": "terra.stereo-rgb.bin2tif",
    "extractor_version": "1.1",
    "extractor_author": "Max Burnette <mburnet2@illinois.edu>",
    "extractor_description": "Stereo RGB Image Bin to GeoTIFF Converter (Pegasus environment)",
    "extractor_repo": "https://github.com/terraref/extractors-stereo-rgb.git"
}

logger.debug("Creating output directories")
sensors = Sensors(base=args.output, station="ua-mac", sensor="rgb_geotiff")
left_tiff = sensors.create_sensor_path(args.timestamp, opts=['left'])
right_tiff = sensors.create_sensor_path(args.timestamp, opts=['right'])

logger.debug("Generating geotiffs")
lshape  = terraref.stereo_rgb.get_image_shape(md, 'left')
lbounds = geojson_to_tuples(md['spatial_metadata']['left']['bounding_box'])
rshape  = terraref.stereo_rgb.get_image_shape(md, 'right')
rbounds = geojson_to_tuples(md['spatial_metadata']['right']['bounding_box'])

terraref.stereo_rgb.bin2tif(args.left, left_tiff, lshape, lbounds, tif_meta)
terraref.stereo_rgb.bin2tif(args.right, right_tiff, rshape, rbounds, tif_meta)

logger.debug("Writing cleaned metadata to file")
clean_md_file = os.path.join(os.path.dirname(left_tiff, "clean_metadata.json"))
with open(clean_md_file, 'w') as cmdfile:
    cmdfile.write(json.dumps(md))
