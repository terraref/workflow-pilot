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

# "fix" any remaining files with ___
for SRC in `ls *___*`; do
    TRG=`echo "$SRC" | sed 's;___;/;g'`
    mkdir -p `dirname $TRG`
    cp $SRC $TRG
done

# TODO: Deal with this...
# TODO: cp: cannot stat 'ua-mac/Level_1/rgb_geotiff/2018-07-01/2018-07-01__08-35-45-218/rgb_geotiff_L1_ua-mac_2018-07-01__08-35-45-218_left.tif': No such file or directory
OUT_DIR=`dirname $OUT_LEFT`

export BETYDB_LOCAL_CACHE_FOLDER=$PWD
export SENSOR_METADATA_CACHE=$PWD/ua-mac/sensor-metadata

# touch the outputs so we don't get held jobs in case of failures
touch $4 $5 $6

# condor pool?
if [ "$1" != "$IN_LEFT" ]; then
    cp $1 $IN_LEFT
    cp $2 $IN_RIGHT
    cp $3 $IN_META
    cp $8 $FIXED_META
fi

./bin2tif.py -l $IN_LEFT -r $IN_RIGHT -m $IN_META -t $TIMESTAMP -o $OUT_DIR

# condor pool?
if [ "$1" != "$IN_LEFT" ]; then
    cp $OUT_LEFT $4
    cp $OUT_RIGHT $5
    cp $OUT_META $6 
fi
