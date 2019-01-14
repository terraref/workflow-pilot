#!/bin/bash

set -e
set -x

JOBTYPE=$1
JOBARG=$2
INPUT=$3

export BETYDB_LOCAL_CACHE_FOLDER=$PWD
export SENSOR_METADATA_CACHE=$PWD/ua-mac/sensor-metadata

if [ $JOBTYPE == 'bety' ]; then
    ./submit_bety.py -i $INPUT -c $JOBARG
elif [ $JOBTYPE == 'geo' ]; then
    ./submit_geo.py -i $INPUT -c $JOBARG
else
    ./submit_clowder.py --dir $INPUT -t $JOBTYPE -s $JOBARG
fi
