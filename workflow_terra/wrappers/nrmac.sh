#!/bin/bash

set -e

IN_LEFT=`echo "$1" | sed 's;___;/;g'`
IN_RIGHT=`echo "$2" | sed 's;___;/;g'`
OUTPUT=`echo "$3" | sed 's;___;/;g'`

# touch the outputs so we don't get held jobs in case of failures
touch $3

# condor pool?
if [ "$1" != "$IN_LEFT" ]; then
    cp $1 $IN_LEFT
    cp $2 $IN_RIGHT
fi

chmod 755 nrmac.py
./nrmac.py -l $IN_LEFT -r $IN_RIGHT -o $OUTPUT

# condor pool?
if [ "$1" != "$IN_LEFT" ]; then
    cp $OUTPUT $3
fi
