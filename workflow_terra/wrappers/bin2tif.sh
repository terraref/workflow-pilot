#!/bin/bash

set -e
set -x

IN_LEFT="$1"
IN_RIGHT="$2"
IN_META="$3"
OUT_LEFT="$4"
OUT_RIGHT="$5"
OUT_META="$6"
TIMESTAMP="$7"
FIXED_META="$8"

# TODO: Deal with this...
# TODO: cp: cannot stat 'ua-mac/Level_1/rgb_geotiff/2018-07-01/2018-07-01__08-35-45-218/rgb_geotiff_L1_ua-mac_2018-07-01__08-35-45-218_left.tif': No such file or directory
OUT_DIR="."

export BETYDB_LOCAL_CACHE_FOLDER=$PWD
export SENSOR_METADATA_CACHE=$PWD/ua-mac/sensor-metadata

./bin2tif.py -l $IN_LEFT -r $IN_RIGHT -m $IN_META -t $TIMESTAMP -o $OUT_DIR

