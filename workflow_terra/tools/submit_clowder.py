#!/usr/bin/python

import argparse
import logging
import os

from pyclowder.connectors import Connector
from pyclowder.files import upload_metadata as upload_file_metadata
from pyclowder.datasets import upload_metadata as upload_dataset_metadata
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

def upload_to_clowder(dir, type, scan):
    conn = Connector(None , mounted_paths={"/home/clowder/sites":"/home/clowder/sites"})

    if args.type == "rgb_geotiff":
        print("Submission of RGB GeoTIFF would happen now")
        return

        disp = "RGB GeoTIFFs"
        timestamp = dir.split("/")[-2]
        target_dsid = build_dataset_hierarchy(host, secret_key, clow_user, clow_pass, clowspace, disp,
                                              timestamp[:4], timestamp[5:7], timestamp[8:10], leaf_ds_name=disp+' - '+timestamp)

        output_ids = {}
        # First, upload actual files
        for targ_file in ["rgb_geotiff_L1_ua-mac_%s_left.tif" % ts,
                          "rgb_geotiff_L1_ua-mac_%s_right.tif" % ts,
                          "rgb_geotiff_L1_ua-mac_%s_nrmac_left.tif" % ts,
                          "rgb_geotiff_L1_ua-mac_%s_nrmac_right.tif" % ts]:
            targ_path = os.path.join(dir, targ_file)
            if os.path.isfile(targ_path):
                file_id = upload_to_dataset(conn, host, clow_user, clow_pass, target_dsid, targ_path)
                output_ids[targ_file] = file_id

        # Second, upload metadata
        ds_md = os.path.join(dir, "clean_metadata.json")
        if os.path.isfile(ds_md):
            # Dataset metadata
            extractor_info = {
                "extractor_name": "terra.stereo-rgb.bin2tif",
                "extractor_version": "1.1",
                "extractor_author": "Max Burnette <mburnet2@illinois.edu>",
                "extractor_description": "Stereo RGB Image Bin to GeoTIFF Converter",
                "extractor_repo": "https://github.com/terraref/extractors-stereo-rgb.git"
            }

            with open(ds_md, 'r') as contents:
                jmd = json.load(contents)
            upload_dataset_metadata(conn, host, secret_key, clowder_id, jmd)
            lemna_md = build_metadata(host, extractor_info, target_dsid, jmd, 'dataset')
            upload_metadata(connector, host, secret_key, target_dsid, lemna_md)

        nrmac_md = os.path.join(dir, "nrmac_scores.json")
        if os.path.isfile(nrmac_md):
            # NRMAC file metadata
            extractor_info = {
                "extractor_name": "terra.stereo-rgb.nrmac",
                "extractor_version": "1.0",
                "extractor_author": "Sidike Paheding <sidike.paheding@slu.edu>",
                "extractor_description": "Stereo RGB No-Reference Multiscale Autocorrelation",
                "extractor_repo": "https://github.com/terraref/quality-metrics.git"
            }

            with open(nrmac_md, 'r') as contents:
                jmd = json.load(contents)
            fi_id = output_ids["rgb_geotiff_L1_ua-mac_%s_nrmac_left.tif" % ts]
            ext_meta = build_metadata(host, extractor_info, fi_id, {
                "quality_score": jmd["quality_score"]["left"]
            }, 'file')
            upload_metadata(connector, host, secret_key, fi_id, ext_meta)
            fi_id = output_ids["rgb_geotiff_L1_ua-mac_%s_nrmac_right.tif" % ts]
            ext_meta = build_metadata(host, extractor_info, fi_id, {
                "quality_score": jmd["quality_score"]["right"]
            }, 'file')
            upload_metadata(connector, host, secret_key, fi_id, ext_meta)

        # Write output_ids.json
        with open(os.path.join(dir, "clowder_ids.json"), 'w') as js:
            js.write(json.dumps(output_ids))

    elif args.type == "fullfield":
        print("Submission of Full Field Mosaic would happen now")
        return

        disp = "Full Field Stitched Mosaics"
        timestamp = dir.split("/")[-2]
        target_dsid = build_dataset_hierarchy(host, secret_key, clow_user, clow_pass, clowspace, disp,
                                              timestamp[:4], timestamp[5:7], leaf_ds_name=disp+' - '+timestamp)

        # TODO: Can each scan be in a separate folder in Clowder?

        output_ids = {}
        # First, upload NRMAC files
        for targ_file in ["fullfield_L1_ua-mac_%s_%s_nrmac.vrt" % (day, scan),
                          "fullfield_L1_ua-mac_%s_%s_nrmac.tif" % (day, scan)]:
            targ_path = os.path.join(dir, targ_file)
            if os.path.isfile(targ_path):
                file_id = upload_to_dataset(conn, host, clow_user, clow_pass, target_dsid, targ_path)
                output_ids[targ_file] = file_id

        # Second, upload main stitched files
        for targ_file in ["fullfield_L1_ua-mac_%s_%s.vrt" % (day, scan),
                          "fullfield_L1_ua-mac_%s_%s.tif" % (day, scan),
                          "fullfield_L1_ua-mac_%s_%s_thumb.tif" % (day, scan),
                          "fullfield_L1_ua-mac_%s_%s_10pct.tif" % (day, scan),
                          "fullfield_L1_ua-mac_%s_%s.png" % (day, scan)]:
            targ_path = os.path.join(dir, targ_file)
            if os.path.isfile(targ_path):
                file_id = upload_to_dataset(conn, host, clow_user, clow_pass, target_dsid, targ_path)
                output_ids[targ_file] = file_id

        # Third, upload trait CSV files
        for targ_file in ["fullfield_L1_ua-mac_%s_%s_canopycover_bety.csv" % (day, scan),
                          "fullfield_L1_ua-mac_%s_%s_canopycover_geo.csv" % (day, scan)]:
            targ_path = os.path.join(dir, targ_file)
            if os.path.isfile(targ_path):
                file_id = upload_to_dataset(conn, host, clow_user, clow_pass, target_dsid, targ_path)
                output_ids[targ_file] = file_id

        # Write output_ids.json
        with open(os.path.join(dir, "clowder_ids.json"), 'w') as js:
            js.write(json.dumps(output_ids))

upload_to_clowder(args.dir, args.type, args.scan)
