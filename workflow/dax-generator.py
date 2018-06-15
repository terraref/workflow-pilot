#!/usr/bin/env python

import glob
import math
import os
import re
import sys
import getpass
import ConfigParser

from Pegasus.DAX3 import *

# global
top_dir = os.getcwd()


def add_merge_job(final_name, chunk, level, job_number, final):
    """
    adds a merge job
    """
    j = Job(name="merge.sh")
    out_file = File(final_name + "-%d-%d.tar.gz" %(level, job_number))
    if final:
        out_file = File(final_name)
    j.uses(out_file, link=Link.OUTPUT, transfer=final)
    j.addArguments(out_file)
    for f in chunk:
        j.uses(f, link=Link.INPUT)
        j.addArguments(f)
    j.addProfile(Profile(Namespace.CONDOR, 'request_disk', '100 GB'))
    dax.addJob(j)
    return out_file


def merge_rgb_geotiffs(final_name, inputs, level):
    """
    creates a set of small jobs to merge geotifs to a tarball
    """
    max_files = 60
    new_outputs = []

    input_chunks = [inputs[i:i + max_files] for i in xrange(0, len(inputs), max_files)]

    job_count = 0
    for chunk in input_chunks:
        job_count = job_count + 1
        f = add_merge_job(final_name, chunk, level, job_count, False)
        new_outputs.append(f)

    # end condition - only one chunk
    if len(new_outputs) <= max_files:
        return add_merge_job(final_name, new_outputs, level + 1, 1, True)

    return merge_rgb_geotiffs(final_name, new_outputs, level + 1)


def my_lfn(orig_lfn):
    '''
    Depending on the execution environment, we might have to "flatten" the
    lfn so that it does not have any sub directories.
    '''
    lfn = orig_lfn
    if conf.get('settings', 'execution_env') == 'condor_pool':
        lfn = re.sub(r'/', '___', orig_lfn)
    return lfn


def my_pfn(orig_path):
    '''
    Depending on the execution environment, use either file:// or go:// PFNs
    '''
    if conf.get('settings', 'execution_env') != 'condor_pool' and \
       re.search(r'sites/ua-mac/raw_data/stereoTop', orig_path):
        path = re.sub(r'.*ua-mac/', 'go://terraref#403204c4-6004-11e6-8316-22000b97daec/ua-mac/', orig_path)
        return PFN(path, site='globusonline')
    return PFN('file://' + orig_path, site='local')


### main ###

conf = ConfigParser.SafeConfigParser({'username': getpass.getuser()})
r = conf.read("workflow/run-settings.conf")
if len(r) != 1:
    print("Unable to read workflow/run-settings.conf")
    sys.exit(1)

dax = ADAG('stereo_rgb')

tools = []
for tool in os.listdir("stereo_rgb"):
    f = File(tool)
    f.addPFN(my_pfn(top_dir + "/stereo_rgb/" + tool))
    dax.addFile(f)
    tools.append(f)

# pick a base dir based on where the workflow is running from
input_base_dir = None
for test_dir in [
        '/data/terraref/sites/ua-mac/raw_data/stereoTop',
        '/lizard/projects/terraref/sites/ua-mac/raw_data/stereoTop'
        ]:
    if os.path.exists(test_dir):
        input_base_dir = test_dir
if not input_base_dir:
    print('Unable to determine data dir. Existing.')
    sys.exit(1)

