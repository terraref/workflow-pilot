#!/bin/bash

INPUT=`echo "$1" | sed 's;___;/;g'`

chmod 755 canopyCover.py
./canopyCover.py -i $INPUT

