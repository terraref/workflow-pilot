#!/bin/bash

set -e

DAY=$1
OUT_FILE=$2

if [ -e "rgb_geotiff_${DAY}.tar.gz" ]; then
    tar xzf rgb_geotiff_${DAY}.tar.gz
fi

mkdir sites
mv ua-mac sites/

python fieldmosaic.py -b . -d $DAY -o output -p 1 -v 2>&1

tar czf fullfield.tar.gz output

