#!/usr/bin/python

import argparse
import logging

from pyclowder.connectors import Connector
from pyclowder.files import upload_metadata
from terrautils.extractors import build_dataset_hierarchy, upload_to_dataset, build_metadata
from terrautils.betydb import submit_traits


logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger("nrmac")

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", required=True, help="Input bety CSV file")
parser.add_argument("-c", "--clowderid", required=True, help="Clowder id of fullfield file used to generate")
parser.add_argument("-v", "--verbose", help="Debug logging", action="store_true")

args = parser.parse_args()
if args.verbose:
    logger.setLevel(logging.DEBUG)


host = "https://terraref.ncsa.illinois.edu/clowder/"
secret_key = ""
bety_key = ""

def upload_to_bety(file, clowder_id):
    conn = Connector(None , mounted_paths={"/home/clowder/sites":"/home/clowder/sites"})

    submit_traits(file, betykey=bety_key)

    # Extractor metadata
    extractor_info = {
        "extractor_name": "terra.betydb",
        "extractor_version": "1.0",
        "extractor_author": "Max Burnette <mburnet2@illinois.edu>",
        "extractor_description": "BETYdb CSV uploader",
        "extractor_repo": "https://github.com/terraref/computing-pipeline.git"
    }

    # Add metadata to original dataset indicating this was run
    ext_meta = build_metadata(host, extractor_info, clowder_id, {
        "betydb_link": "https://terraref.ncsa.illinois.edu/bety/api/v1/variables?name=canopy_cover"
    }, 'file')
    upload_metadata(conn, host, secret_key, clowder_id, ext_meta)

    # TODO: write bety_ids.json

print("Submission to BETYdb would happen now")
# upload_to_bety(args.input, args.clowderid)
