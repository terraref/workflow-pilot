#!/bin/bash

set -e
set -x

IN_LEFT=`echo "$1" | sed 's;___;/;g'`
IN_RIGHT=`echo "$2" | sed 's;___;/;g'`
IN_META=`echo "$3" | sed 's;___;/;g'`
OUT_LEFT=`echo "$4" | sed 's;___;/;g'`
OUT_RIGHT=`echo "$5" | sed 's;___;/;g'`
OUT_META=`echo "$6" | sed 's;___;/;g'`
TIMESTAMP=`echo "$7"`
FIXED_META=`echo "$8" | sed 's;___;/;g'`
BETY_DUMP=`echo "$9" | sed 's;___;/;g'`

IN_DIR=`dirname $IN_LEFT`
OUT_DIR=`dirname $OUT_LEFT`
META_DIR=`dirname $FIXED_META`
BETY_DIR=`dirname $BETY_DUMP`

mkdir -p $IN_DIR $OUT_DIR $META_DIR $BETY_DIR
OUT_DIR="."

export BETYDB_LOCAL_CACHE_FOLDER=$(dirname $PWD)/tools/
export SENSOR_METADATA_CACHE=data/terraref/sites/ua-mac/sensor-metadata

# touch the outputs so we don't get held jobs in case of failures
touch $4 $5 $6

# condor pool?
if [ "$1" != "$IN_LEFT" ]; then
    cp $1 $IN_LEFT
    cp $2 $IN_RIGHT
    cp $3 $IN_META
    cp $8 $FIXED_META
    cp $9 $BETY_DIR
fi

chmod 755 bin2tif.py
./bin2tif.py -l $IN_LEFT -r $IN_RIGHT -m $IN_META -t $TIMESTAMP -o $OUT_DIR

# condor pool?
if [ "$1" != "$IN_LEFT" ]; then
    cp $OUT_LEFT $4
    cp $OUT_RIGHT $5
    cp $OUT_META $6 
fi
