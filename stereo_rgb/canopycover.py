from terrautils.betydb import add_arguments, get_sites, get_sites_by_latlon, submit_traits, \
    get_site_boundaries
    
import argparse
import os
import canopyCover as ccCore
import terra_common
from terrautils.gdal import clip_raster, centroid_from_geojson
from numpy import asarray, rollaxis
import sys
import logging

#
#
# Simple example of canopycover calculation from fullfield RGB image
# This still has a dependency on the BETYDB REST API
# python canopycover.py -i <path to fullfield image> -k <bety key>
#

logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger("canopycover")
logger.setLevel(logging.INFO)

parser = argparse.ArgumentParser()

parser.add_argument("-i", "--input", required=True, help="Fullfield path")
parser.add_argument("-k", "--key", required=True, help="BETYDB API Key ")
parser.add_argument("-v", "--verbose", help="Debug logging", action="store_true")

args = parser.parse_args()

if args.verbose:
    logger.setLevel(logging.DEBUG)

#os.environ["BETYDB_KEY"] = "GZJZWnJpnDBhmKk7k6vb46z6lW6vjxSniRivRl2I"

os.environ["BETYDB_KEY"] = args.key

dirname = os.path.dirname(args.input)
date = dirname[dirname.rfind("/")+1:len(dirname)]


all_plots = get_site_boundaries(date, city='Maricopa')    

trait_csv = args.input.replace(".tif", "-canopycover.csv")
csv_file = open(trait_csv, 'w')
(fields, traits) = ccCore.get_traits_table()
csv_file.write(','.join(map(str, fields)) + '\n')

successful_plots = 0
for plotname in all_plots:
    logger.debug("Processing plot %s" % plotname)
    bounds = all_plots[plotname]

    # Use GeoJSON string to clip full field to this plot
    try:
        (pxarray, geotrans) = clip_raster(args.input, bounds)
        if len(pxarray.shape) < 3:
            print("unexpected array shape for %s (%s)" % (plotname, pxarray.shape))
            continue
        ccVal = ccCore.gen_cc_for_img(rollaxis(pxarray,0,3), 5)
        ccVal *= 100.0 # Make 0-100 instead of 0-1
        successful_plots += 1
        if successful_plots % 10 == 0:
            logger.info("processed %s/%s plots successfully" % (successful_plots, len(all_plots)))
    except Exception, e:
        logge.error("error generating cc for %s: %s" % (plotname, str(e)))
        continue

    traits['canopy_cover'] = str(ccVal)
    traits['site'] = plotname
    traits['local_datetime'] = date+"T12:00:00"
    trait_list = ccCore.generate_traits_list(traits)

    csv_file.write(','.join(map(str, trait_list)) + '\n')
    
csv_file.close()