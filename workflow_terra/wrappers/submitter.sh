#!/bin/bash

set -e

JOBTYPE=$1
JOBARG=$2
INPUT=$3

export BETYDB_LOCAL_CACHE_FOLDER=$(dirname $PWD)/tools/
export SENSOR_METADATA_CACHE=data/terraref/sites/ua-mac/sensor-metadata

if [ $JOBTYPE == 'bety' ]; then
    python submit_bety.py -i $INPUT -c $JOBARG
elif [ $JOBTYPE == 'geo' ]; then
    python submit_geo.py -i $INPUT -c $JOBARG
else
    python submit_clowder.py --dir $INPUT -t $JOBTYPE -s $JOBARG
fi
