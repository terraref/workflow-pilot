#!/usr/bin/env python

import os
import json

from Pegasus.DAX3 import *


raw_dir = "/home/clowder/sites/ua-mac/raw_data/stereoTop"

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

def generate_tools_list():
    return [
        "tools/bin2tif.py",
        "tools/nrmac.py",
        "tools/canopyCover.py",
        "tools/fieldmosaic.py"
    ]

def generate_raw_filelist():
    # Scan raw data directory and build jobs by scan name
    scan_list = []
    curr_scan = ""

    dates = sorted(os.listdir(raw_dir))
    for date in dates:
        date_dir = os.path.join(raw_dir, date)

        timestamps = sorted(os.listdir(date_dir))
        for ts in timestamps:
            ts_dir = os.path.join(date_dir, ts)

            meta, lbin, rbin = None, None, None, None

            files = os.listdir(ts_dir)
            for fname in files:
                fpath = os.path.join(ts_dir, fname)
                if fname.endswith("metadata.json"):
                    meta = fpath
                if fname.endswith("left.bin"):
                    lbin = fpath
                if fname.endswith("right.bin"):
                    rbin = fpath

            if meta and lbin and rbin:
                scan = get_scan_from_metadata(meta)

                if scan and scan != curr_scan:
                    if scan_list.length > 0:
                        create_scan_job(curr_scan, scan_list)

                    scan_list = []
                    curr_scan = scan

                scan_list.append({"left": lbin, "right": rbin, "metadata": meta})

    if scan_list.length > 0:
        create_scan_job(curr_scan, scan_list)

def get_scan_from_metadata(meta):
    # Extract scan name & hash from metadata.json file
    with open(meta, 'r') as f:
        md = json.load(f)

    scan_name = None

    if 'lemnatec_measurement_metadata' in md:
        if 'gantry_system_variable_metadata' in md['lemnatec_measurement_metadata']:
            if 'Script copy path on FTP server' in md['lemnatec_measurement_metadata']['gantry_system_variable_metadata']:
                ftp = md['lemnatec_measurement_metadata']['gantry_system_variable_metadata']['Script copy path on FTP server']
                scan_name = os.path.basename(ftp).replace(".cs", "").lower()

    return scan_name

