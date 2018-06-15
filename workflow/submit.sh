#!/bin/bash

set -e

TOP_DIR=`dirname $0`
TOP_DIR=`cd $TOP_DIR/.. && pwd`
cd $TOP_DIR

# workflow/run-settings.conf is required
if [ ! -e "workflow/run-settings.conf" ]; then
    echo "Please create workflow/run-settings.conf"
    exit 1
fi

# exec env
EXEC_ENV=`cat workflow/run-settings.conf | grep '^execution_env' | sed 's/execution_env = //'`
case $EXEC_ENV in
    "condor_pool")
        EXEC_SITE="condor_pool"
        STAGING_SITE="local"
        OUTPUT_SITE="local"
        ;;
    "psc_bridges")
        EXEC_SITE="condor_pool"
        STAGING_SITE="local"
        OUTPUT_SITE="local"
        ;;
    "isi_shared")
        EXEC_SITE="isi_shared"
        STAGING_SITE="isi_shared"
        OUTPUT_SITE="isi_shared"
        ;;
    *)
        echo "Unknown execution environment."
        exit 1
        ;;
esac

export RUN_ID=stereo_rgb-`date +'%s'`
export RUN_DIR=$HOME/workflows/$RUN_ID
# ISI special
if [ -e /lizard/scratch-90-days ]; then
    export RUN_DIR=/local-scratch/1-month-auto-purge/$USER/$RUN_ID
fi

mkdir -p $RUN_DIR
mkdir -p workflow/generated

# create a site catalog from the template
envsubst < workflow/sites.template.xml > workflow/generated/sites.xml

# generate a transformation catalog
./workflow/tc-generator.sh $EXEC_ENV >workflow/generated/tc.data

# generate the workflow
./workflow/dax-generator.py

# plan and submit
pegasus-plan \
    --conf workflow/pegasus.conf \
    --sites $EXEC_SITE \
    --staging-site $STAGING_SITE \
    --output-site $OUTPUT_SITE \
    --cluster horizontal \
    --cleanup leaf \
    --relative-dir $RUN_ID \
    --dir $RUN_DIR \
    --dax workflow/generated/dax.xml \
    --submit 


