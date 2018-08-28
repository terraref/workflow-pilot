#!/usr/bin/env python

import os
import re
import json

from Pegasus.DAX3 import *


root_dir = "/data/terraref/sites/"
limit_dates = ["2018-07-01", "2018-07-02", "2018-07-03"]
execution_env = 'condor_pool'
dry_run = True


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
    if execution_env == 'condor_pool':
        lfn = re.sub(r'/', '___', orig_lfn)
    return lfn

def my_pfn(orig_path):
    '''
    Depending on the execution environment, use either file:// or go:// PFNs
    '''
    if execution_env != 'condor_pool' and \
            re.search(r'sites/ua-mac/raw_data/stereoTop', orig_path):
        path = re.sub(r'.*ua-mac/', 'go://terraref#403204c4-6004-11e6-8316-22000b97daec/ua-mac/', orig_path)
        return PFN(path, site='globusonline')
    return PFN('file://' + orig_path, site='local')

def generate_tools_list():
    """
    return all python scripts in /tools directory
    """
    return [
        "tools/bin2tif.py",
        "tools/nrmac.py",
        "tools/canopyCover.py",
        "tools/fieldmosaic.py"
    ]

def process_raw_filelist():
    """
    scan raw stereoTop directory and create workflow dax files by scan name
    """
    scan_list = []
    curr_scan = ""

    dates = sorted(os.listdir(os.path.join(root_dir, "ua-mac/raw_data/stereoTop")))
    for date in dates:
        if date not in limit_dates:
            continue
        date_dir = os.path.join(os.path.join(root_dir, "ua-mac/raw_data/stereoTop"), date)

        timestamps = sorted(os.listdir(date_dir))
        for ts in timestamps:
            ts_dir = os.path.join(date_dir, ts)

            meta, lbin, rbin = None, None, None

            files = os.listdir(ts_dir)
            for fname in files:
                fpath = os.path.join(ts_dir, fname)
                if fname.endswith("metadata.json"):
                    meta = fpath
                if fname.endswith("left.bin"):
                    lbin = fpath
                if fname.endswith("right.bin"):
                    rbin = fpath

            # TODO: More logging
            if meta and lbin and rbin:
                scan = get_scan_from_metadata(meta)

                if scan and scan != curr_scan:
                    if len(scan_list) > 0:
                        print("%s - [%s] %s datasets" % (date, curr_scan, len(scan_list)))
                        create_scan_dax(curr_scan, scan_list)

                    scan_list = []
                    curr_scan = scan

                # TODO: What do we do if there is no scan in the metadata? "unknown_scan_{date}"?
                scan_list.append({"left": lbin, "right": rbin, "metadata": meta})

    if len(scan_list) > 0:
        print("%s - [%s] %s datasets" % (date, curr_scan, len(scan_list)))
        create_scan_dax(curr_scan, scan_list)

def get_scan_from_metadata(meta):
    """
    extract scan name & hash from metadata.json file
    """
    with open(meta, 'r') as f:
        md = json.load(f)

    scan_name = None

    if 'lemnatec_measurement_metadata' in md:
        if 'gantry_system_variable_metadata' in md['lemnatec_measurement_metadata']:
            if 'Script copy path on FTP server' in md['lemnatec_measurement_metadata']['gantry_system_variable_metadata']:
                ftp = md['lemnatec_measurement_metadata']['gantry_system_variable_metadata']['Script copy path on FTP server']
                scan_name = os.path.basename(ftp).replace(".cs", "").lower()

    return scan_name

def create_job(script, args, inputs, outputs):
    """
    shorthand for defining a Job as part of a workflow
    """
    job = Job(script)
    for arg in args:
        job.addArguments(arg)

    # all jobs will have access to python scripts
    for tool in generate_tools_list():
        job.uses(tool, link=Link.INPUT)

    for input in inputs:
        job.uses(input, link=Link.INPUT)

    for output in outputs:
        job.uses(output, link=Link.OUTPUT, transfer=True)

    #job.addProfile(Profile(Namespace.PEGASUS, 'clusters.size', '20'))
    return job

