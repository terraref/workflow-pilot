#!/bin/bash

set -e

JSON=$1
SCAN=$2
SINGLE=$3

OUT_DIR=`dirname $JSON`

if [ -e "rgb_geotiff_${SCAN}.tar.gz" ]; then
    tar xzf rgb_geotiff_${SCAN}.tar.gz
fi
if [ -e "rgb_geotiff_quality_${SCAN}.tar.gz" ]; then
    tar xzf rgb_geotiff_quality_${SCAN}.tar.gz
fi

if [ $SINGLE == 'true' ]; then
    python fieldmosaic.py -j $JSON --single
else
    python fieldmosaic.py -j $JSON
fi

if [ -e "rgb_geotiff_${SCAN}.tar.gz" ]; then
    tar czf fullfield_${SCAN}.tar.gz $OUT_DIR
fi
