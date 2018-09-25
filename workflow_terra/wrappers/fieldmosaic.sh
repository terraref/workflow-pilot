#!/bin/bash

set -e

IN_JSON=`echo "$1" | sed 's;___;/;g'`
SCAN=$2
SINGLE=$3
TOOL_SCRIPT=`echo "$4" | sed 's;___;/;g'`

OUT_DIR=`dirname $IN_JSON`
TOOL_DIR=`dirname $TOOL_SCRIPT`
mkdir -p $OUT_DIR $TOOL_DIR

export SENSOR_METADATA_CACHE=data/terraref/sites/ua-mac/sensor-metadata

# condor pool?
if [ "$1" != "$IN_JSON" ]; then
    cp $1 $IN_JSON
    cp $4 $TOOL_SCRIPT
fi

if [ $SINGLE == 'true' ]; then
    if [ -e "rgb_geotiff_quality_${SCAN}.tar.gz" ]; then
        tar xzf rgb_geotiff_quality_${SCAN}.tar.gz
    fi

    echo "Here we go with a VRT test..."
    VRTFILE=`echo "$IN_JSON" | sed -e 's/_file_paths.json/.vrt/g'`
    gdalbuildvrt -srcnodata "-99 -99 -99" -overwrite -input_file_list $IN_JSON $VRTFILE

    chmod 755 $TOOL_SCRIPT
    $TOOL_SCRIPT -j $IN_JSON --single

else
    if [ -e "rgb_geotiff_${SCAN}.tar.gz" ]; then
        tar xzf rgb_geotiff_${SCAN}.tar.gz
    fi

    chmod 755 $TOOL_SCRIPT
    $TOOL_SCRIPT -j $IN_JSON

    if [ -e "rgb_geotiff_${SCAN}.tar.gz" ]; then
        tar czf fullfield_${SCAN}.tar.gz $OUT_DIR
    fi
fi


