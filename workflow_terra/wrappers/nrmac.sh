#!/bin/bash

set -e
set -x

IN_LEFT="$1"
IN_RIGHT="$2"
IN_META="$3"
OUT_LEFT="$4"
OUT_RIGHT="$5"
OUT_JSON="$6"

export SENSOR_METADATA_CACHE=$PWD/ua-mac/sensor-metadata

./nrmac.py -l $IN_LEFT -r $IN_RIGHT -m $IN_META --out_l $OUT_LEFT --out_r $OUT_RIGHT --out_j $OUT_JSON

