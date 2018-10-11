#!/bin/bash

set -e

INPUT=`echo "$1" | sed 's;___;/;g'`
SCAN=$2
IMAGE=$3
DATE=$4

export BETYDB_LOCAL_CACHE_FOLDER=$PWD
export SENSOR_METADATA_CACHE=$PWD/ua-mac/sensor-metadata

if [ -e "fullfield_${SCAN}.tar.gz" ]; then
    echo "Unzipping fullfield_${SCAN}.tar.gz..."
    tar xzf fullfield_${SCAN}.tar.gz
fi

./canopyCover.py -i $IMAGE -d $DATE
