#!/bin/bash

set -e

JSON=$1
SCAN=$2

OUT_DIR=`dirname $JSON`

if [ -e "rgb_geotiff_${SCAN}.tar.gz" ]; then
    tar xzf rgb_geotiff_${SCAN}.tar.gz
fi

python fieldmosaic.py -j $JSON

if [ -e "rgb_geotiff_${SCAN}.tar.gz" ]; then
    tar czf fullfield_${SCAN}.tar.gz $OUT_DIR
fi
