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

`fieldmosaic.py` take the base directory (i.e., level above "sites") and date as input and produces the Level_1/fullfield heirarchy under the specified output directory:
```
docker run -v /data/terraref:/data/terraref \
  -v /tmp/output:/output \
  craigwillis/workflow-pilot \
  ./fieldmosaic.py -b /data/terraref -d 2018-04-30  -o output -p 10
```

`canopycover.py` takes the path to a fullfield image and generates the `*-canopycover.csv` in the same directory:
```
docker run -v /data/terraref:/data/terraref \
  -v /tmp/output:/output craigwillis/workflow-pilot \
  ./canopycover.py -i /output/ua-mac/Level_1/fullfield/2018-04-30/fullfield_L1_ua-mac_2018-04-30_rgb_geotiff_stereovis_ir_sensors_fullfield_sorghum3_shade_mntest3_westplot_april2018.tif \
  -k <bety key>
```
