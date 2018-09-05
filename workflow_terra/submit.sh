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

export RUN_ID=stereo_rgb-`date +'%s'`
export RUN_DIR=$HOME/workflows/$RUN_ID

mkdir -p $RUN_DIR
mkdir -p workflow/generated

# create a site catalog from the template
envsubst < sites.template.xml > workflow/generated/sites.xml

# generate a transformation catalog
./tc-generator.sh $EXEC_ENV >workflow/generated/tc.data

# generate the workflow
#./workflow_generator.py

# plan and submit
pegasus-plan \
    --conf pegasus.conf \
    --sites $EXEC_SITE \
    --staging-site $STAGING_SITE \
    --output-site $OUTPUT_SITE \
    --cluster horizontal \
    --cleanup leaf \
    --relative-dir $RUN_ID \
    --dir $RUN_DIR \
    --dax workflow/generated/2018-07-01__stereovis_ir_sensors_partialplots_sorghum6_shade_flir_eastedge_mn_14140c8a-e13a-4ccd-a120-d3dbf3eacef4.xml \
    --submit 

