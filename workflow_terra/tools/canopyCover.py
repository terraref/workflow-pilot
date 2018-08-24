from terrautils.betydb import add_arguments, get_sites, get_sites_by_latlon, submit_traits, \
    get_site_boundaries
    
import argparse
import os
import json
import canopyCover as ccCore
from terrautils.gdal import clip_raster, centroid_from_geojson
from numpy import asarray, rollaxis
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
parser.add_argument("-v", "--verbose", help="Debug logging", action="store_true")

args = parser.parse_args()

if args.verbose:
    logger.setLevel(logging.DEBUG)

dirname = os.path.dirname(args.input)
date = dirname[dirname.rfind("/")+1:len(dirname)]
time_fmt = date+"T12:00:00-07:00"

bety_csv = args.input.replace(".tif", "_canopycover_bety.csv")
geo_csv = args.input.replace(".tif", "-_canopycover_geo.csv")
csv_file = open(bety_csv, 'w')
(fields, traits) = ccCore.get_traits_table()
csv_file.write(','.join(map(str, fields)) + '\n')

geo_file = open(geo_csv, 'w')
geo_file.write(','.join(['site', 'trait', 'lat', 'lon', 'dp_time', 'source', 'value', 'timestamp']) + '\n')

all_plots = get_site_boundaries(date, city='Maricopa')
successful_plots = 0
for plotname in all_plots:
    logger.debug("Processing plot %s" % plotname)

    bounds = all_plots[plotname]
    centroid_lonlat = json.loads(centroid_from_geojson(bounds))["coordinates"]

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
        logger.error("error generating cc for %s: %s" % (plotname, str(e)))
        continue

    geo_file.write(','.join([plotname,
                             'Canopy Cover',
                             str(centroid_lonlat[1]),
                             str(centroid_lonlat[0]),
                             time_fmt,
                             "FILE_ID_UNKNOWN",
                             str(ccVal),
                             date]) + '\n')

    traits['canopy_cover'] = str(ccVal)
    traits['site'] = plotname
    traits['local_datetime'] = date+"T12:00:00"
    trait_list = ccCore.generate_traits_list(traits)
    csv_file.write(','.join(map(str, trait_list)) + '\n')
    
csv_file.close()
geo_file.close()
