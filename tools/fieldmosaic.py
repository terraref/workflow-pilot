import argparse
import logging
import os
import subprocess
from PIL import Image


logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger("fieldmosaic")

parser = argparse.ArgumentParser()
parser.add_argument("-j", "--json", required=True, help="Input json file list")
parser.add_argument("-v", "--verbose", help="Debug logging", action="store_true")

args = parser.parse_args()
if args.verbose:
    logger.setLevel(logging.DEBUG)

def stitch_jsonfile(jsonfile, out_full):
    out_thumb = out_full.replace(".tif", "_thumb.tif")
    out_medium = out_full.replace(".tif", "_10pct.tif")
    out_png = out_full.replace(".tif", ".png")
    out_vrt = out_full.replace(".tif", ".vrt")

    logger.debug("Creating VRT")
    cmd = 'gdalbuildvrt -srcnodata "-99 -99 -99" -overwrite -input_file_list ' + jsonfile +' ' + out_vrt
    os.system(cmd)

    logger.debug("Generating 2% resolution")
    cmd = "gdal_translate -projwin -111.9750963 33.0764953 -111.9747967 33.074485715 " + \
          "-outsize %s%% %s%% %s %s" % (2, 2, out_vrt, out_thumb)
    subprocess.call(cmd, shell=True)

    logger.debug("Generating 10% resolution")
    cmd = "gdal_translate -projwin -111.9750963 33.0764953 -111.9747967 33.074485715 " + \
          "-outsize %s%% %s%% %s %s" % (10, 10, out_vrt, out_medium)
    subprocess.call(cmd, shell=True)

    logger.debug("Generating 100% resolution")
    cmd = "gdal_translate -projwin -111.9750963 33.0764953 -111.9747967 33.074485715 " + \
          "%s %s" % (out_vrt, out_full)
    subprocess.call(cmd, shell=True)

    logger.debug("Generating PNG 10% thumbnail")
    px_img = Image.open(out_medium)
    px_img.save(out_png)

out_full = args.json.replace("_file_paths.json", ".tif")
stitch_jsonfile(args.json, out_full)
