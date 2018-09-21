#!/bin/bash

set -e

INPUT=`echo "$1" | sed 's;___;/;g'`
SCAN=$2
IMAGE=$3
BETY_DUMP=`echo "$9" | sed 's;___;/;g'`

BETY_DIR=`dirname $BETY_DUMP`

export BETYDB_LOCAL_CACHE_FOLDER=$(dirname $PWD)/tools/
export SENSOR_METADATA_CACHE=data/terraref/sites/ua-mac/sensor-metadata

if [ -e "fullfield_${SCAN}.tar.gz" ]; then
    tar xzf fullfield_${SCAN}.tar.gz
fi

chmod 755 canopyCover.py
./canopyCover.py -i $IMAGE
