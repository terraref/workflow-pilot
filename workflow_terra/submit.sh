#!/bin/bash

set -e

#TOP_DIR=`dirname $0`
#TOP_DIR=`cd $TOP_DIR/.. && pwd`
#cd $TOP_DIR

# exec env
EXEC_ENV="condor_pool"
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

echo "Setting BetyDB cache folder"
export BETYDB_LOCAL_CACHE_FOLDER=$PWD/tools/

export RUN_ID=stereo_rgb-`date +'%s'`
export RUN_DIR=$HOME/workflows/$RUN_ID

echo "Creating $RUN_DIR"
mkdir -p $RUN_DIR
mkdir -p workflow/generated

# create a site catalog from the template
echo "Generating site catalog"
envsubst < sites.template.xml > workflow/generated/sites.xml

# generate a transformation catalog
echo "Generating transformation catalog"
./tc-generator.sh $EXEC_ENV >workflow/generated/tc.data

# generate the workflow
echo "Calling workflow_generator"
./workflow_generator.py

# plan and submit
echo "Submitting singletest.xml"
pegasus-plan \
    --conf pegasus.conf \
    --sites $EXEC_SITE \
    --staging-site $STAGING_SITE \
    --output-site $OUTPUT_SITE \
    --cluster horizontal \
    --cleanup leaf \
    --relative-dir $RUN_ID \
    --dir $RUN_DIR \
    --dax workflow/generated/singletest.xml \
    --submit
