import argparse
import glob
import json
import full_day_to_tiles
import logging
import os
import subprocess
import sys
from terrautils.sensors import Sensors


#
# Simple example of fieldmosiac process.
# Given a base directory and date, generate the fullfield image.
#
# e.g., python fieldmosaic.py -b /data/terraref -d 2018-04-30 -o output -p 1 -v

logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger("fieldmosaic")

parser = argparse.ArgumentParser()

parser.add_argument("-b", "--base", required=True, help="Base directory (e.g., /data/terraref/")
parser.add_argument("-d", "--date", required=True, help="Input date")
parser.add_argument("-o", "--output", required=True, help="Output directory")
parser.add_argument("-p", "--percent", required=True, default="10", help="Fullfield percent")
parser.add_argument("-v", "--verbose", help="Debug logging", action="store_true")

args = parser.parse_args()

if args.verbose:
    logger.setLevel(logging.DEBUG)

base_dir = args.base
date = args.date
output_dir = args.output
pct=args.percent



# Get the scan program names associated with each timestamp directory.
# There can be multiple scan programs per day, so we can have multiple
# output fullfield images per day.
#
# In the production process, this comes from another component that is tied
# to the RabbitMQ architecture.  For proof-of-concept, we'll generate
# from the source metadata in the corresponding raw_data directory.
#
# Similar to:
# find /data/terraref/sites/ua-mac/raw_data/stereoTop/2018-04-30/ -name "*.json" -exec grep "Script path on local disk" {} +
#
logger.debug("Getting list of scan programs names")
raw_dir = "%s/sites/ua-mac/raw_data/stereoTop/%s/*/*.json" % (base_dir, date)
metadata_files = glob.glob(raw_dir)
scan_programs = {}
vrt_map = {}
for path in metadata_files:
    dirname=os.path.dirname(path)
    dirname=dirname[dirname.rfind("/")+1:len(dirname)]
    with open(path) as f:
        data = json.load(f)
        script_name = data["lemnatec_measurement_metadata"]["gantry_system_variable_metadata"]["Script path on local disk"]
        program_name = script_name[script_name.rfind("\\")+1:script_name.rfind(".")].lower()
        scan_programs[dirname] = program_name
        vrt_map[program_name] = []

# We'll construct the fullfield from left geotiffs only
logger.debug("Getting list of geotiffs")
input_dir = "%s/sites/ua-mac/Level_1/rgb_geotiff/%s" % (base_dir, date)
timestamp = input_dir[input_dir.rfind("/")+1:len(input_dir)]

files = glob.glob("%s/*/*left.tif" % input_dir)
for path in files:
    dirname=os.path.dirname(path)
    dirname=dirname[dirname.rfind("/")+1:len(dirname)] 
    scan_program=scan_programs[dirname]
    vrt_map[scan_program].append(path)
 
 
#
# Loop over each of the scan programs and generate:
#   * List of input files (txt)
#   * VRT from txt
#   * Mosaic TIF image from VRT
#   * PNG from TIF for grins
#
for scan_program in vrt_map.keys():
    logger.info("Processing scan program %s" % scan_program)
    
    logger.debug("Creating output directories")
    sensors = Sensors(base=output_dir, station="ua-mac", sensor="fullfield")
    out_tif_full = sensors.create_sensor_path(timestamp, opts=["rgb_geotiff", scan_program])
    out_tif_thumb = out_tif_full.replace(".tif", "_thumb.tif")
    out_vrt = out_tif_full.replace(".tif", ".vrt")
    out_png = out_tif_full.replace(".tif", ".png")
    out_txt = out_tif_full.replace(".tif", ".txt")
    out_dir = os.path.dirname(out_vrt)

    # Create a text file with the tiff names for this scan program
    with open(out_txt, "w") as tifftxt:
        for file in sorted(vrt_map[scan_program]):
            tifftxt.write("%s\n" % file)    

    # Create VRT
    full_day_to_tiles.createVrtPermanent(".", out_txt, out_vrt)
    
    # Create fullfield image at specified scale   
    cmd = "gdal_translate -projwin -111.9750963 33.0764953 -111.9747967 33.074485715 " + \
        "-outsize %s%% %s%% %s %s" % (pct, pct, out_vrt, out_tif_full)
    subprocess.call(cmd, shell=True)

    # Create PNG 
    cmd = "gdal_translate -of PNG %s %s " % (out_tif_full, out_png)
    subprocess.call(cmd, shell=True)