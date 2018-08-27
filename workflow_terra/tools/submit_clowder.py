#!/usr/bin/python

import argparse
import logging
import os

from pyclowder.connectors import Connector
from terrautils.extractors import build_dataset_hierarchy, upload_to_dataset


logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger("nrmac")

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--dir", required=True, help="Directory containing files and metadata")
parser.add_argument("-t", "--type", required=True, help="Directory sensor type")
parser.add_argument("-s", "--scan", required=True, help="Scan name")
parser.add_argument("-v", "--verbose", help="Debug logging", action="store_true")

args = parser.parse_args()
if args.verbose:
    logger.setLevel(logging.DEBUG)


host = "https://terraref.ncsa.illinois.edu/clowder/"
secret_key = ""
clow_user = "terrarefglobus+uamac@ncsa.illinois.edu"
clow_pass = ""
# TODO: Make a new space for Pegasus reprocessing
clowspace = "59d3e9594f0c888ad6ca1279"

if args.type == "rgb_geotiff":
    """
        rgb_geotiff_L1_ua-mac_%s_left.tif % ts
        rgb_geotiff_L1_ua-mac_%s_right.tif % ts
        clean_metadata.json -> dataset

        rgb_geotiff_L1_ua-mac_%s_nrmac_left.tif % ts
        rgb_geotiff_L1_ua-mac_%s_nrmac_right.tif % ts
        nrmac_scores.json -> nrmac.tif files

        write clowder_ids.json
    """
    print("Submission of RGB GeoTIFF would happen now")
    timestamp = args.dir.split("/")[-2]
    files = os.listdir(args.dir)

elif args.type == "fullfield":
    """
        fullfield_L1_ua-mac_%s_%s_nrmac.vrt % (day, args.scan)
        fullfield_L1_ua-mac_%s_%s_nrmac.tif % (day, args.scan)

        fullfield_L1_ua-mac_%s_%s.vrt % (day, args.scan)
        fullfield_L1_ua-mac_%s_%s.tif % (day, args.scan)
        fullfield_L1_ua-mac_%s_%s_thumb.tif % (day, args.scan)
        fullfield_L1_ua-mac_%s_%s_10pct.tif % (day, args.scan)
        fullfield_L1_ua-mac_%s_%s.png % (day, args.scan)

        fullfield_L1_ua-mac_%s_%s_canopycover_bety.csv % (day, args.scan)
        fullfield_L1_ua-mac_%s_%s_canopycover_geo.csv % (day, args.scan)

        write clowder_ids.json
    """
    print("Submission of Full Field Mosaic would happen now")
    date = args.dir.split("/")[-2]
    files = os.listdir(args.dir)

    # TODO: Can each scan be in a separate folder in Clowder?
