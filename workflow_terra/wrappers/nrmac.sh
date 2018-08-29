#!/bin/bash

set -e

IN_LEFT=`echo "$1" | sed 's;___;/;g'`
IN_RIGHT=`echo "$2" | sed 's;___;/;g'`
IN_META=`echo "$3" | sed 's;___;/;g'`
OUT_LEFT=`echo "$4" | sed 's;___;/;g'`
OUT_RIGHT=`echo "$5" | sed 's;___;/;g'`
OUT_JSON=`echo "$6" | sed 's;___;/;g'`

# touch the outputs so we don't get held jobs in case of failures
touch $4 $5

# condor pool?
if [ "$1" != "$IN_LEFT" ]; then
    cp $1 $IN_LEFT
    cp $2 $IN_RIGHT
fi

chmod 755 nrmac.py
./nrmac.py -l $IN_LEFT -r $IN_RIGHT -m $IN_META -out_l $OUT_LEFT -out_r $OUT_RIGHT -out_j $OUT_JSON

# condor pool?
if [ "$1" != "$IN_LEFT" ]; then
    cp $OUT_LEFT $4
    cp $OUT_RIGHT $5
    cp $OUT_JSON $6
fi
