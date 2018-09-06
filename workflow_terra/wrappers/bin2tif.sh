#!/bin/bash

set -e

IN_LEFT=`echo "$1" | sed 's;___;/;g'`
IN_RIGHT=`echo "$2" | sed 's;___;/;g'`
IN_META=`echo "$3" | sed 's;___;/;g'`
OUT_LEFT=`echo "$4" | sed 's;___;/;g'`
OUT_RIGHT=`echo "$5" | sed 's;___;/;g'`
OUT_META=`echo "$6" | sed 's;___;/;g'`
TIMESTAMP=`echo "$7"`

IN_DIR=`dirname $IN_LEFT`
OUT_DIR=`dirname $OUT_LEFT`

echo "mkdir -p $IN_DIR $OUT_DIR"
mkdir -p $OUT_DIR

# touch the outputs so we don't get held jobs in case of failures
touch $4 $5 $6

# condor pool?
if [ "$1" != "$IN_LEFT" ]; then
    cp $1 $IN_LEFT
    cp $2 $IN_RIGHT
    cp $3 $IN_META
fi

chmod 755 bin2tif.py
./bin2tif.py -l $IN_LEFT -r $IN_RIGHT -m $IN_META -t $TIMESTAMP -o $OUT_DIR

# condor pool?
if [ "$1" != "$IN_LEFT" ]; then
    cp $OUT_LEFT $4
    cp $OUT_RIGHT $5
    cp $OUT_META $6 
fi