# do we want to support processing multiple days?
for day in [conf.get('settings', 'day')]:

    count = 0
    fieldmosaic_inputs = []

    # find the timestamp directories
    timestamp_dirs = sorted(os.listdir(input_base_dir + '/' + day))
    # and limit time if asked to
    limit = conf.getint('settings', 'entries_limit')
    if limit > 0:
        timestamp_dirs = timestamp_dirs[0:limit]

    for ts in timestamp_dirs:

        # simplify paths
        ts_dir = input_base_dir + '/' + day + '/' + ts

        # find the uuid for the left/right/metadata
        uuid = glob.glob(ts_dir + '/*_metadata.json')
        if len(uuid) != 1:
            print('Confused about the files in ' + ts_dir)
            continue
        uuid = uuid[0]
        uuid = re.sub(r'.*/', '', uuid)
        uuid = re.sub(r'_.*', '', uuid)

        # verify that we have the expected left, right and metadata files
        if not os.path.exists(ts_dir + '/' + uuid + '_left.bin'):
            print('Expected file does not exist: ' + ts_dir + '/' + uuid + '_left.bin')
            continue
        if not os.path.exists(ts_dir + '/' + uuid + '_right.bin'):
            print('Expected file does not exist: ' + ts_dir + '/' + uuid + '_right.bin')
            continue
        if not os.path.exists(ts_dir + '/' + uuid + '_metadata.json'):
            print('Expected file does not exist: ' + ts_dir + '/' + uuid + '_metadata.json')
            continue

        # input files
        in_left = File(my_lfn('stereoTop/' + day + '/' + ts + '/' + uuid + '_left.bin'))
        in_left.addPFN(my_pfn(ts_dir + '/' + uuid + '_left.bin'))
        dax.addFile(in_left)
        in_right = File(my_lfn('stereoTop/' + day + '/' + ts + '/' + uuid + '_right.bin'))
        in_right.addPFN(my_pfn(ts_dir + '/' + uuid + '_right.bin'))
        dax.addFile(in_right)
        in_metadata = File(my_lfn('stereoTop/' + day + '/' + ts + '/' + uuid + '_metadata.json'))
        in_metadata.addPFN(my_pfn(ts_dir + '/' + uuid + '_metadata.json'))
        dax.addFile(in_metadata)

        # output files
        out_left =  File(my_lfn('ua-mac/Level_1/rgb_geotiff/' + day + '/' + ts + '/rgb_geotiff_L1_ua-mac_' + ts + '_left.tif'))
        out_right = File(my_lfn('ua-mac/Level_1/rgb_geotiff/' + day + '/' + ts + '/rgb_geotiff_L1_ua-mac_' + ts + '_right.tif'))
        out_metadata = File(my_lfn('ua-mac/Level_1/rgb_geotiff/' + day + '/' + ts + '/rgb_geotiff_L1_ua-mac_' + ts + '_metadata.json'))

        # now add a job for bin2tif
        job = Job('bin2tif.sh')
        job.addArguments(in_left, in_right, in_metadata, out_left, out_right, out_metadata, 
                         conf.get('settings', 'clowder_key'))
        for tool in tools:
            job.uses(tool, link=Link.INPUT)
        job.uses(in_left, link=Link.INPUT)
        job.uses(in_right, link=Link.INPUT)
        job.uses(in_metadata, link=Link.INPUT)
        job.uses(out_left, link=Link.OUTPUT, transfer=True)
        job.uses(out_right, link=Link.OUTPUT, transfer=True)
        job.uses(out_metadata, link=Link.OUTPUT, transfer=True)
        #job.addProfile(Profile(Namespace.PEGASUS, 'clusters.size', '20'))
        dax.addJob(job)

        # keep track of the files we need for the next step
        fieldmosaic_inputs.append(out_left)
        fieldmosaic_inputs.append(out_right)
        fieldmosaic_inputs.append(out_metadata)

        count += 1

    print(" ... %s: %d left/right/metadata triples found" %(day, count)) 

    # when running in condorio mode, lfns are flat, so create a tarball with the deep
    # lfns for the fieldmosaic
    if conf.get('settings', 'execution_env') == 'condor_pool':
        rgb_geotiff_tar = merge_rgb_geotiffs("rgb_geotiff_" + day + ".tar.gz", fieldmosaic_inputs, 0)   
        fieldmosaic_inputs = [rgb_geotiff_tar]

    # fieldmosaic outputs
    out_fullfield_tar = File(my_lfn('fullfield.tar.gz'))
    #out_fullfield_tif = File(my_lfn('fullfield_mosaic/fullfield_' + day + '.tif'))
    #out_fullfield_meta = File(my_lfn('fullfield_mosaic/fullfield_' + day + '.meta'))

    # fieldmosaic
    job = Job('fieldmosaic.sh')
    job.addArguments(day, out_fullfield_tar)
    for tool in tools:
        job.uses(tool, link=Link.INPUT)
    for in_file in fieldmosaic_inputs:
        job.uses(in_file, link=Link.INPUT)
    job.uses(out_fullfield_tar, link=Link.OUTPUT, transfer=True)
    #job.uses(out_fullfield_tif, link=Link.OUTPUT, transfer=True)
    #job.uses(out_fullfield_meta, link=Link.OUTPUT, transfer=True)
    dax.addJob(job)
    
    # canopy_cover outputs
    out_trait_csv = File(my_lfn('trait/' + day + '.csv'))

    # canopy_cover
    job = Job('canopy_cover.sh')
    job.addArguments(day, out_trait_csv)
    job.uses(out_fullfield_tar, link=Link.INPUT)
    job.uses(out_trait_csv, link=Link.OUTPUT, transfer=True)
    dax.addJob(job)

# write out the dax
f = open('workflow/generated/dax.xml', 'w')
dax.writeXML(f)
f.close()


