#!/usr/bin/python
    
import argparse
import os
import json
import yaml
import logging
from numpy import asarray, rollaxis, zeros_like, count_nonzero, array

from terrautils.gdal import clip_raster, centroid_from_geojson
from terrautils.betydb import get_site_boundaries
from terrautils.spatial import geojson_to_tuples_betydb
import terraref.stereo_rgb


logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger("canopycover")
logger.setLevel(logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", required=True, help="Fullfield path")
parser.add_argument("-d", "--date", required=True, help="Date being processed")
parser.add_argument("-v", "--verbose", help="Debug logging", action="store_true")

args = parser.parse_args()
if args.verbose:
    logger.setLevel(logging.DEBUG)

# TODO: Keep these in terrautils.bety instead
def get_traits_table():
    # Compiled traits table
    fields = ('local_datetime', 'canopy_cover', 'access_level', 'species', 'site',
              'citation_author', 'citation_year', 'citation_title', 'method')
    traits = {'local_datetime' : '',
              'canopy_cover' : [],
              'access_level': '2',
              'species': 'Sorghum bicolor',
              'site': [],
              'citation_author': '"Zongyang, Li"',
              'citation_year': '2016',
              'citation_title': 'Maricopa Field Station Data and Metadata',
              'method': 'Canopy Cover Estimation from Field Scanner RGB images'}

    return (fields, traits)

def generate_traits_list(traits):
    # compose the summary traits
    trait_list = [  traits['local_datetime'],
                    traits['canopy_cover'],
                    traits['access_level'],
                    traits['species'],
                    traits['site'],
                    traits['citation_author'],
                    traits['citation_year'],
                    traits['citation_title'],
                    traits['method']
                    ]

    return trait_list


date = args.date
time_fmt = date+"T12:00:00-07:00"

bety_csv = args.input.replace(".tif", "_canopycover_bety.csv")
geo_csv = args.input.replace(".tif", "-_canopycover_geo.csv")
csv_file = open(bety_csv, 'w')
(fields, traits) = get_traits_table()
csv_file.write(','.join(map(str, fields)) + '\n')

geo_file = open(geo_csv, 'w')
geo_file.write(','.join(['site', 'trait', 'lat', 'lon', 'dp_time', 'source', 'value', 'timestamp']) + '\n')

all_plots = get_site_boundaries(date, city='Maricopa')
successful_plots = 0
for plotname in all_plots:
    logger.debug("Processing plot %s" % plotname)
    bounds = all_plots[plotname]
    tuples = geojson_to_tuples_betydb(yaml.safe_load(bounds))
    centroid_lonlat = json.loads(centroid_from_geojson(bounds))["coordinates"]

    # Use GeoJSON string to clip full field to this plot
    try:
        pxarray = clip_raster(args.input, tuples)
        if pxarray is not None:
            pxarray = rollaxis(pxarray,0,3)
            if len(pxarray.shape) < 3:
                logger.error("unexpected array shape for %s (%s)" % (plotname, pxarray.shape))
                continue

            ccVal = terraref.stereo_rgb.calculate_canopycover(pxarray)

            successful_plots += 1
            if successful_plots % 10 == 0:
                logger.info("processed %s/%s plots successfully" % (successful_plots, len(all_plots)))
        else:
            continue

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
    trait_list = generate_traits_list(traits)
    csv_file.write(','.join(map(str, trait_list)) + '\n')

print("successful: %s" % successful_plots)
csv_file.close()
geo_file.close()
