#!/bin/bash

set -e
set -x

IN_JSON=`echo "$1" | sed 's;___;/;g'`
SCAN=$2
SINGLE=$3

OUT_DIR=`dirname $IN_JSON`
mkdir -p $OUT_DIR

# condor pool?
if [ "$1" != "$IN_JSON" ]; then
    cp $1 $IN_JSON
fi

if [ -e "rgb_geotiff_${SCAN}.tar.gz" ]; then
    echo "Unzipping rgb_geotiff_quality_${SCAN}.tar.gz..."
    tar xzf rgb_geotiff_${SCAN}.tar.gz
fi


echo "Generating VRT file..."
VRTFILE=`echo "$IN_JSON" | sed -e 's/_file_paths.json/.vrt/g'`
gdalbuildvrt -srcnodata "-99 -99 -99" -overwrite -input_file_list $IN_JSON $VRTFILE

echo "Generating 100% GeoTIFF..."
GEOTIFF=`echo "$IN_JSON" | sed -e 's/_file_paths.json/.tif/g'`
gdal_translate -projwin -111.9750963 33.0764953 -111.9747967 33.074485715 $VRTFILE $GEOTIFF

if [ $SINGLE != 'true' ]; then
    echo "Generating 2% GeoTIFF..."
    THUMB=`echo "$IN_JSON" | sed -e 's/_file_paths.json/_thumb.tif/g'`
    gdal_translate -projwin -111.9750963 33.0764953 -111.9747967 33.074485715 -outsize 2% 2% $VRTFILE $THUMB

    echo "Generating 10% GeoTIFF..."
    PCT10=`echo "$IN_JSON" | sed -e 's/_file_paths.json/_10pct.tif/g'`
    gdal_translate -projwin -111.9750963 33.0764953 -111.9747967 33.074485715 -outsize 10% 10% $VRTFILE $PCT10

    echo "Generating 10% PNG..."
    PNG=`echo "$IN_JSON" | sed -e 's/_file_paths.json/.png/g'`
    gdal_translate -of PNG $PCT10 $PNG
fi


if [ -e "rgb_geotiff_${SCAN}.tar.gz" ]; then
    echo "Zipping fullfield_${SCAN}.tar.gz..."
    tar czf fullfield_${SCAN}.tar.gz $OUT_DIR
fi
