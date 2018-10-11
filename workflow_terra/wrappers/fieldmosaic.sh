#!/bin/bash

set -e
set -x

IN_JSON=`echo "$1" | sed 's;___;/;g'`
SCAN=$2
SINGLE=$3
DRY_RUN=$4

OUT_DIR=`dirname $IN_JSON`
mkdir -p $OUT_DIR

VRTFILE=`echo "$IN_JSON" | sed -e 's/_file_paths.json/.vrt/g'`
GEOTIFF=`echo "$IN_JSON" | sed -e 's/_file_paths.json/.tif/g'`
THUMB=`echo "$IN_JSON" | sed -e 's/_file_paths.json/_thumb.tif/g'`
PCT10=`echo "$IN_JSON" | sed -e 's/_file_paths.json/_10pct.tif/g'`
PNG=`echo "$IN_JSON" | sed -e 's/_file_paths.json/.png/g'`


# condor pool?
if [ "$1" != "$IN_JSON" ]; then
    cp $1 $IN_JSON
fi

# Unzip input tar file if exists (contains nested folder contents)
if [ -e "rgb_geotiff_quality_${SCAN}.tar.gz" ]; then
    echo "Unzipping rgb_geotiff_quality_${SCAN}.tar.gz..."
    tar xzf rgb_geotiff_quality_${SCAN}.tar.gz
elif [ -e "rgb_geotiff_${SCAN}.tar.gz" ]; then
    echo "Unzipping rgb_geotiff_${SCAN}.tar.gz..."
    tar xzf rgb_geotiff_${SCAN}.tar.gz
else
    echo "No .tar.gz file found."
fi

# Generate VRT and GeoTIFFs
echo "Generating VRT file..."
gdalbuildvrt -srcnodata "-99 -99 -99" -overwrite -input_file_list $IN_JSON $VRTFILE

if [ $DRY_RUN == 'true' ]; then
    # For space considerations, only generate 2% mosaics during a dry run
    echo "Generating faux-100% GeoTIFF..."
    gdal_translate -projwin -111.9750963 33.0764953 -111.9747967 33.074485715 -outsize 2% 2% $VRTFILE $GEOTIFF
else
    echo "Generating 100% GeoTIFF..."
    gdal_translate -projwin -111.9750963 33.0764953 -111.9747967 33.074485715 $VRTFILE $GEOTIFF
fi

if [ $SINGLE == 'false' ]; then
    echo "Generating 2% GeoTIFF..."
    gdal_translate -projwin -111.9750963 33.0764953 -111.9747967 33.074485715 -outsize 2% 2% $VRTFILE $THUMB

    if [ $DRY_RUN == 'true' ]; then
        # For space considerations, only generate 2% mosaics during a dry run
        echo "Generating faux-10% GeoTIFF..."
        gdal_translate -projwin -111.9750963 33.0764953 -111.9747967 33.074485715 -outsize 2% 2% $VRTFILE $PCT10
    else
        echo "Generating 10% GeoTIFF..."
        gdal_translate -projwin -111.9750963 33.0764953 -111.9747967 33.074485715 -outsize 10% 10% $VRTFILE $PCT10
    fi

    echo "Generating 10% PNG..."
    gdal_translate -of PNG $PCT10 $PNG
fi

# Zip up results of fullfield if inputs were zipped
if [ -e "rgb_geotiff_${SCAN}.tar.gz" ]; then
    echo "Zipping fullfield_${SCAN}.tar.gz..."
    tar czf fullfield_${SCAN}.tar.gz $OUT_DIR
fi
