# Workflow Pilot

This repository contains files related to the TERRA-REF ECSS workflow pilot.  

## Using the Docker image

`bin2tif.py` takes a raw_data timestamp directory as input and produces the Level_1/rgb_geotiff heirarchy under the specified output directory:
```
docker run -v /data/terraref:/data/terraref \
  -v /tmp/output:/output \
  craigwillis/workflow-pilot \
  ./bin2tif.py -i /data/terraref/sites/ua-mac/raw_data/stereoTop/2018-05-01/2018-05-01__09-08-02-749 \
  -o /output -k <clowder key>
```

This will produce two geotiffs in the `output` heirarchy.

`fieldmosaic.py` take the base directory (i.e., level above "sites") and date as input and produces the Level_1/fullfield heirarchy under the specified output directory:
```
docker run -v /data/terraref:/data/terraref \
  -v /tmp/output:/output \
  craigwillis/workflow-pilot \
  ./fieldmosaic.py -b /data/terraref -d 2018-04-30  -o output -p 10
```
This will create one of more fullfield images, depending on the number of scans run that day.

`canopycover.py` takes the path to a fullfield image and generates the `*-canopycover.csv` in the same directory:
```
docker run -v /data/terraref:/data/terraref \
  -v /tmp/output:/output craigwillis/workflow-pilot \
  ./canopycover.py -i /output/ua-mac/Level_1/fullfield/2018-04-30/fullfield_L1_ua-mac_2018-04-30_rgb_geotiff_stereovis_ir_sensors_fullfield_sorghum3_shade_mntest3_westplot_april2018.tif \
  -k <bety key>
```

## Pegasus Workflow

This workflow was designed to run both on the local OpenStack infrastructure as well as on PSC Bridges. To support the OpenStack mode, which is a straight HTCondor pool with HTCondor file transfers, and the tools' existing directory structure assumptions, the workflow "flattens" some of the logical file names (LFNs) and encode the directories in the filename. For example, a file named `stereoTop/2018-03-31/2018-03-31__11-20-34-311/d0e7dfff-40ae-4c10-baf1-8ec339ac29e6_left.bin` will be tracked by Pegasus as `stereoTop___2018-03-31___2018-03-31__11-20-34-311___d0e7dfff-40ae-4c10-baf1-8ec339ac29e6_left.bin`. Files like that are put back into the correct directory structure before the tools are executed.

The workflow is defined in the abstract workflow generator (`workflow/dax-generator.py`)

### Singularity Image

In order to prepare for running at PSC, the Docker image was converted to a Singularity image with the command:

```
singularity build terraref.img docker//craigwillis/workflow-pilot
```

The image is temporarily hosted on http://workflow.isi.edu - but that location can easily be changed in the transformation catalog (`workflow/tc-generator.sh`)

### Submitting a Workflow

Create/update the settings file `workflow/run-settings.conf`:

```
[settings]

clowder_key = 

# condor_pool / psc_bridges 
execution_env = condor_pool

# day to process in YYYY-MM-DD format
day = 2018-03-31

# limit the number of entries to process - useful when debugging
entries_limit = 20

```

Then run:

```
./workflow/submit.sh
```

### Useful Pegasus Commands

   * `pegasus-status -v [wfdir]`
        Provides status on a currently running workflow. ([more](http://pegasus.isi.edu/wms/docs/latest/cli-pegasus-status.php))
   * `pegasus-analyzer [wfdir]`
        Provides debugging clues on failed workflows. Run this after a workflow has failed. ([more](http://pegasus.isi.edu/wms/docs/latest/cli-pegasus-analyzer.php))
   * `pegasus-statistics [wfdir]`
        Provides statistics, such as walltimes, on a workflow after it has completed. ([more](http://pegasus.isi.edu/wms/docs/latest/cli-pegasus-statistics.php))
   * `pegasus-remove [wfdir]`
        Removes a workflow. ([more](http://pegasus.isi.edu/wms/docs/latest/cli-pegasus-remove.php))


