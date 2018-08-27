#!/bin/bash

set -e

JOBTYPE=$1
JOBNAME=$2
INPUT=$3


if [ $JOBTYPE == 'clowder' ]; then
    python submit_clowder.py --dir $INPUT -t $JOBNAME
elif [ $JOBTYPE == 'bety' ]; then
    python submit_bety.py -i $INPUT -t $JOBNAME
else
    python submit_geo.py -i $INPUT -t $JOBNAME
fi
