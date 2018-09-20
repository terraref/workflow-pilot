#!/bin/bash

set -e

JSON=$1
SCAN=$2
SINGLE=$3

OUT_DIR=`dirname $JSON`

export BETYDB_LOCAL_CACHE_FOLDER=$(dirname $PWD)/tools/
export SENSOR_METADATA_CACHE=data/terraref/sites/ua-mac/sensor-metadata

if [ $SINGLE == 'true' ]; then
    if [ -e "rgb_geotiff_quality_${SCAN}.tar.gz" ]; then
        tar xzf rgb_geotiff_quality_${SCAN}.tar.gz
    fi

    python fieldmosaic.py -j $JSON --single

else
    if [ -e "rgb_geotiff_${SCAN}.tar.gz" ]; then
        tar xzf rgb_geotiff_${SCAN}.tar.gz
    fi

    python fieldmosaic.py -j $JSON

    if [ -e "rgb_geotiff_${SCAN}.tar.gz" ]; then
        tar czf fullfield_${SCAN}.tar.gz $OUT_DIR
    fi
fi


