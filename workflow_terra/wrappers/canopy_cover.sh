#!/bin/bash

set -e

INPUT=`echo "$1" | sed 's;___;/;g'`
SCAN=$2
IMAGE=$3

if [ -e "fullfield_${SCAN}.tar.gz" ]; then
    tar xzf fullfield_${SCAN}.tar.gz
fi

chmod 755 canopyCover.py
./canopyCover.py -i $IMAGE