def create_scan_job(scan_name, scan_list):
    # Extract scan name & hash from metadata.json file
    dax = ADAG('stereo_rgb_'+scan_name)

    tools = generate_tools_list()

    count = 0
    fieldmosaic_inputs = []

    fieldmosaic_day = None
    for triple in scan_list:
        fileset = scan_list[triple]
        day = fileset["left"].split("/")[-3]
        ts  = fileset["left"].split("/")[-2]
        out_dir = 'ua-mac/Level_1/rgb_geotiff/%s/%s/' % (day, ts)
        if not fieldmosaic_day:
            fieldmosaic_day = day

        # input files
        in_left = File(my_lfn(fileset["left"]))
        in_left.addPFN(my_pfn(os.path.join(ts, os.path.basename(fileset["left"]))))
        dax.addFile(in_left)
        in_right = File(my_lfn(fileset["right"]))
        in_right.addPFN(my_pfn(os.path.join(ts, os.path.basename(fileset["right"]))))
        dax.addFile(in_right)
        in_meta = File(my_lfn(fileset["metadata"]))
        in_meta.addPFN(my_pfn(os.path.join(ts, os.path.basename(fileset["metadata"]))))
        dax.addFile(in_meta)

        # output files
        out_left = File(my_lfn(out_dir+'rgb_geotiff_L1_ua-mac_%s_left.tif' % ts))
        out_right = File(my_lfn(out_dir+'rgb_geotiff_L1_ua-mac_%s_right.tif' % ts))
        out_meta = File(my_lfn(out_dir+'clean_metadata.json'))

        # add a job for bin2tif
        job = Job('bin2tif.sh')
        job.addArguments(in_left, in_right, in_meta, out_left, out_right, out_meta, ts)
        for tool in tools:
            job.uses(tool, link=Link.INPUT)
        job.uses(in_left, link=Link.INPUT)
        job.uses(in_right, link=Link.INPUT)
        job.uses(in_meta, link=Link.INPUT)
        job.uses(out_left, link=Link.OUTPUT, transfer=True)
        job.uses(out_right, link=Link.OUTPUT, transfer=True)
        job.uses(out_meta, link=Link.OUTPUT, transfer=True)
        #job.addProfile(Profile(Namespace.PEGASUS, 'clusters.size', '20'))
        dax.addJob(job)

        # quality scoring files
        out_nrmac = File(my_lfn(out_dir+'nrmac_scores.json'))

        # add jobs for NRMAC quality scoring
        job = Job('nrmac.sh')
        job.addArguments(out_left, out_right, out_nrmac)
        for tool in tools:
            job.uses(tool, link=Link.INPUT)
        job.uses(out_left, link=Link.INPUT)
        job.uses(out_right, link=Link.INPUT)
        job.uses(out_nrmac, link=Link.OUTPUT, transfer=True)
        dax.addJob(job)

        # keep track of the files we need for the next step
        fieldmosaic_inputs.append(out_left)
        #fieldmosaic_inputs.append(out_right)
        #fieldmosaic_inputs.append(out_meta)
        count += 1

    print("%s: %d datasets found" % (scan_name, count))

    file_paths = 'ua-mac/Level_1/fullfield/%s/fullfield_L1_ua-mac_%s_%s_file_paths.json' % (day, day, scan_name)
    with open(file_paths, 'w') as j:
        json.dump(sorted(fieldmosaic_inputs), j)
    fieldmosaic_json = File(my_lfn(file_paths))

    # when running in condorio mode, lfns are flat, so create a tarball with the deep lfns for the fieldmosaic
    if conf.get('settings', 'execution_env') == 'condor_pool':
        rgb_geotiff_tar = merge_rgb_geotiffs("rgb_geotiff_" + scan_name + ".tar.gz", fieldmosaic_inputs, 0)
        fieldmosaic_inputs = [rgb_geotiff_tar]
        fieldmosaic_outputs = ['fullfield_'+scan_name+'.tar.gz']
        canopy_cover_input = 'fullfield_'+scan_name+'.tar.gz'
    else:
        fieldmosaic_outputs = [
            file_paths.replace("_file_paths.json", ".vrt"),
            file_paths.replace("_file_paths.json", ".tif"),
            file_paths.replace("_file_paths.json", "_thumb.tif"),
            file_paths.replace("_file_paths.json", "_10pct.tif"),
            file_paths.replace("_file_paths.json", ".png")
        ]

    # fieldmosaic
    job = Job('fieldmosaic.sh')
    job.addArguments(fieldmosaic_json, scan_name)
    for tool in tools:
        job.uses(tool, link=Link.INPUT)
    for in_file in fieldmosaic_inputs:
        job.uses(in_file, link=Link.INPUT)
    job.uses(fieldmosaic_json, link=Link.INPUT)
    for out_file in fieldmosaic_outputs:
        job.uses(File(my_lfn(out_file)), link=Link.OUTPUT, transfer=True)
    dax.addJob(job)

    # canopy_cover outputs
    cc_bety = file_paths.replace("_file_paths.json", "_canopycover_bety.csv")
    cc_geo = file_paths.replace("_file_paths.json", "_canopycover_geo.csv")
    out_bety_csv = File(my_lfn(cc_bety))
    out_geo_csv = File(my_lfn(cc_geo))

    # canopy_cover
    job = Job('canopy_cover.sh')
    job.addArguments(canopy_cover_input, scan_name)
    job.uses(canopy_cover_input, link=Link.INPUT)
    job.uses(out_bety_csv, link=Link.OUTPUT, transfer=True)
    job.uses(out_geo_csv, link=Link.OUTPUT, transfer=True)
    dax.addJob(job)

# write out the dax
f = open('workflow/generated/dax.xml', 'w')
dax.writeXML(f)
f.close()
