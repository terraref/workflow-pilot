#!/bin/bash

set -e

INPUT=`echo "$1" | sed 's;___;/;g'`
SCAN=$2
IMAGE=$3

export BETYDB_LOCAL_CACHE_FOLDER=$PWD/../tools/
export SENSOR_METADATA_CACHE=data/terraref/sites/ua-mac/sensor-metadata

if [ -e "fullfield_${SCAN}.tar.gz" ]; then
    tar xzf fullfield_${SCAN}.tar.gz
fi

chmod 755 canopyCover.py
./canopyCover.py -i $IMAGE