def create_scan_dax(scan_name, scan_list):
    """
    register all jobs in stereoTop workflow and create dax file for single scan
    """
    dax = ADAG('stereo_rgb_'+scan_name)

    count = 0
    fieldmosaic_inputs = []
    fieldmosaic_quality_inputs = []

    # the scan will be associated with the day on which it begins
    fieldmosaic_day = None
    for fileset in scan_list:
        # interpret date and timestamp of scan from folder structure of first image
        day = fileset["left"].split("/")[-3]
        ts  = fileset["left"].split("/")[-2]
        if not fieldmosaic_day:
            fieldmosaic_day = day

        # converted geoTIFFs, quality score JSON and quality score geoTIFF end up here
        rgb_geotiff_out_dir = os.path.join(root_dir, 'ua-mac/Level_1/rgb_geotiff/%s/%s/' % (day, ts))

        """
        ----- bin2tif (convert raw BIN files to geoTIFFs) -----
        """
        # INPUT
        in_left = File(my_lfn(fileset["left"]))
        in_left.addPFN(my_pfn(os.path.join(ts, os.path.basename(fileset["left"]))))
        dax.addFile(in_left)
        in_right = File(my_lfn(fileset["right"]))
        in_right.addPFN(my_pfn(os.path.join(ts, os.path.basename(fileset["right"]))))
        dax.addFile(in_right)
        in_meta = File(my_lfn(fileset["metadata"]))
        in_meta.addPFN(my_pfn(os.path.join(ts, os.path.basename(fileset["metadata"]))))
        dax.addFile(in_meta)

        # OUTPUT
        out_left = File(my_lfn(rgb_geotiff_out_dir+'rgb_geotiff_L1_ua-mac_%s_left.tif' % ts))
        out_right = File(my_lfn(rgb_geotiff_out_dir+'rgb_geotiff_L1_ua-mac_%s_right.tif' % ts))
        out_meta = File(my_lfn(rgb_geotiff_out_dir+'clean_metadata.json'))

        # JOB
        args = [in_left, in_right, in_meta, out_left, out_right, out_meta, ts]
        inputs = [in_left, in_right, in_meta]
        outputs = [out_left, out_right, out_meta]
        job = create_job('bin2tif.sh', args, inputs, outputs)
        dax.addJob(job)

        """
        ----- nrmac (determine quality score of input geoTIFF and create low-res output geoTIFF) -----
        """
        # OUTPUT
        out_qual_left  = File(my_lfn(rgb_geotiff_out_dir+'rgb_geotiff_L1_ua-mac_%s_nrmac_left.tif' % ts))
        out_nrmac = File(my_lfn(rgb_geotiff_out_dir+'nrmac_scores.json'))

        # JOB
        args = [out_left, out_right, out_qual_left, out_nrmac]
        inputs = [out_left, out_right, in_meta]
        outputs = [out_qual_left, out_nrmac]
        job = create_job('nrmac.sh', args, inputs, outputs)
        dax.addJob(job)

        # needed for upcoming stitching
        fieldmosaic_inputs.append(out_left)
        fieldmosaic_quality_inputs.append(out_qual_left)
        count += 1

        """
        ----- Clowder submission (upload bin2tif files to Clowder) -----
        """
        clowder_ids = rgb_geotiff_out_dir+'clowder_ids.json'
        args = ['rgb_geotiff', scan_name, rgb_geotiff_out_dir]
        outputs = [clowder_ids]
        job = create_job('submitter.sh', args, [], outputs)
        dax.addJob(job)

    # fullfield mosaics and canopy cover CSVs end up here
    fullfield_out_dir = os.path.join(root_dir, 'ua-mac/Level_1/fullfield/%s/' % day)

    """
    ----- fieldmosaic QAQC (create fullfield stitch of the nrmac quality geoTIFFs) -----
    """
    # INPUT
    if dry_run:
        file_paths = 'workflow/json/%s/fullfield_L1_ua-mac_%s_%s_nrmac_file_paths.json' % (day, day, scan_name)
    else:
        file_paths = fullfield_out_dir+'fullfield_L1_ua-mac_%s_%s_nrmac_file_paths.json' % (day, scan_name)
    os.makedirs(os.path.dirname(file_paths))
    with open(file_paths, 'w') as j:
        json.dump(sorted(fieldmosaic_quality_inputs), j)
    fieldmosaic_quality_json = File(my_lfn(file_paths))
    dax.addFile(fieldmosaic_quality_json)

    # OUTPUT
    # when running in condorio mode, lfns are flat, so create a tarball with the deep lfns for the fieldmosaic
    if execution_env == 'condor_pool':
        rgb_geotiff_tar = merge_rgb_geotiffs("rgb_geotiff_quality_" + scan_name + ".tar.gz", fieldmosaic_quality_inputs, 0)
        fieldmosaic_quality_inputs = [rgb_geotiff_tar]
    # the quality stitched output is small, so don't tar this up even for condorio
    fieldmosaic_quality_outputs = [
        file_paths.replace("_file_paths.json", ".vrt"),
        file_paths.replace("_file_paths.json", ".tif")]

    # JOB
    args = [fieldmosaic_quality_json, scan_name, 'true']
    inputs = fieldmosaic_quality_inputs + [fieldmosaic_quality_json]
    outputs = list(map(lambda x: File(my_lfn(x)), fieldmosaic_quality_outputs))
    job = create_job('fieldmosaic.sh', args, inputs, outputs)
    dax.addJob(job)

    """
    ----- fieldmosaic (create fullfield stitch of the actual geoTIFFs) -----
    """
    # INPUT
    if dry_run:
        file_paths = 'workflow/json/%s/fullfield_L1_ua-mac_%s_%s_file_paths.json' % (day, day, scan_name)
    else:
        file_paths = fullfield_out_dir+'fullfield_L1_ua-mac_%s_%s_file_paths.json' % (day, scan_name)
    os.makedirs(os.path.dirname(file_paths))
    with open(file_paths, 'w') as j:
        json.dump(sorted(fieldmosaic_inputs), j)
    fieldmosaic_json = File(my_lfn(file_paths))

    # OUTPUT
    # when running in condorio mode, lfns are flat, so create a tarball with the deep lfns for the fieldmosaic
    full_resolution_geotiff = file_paths.replace("_file_paths.json", ".tif")
    if execution_env == 'condor_pool':
        rgb_geotiff_tar = merge_rgb_geotiffs("rgb_geotiff_" + scan_name + ".tar.gz", fieldmosaic_inputs, 0)
        fieldmosaic_inputs = [rgb_geotiff_tar]
        fieldmosaic_outputs = ['fullfield_'+scan_name+'.tar.gz']
        canopy_cover_input = 'fullfield_'+scan_name+'.tar.gz'
    else:
        fieldmosaic_outputs = [
            file_paths.replace("_file_paths.json", ".vrt"),
            full_resolution_geotiff,
            file_paths.replace("_file_paths.json", "_thumb.tif"),
            file_paths.replace("_file_paths.json", "_10pct.tif"),
            file_paths.replace("_file_paths.json", ".png")]
        canopy_cover_input = file_paths.replace("_file_paths.json", ".tif")

    # JOB
    args = [fieldmosaic_json, scan_name, 'false']
    inputs = fieldmosaic_inputs + [fieldmosaic_json]
    outputs = list(map(lambda x: File(my_lfn(x)), fieldmosaic_outputs))
    job = create_job('fieldmosaic.sh', args, inputs, outputs)
    dax.addJob(job)

    """
    ----- canopyCover (generate plot-level canopy cover trait CSVs) -----
    """
    # OUTPUT
    cc_bety = file_paths.replace("_file_paths.json", "_canopycover_bety.csv")
    cc_geo = file_paths.replace("_file_paths.json", "_canopycover_geo.csv")
    out_bety_csv = File(my_lfn(cc_bety))
    out_geo_csv = File(my_lfn(cc_geo))

    # JOB
    args = [canopy_cover_input, scan_name, full_resolution_geotiff]
    inputs = [canopy_cover_input]
    outputs = [out_bety_csv, out_geo_csv]
    job = create_job('canopy_cover.sh', args, inputs, outputs)
    dax.addJob(job)

    """
    ----- Clowder submission (upload bin2tif files to Clowder) -----
    """
    clowder_ids = fullfield_out_dir+scan_name+'_clowder_ids.json'
    args = ['fullfield', scan_name, fullfield_out_dir]
    outputs = [clowder_ids]
    job = create_job('submitter.sh', args, [], outputs)
    dax.addJob(job)

    """
    ----- BETY submission (upload trait CSVs) -----
    """
    bety_ids = fullfield_out_dir+scan_name+'_bety_ids.json'
    args = ['bety', 'canopy_cover', cc_bety]
    outputs = [bety_ids]
    job = create_job('submitter.sh', args, [], outputs)
    dax.addJob(job)

    """
    ----- Geostreams submission (upload geo CSVs - requires fullfield Clowder ID) -----
    """
    geo_ids = fullfield_out_dir+scan_name+'_geo_ids.json'
    args = ['geo', 'canopy_cover', cc_geo]
    inputs = [clowder_ids]
    outputs = [geo_ids]
    job = create_job('submitter.sh', args, inputs, outputs)
    dax.addJob(job)

    # write out the dax
    dax_file = 'workflow/generated/%s.xml' % scan_name
    f = open(dax_file, 'w')
    dax.writeXML(f)
    f.close()

    print("...wrote %s" % dax_file)


process_raw_filelist()
