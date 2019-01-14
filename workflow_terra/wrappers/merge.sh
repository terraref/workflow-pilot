#!/bin/bash

set -e

OUTFILE=$1 #output file
shift

for FILE in "$@"; do
    if (ls $FILE | grep .tar.gz) >/dev/null 2>&1; then
        tar xzf $FILE
    else
        TARGET_FILE=`echo $FILE | sed 's;___;/;g'`
        echo "Moving $FILE to $TARGET_FILE ..."
        DIRNAME=`dirname $TARGET_FILE`
        mkdir -p $DIRNAME
        mv $FILE $TARGET_FILE
    fi
done

tar czf $OUTFILE ua-mac

