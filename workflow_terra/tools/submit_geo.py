#!/usr/bin/python

import argparse
import logging

from pyclowder.connectors import Connector
from pyclowder.files import upload_metadata
from terrautils.extractors import build_dataset_hierarchy, upload_to_dataset, build_metadata
from terrautils.geostreams import create_datapoint_with_dependencies


logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger("nrmac")

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", required=True, help="Input geo CSV file")
parser.add_argument("-c", "--clowderid", required=True, help="Clowder id of fullfield file used to generate")
parser.add_argument("-v", "--verbose", help="Debug logging", action="store_true")

args = parser.parse_args()
if args.verbose:
    logger.setLevel(logging.DEBUG)


host = "https://terraref.ncsa.illinois.edu/clowder/"
secret_key = ""

def upload_to_geostreams(file, clowder_id):
    conn = Connector(None , mounted_paths={"/home/clowder/sites":"/home/clowder/sites"})

    successful_plots = 0
    with open(file, 'rb') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            centroid_lonlat = [row['lon'], row['lat']]
            time_fmt = row['dp_time']
            timestamp = row['timestamp']
            dpmetadata = {
                "source": row['source'],
                "value": row['value']
            }
            trait = row['trait']

            create_datapoint_with_dependencies(conn, host, secret_key, trait,
                                               (centroid_lonlat[1], centroid_lonlat[0]), time_fmt, time_fmt,
                                               dpmetadata, timestamp)
            successful_plots += 1

    # Extractor metadata
    extractor_info = {
        "extractor_name": "terra.geostreams",
        "extractor_version": "1.0",
        "extractor_author": "Max Burnette <mburnet2@illinois.edu>",
        "extractor_description": "Geostreams CSV uploader",
        "extractor_repo": "https://github.com/terraref/computing-pipeline.git"
    }

    # Add metadata to original dataset indicating this was run
    ext_meta = build_metadata(host, extractor_info, clowder_id, {
        "plots_processed": successful_plots,
    }, 'file')
    upload_metadata(conn, host, secret_key, clowder_id, ext_meta)

    # TODO: write geo_ids.json

print("Submission to Geostreams would happen now")
# upload_to_geostreams(args.input, args.clowderid)
