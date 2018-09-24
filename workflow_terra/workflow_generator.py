#!/usr/bin/env python

import os
import re
import json

from Pegasus.DAX3 import *

from terrautils.betydb import dump_experiments


top_dir = os.getcwd()
scan_root = "/data/terraref/sites/"
limit_dates = ["2018-07-01", "2018-07-02", "2018-07-03"]
scan_size_limit = 1
execution_env = 'condor_pool'
dry_run = True

if not dry_run:
    root_dir = "/data/terraref/sites/"
else:
    root_dir = top_dir+"/workflow/sites/"


# TODO: Checks for existing files that skip certain jobs if they don't need to be run?
# TODO: Implement plot clipping outputs alongside the existing pipeline



def add_merge_job(dax, final_name, chunk, level, job_number, final):
    """
    adds a merge job
    """
    j = Job(name="merge.sh")
    out_file_name = final_name + "-%d-%d.tar.gz" %(level, job_number)
    out_file = File(out_file_name)
    if final:
        out_file_name = final_name
        out_file = File(final_name)
    j.uses(out_file, link=Link.OUTPUT, transfer=final)
    j.addArguments(out_file)
    for f in chunk:
        flfn = File(my_lfn(f))
        j.uses(flfn, link=Link.INPUT)
        j.addArguments(flfn)
    j.addProfile(Profile(Namespace.CONDOR, 'request_disk', '100 GB'))
    dax.addJob(j)
    return out_file_name

def merge_rgb_geotiffs(dax, final_name, inputs, level):
    """
    creates a set of small jobs to merge geotifs to a tarball
    """
    max_files = 60
    new_outputs = []

    input_chunks = [inputs[i:i + max_files] for i in xrange(0, len(inputs), max_files)]

    job_count = 0
    for chunk in input_chunks:
        job_count = job_count + 1
        f = add_merge_job(dax, final_name, chunk, level, job_count, False)
        new_outputs.append(f)

    # end condition - only one chunk
    if len(new_outputs) <= max_files:
        return add_merge_job(dax, final_name, new_outputs, level + 1, 1, True)

    return merge_rgb_geotiffs(dax, final_name, new_outputs, level + 1)

def my_lfn(orig_lfn):
    '''
    Depending on the execution environment, we might have to "flatten" the
    lfn so that it does not have any sub directories.
    '''
    lfn = orig_lfn
    if execution_env == 'condor_pool':
        lfn = re.sub(r'/', '___', orig_lfn)

    lfn = re.sub(r'^___', '', lfn)
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
    out = {}

    # Set BETYDB_LOCAL_CACHE_FOLDER = /tools directory
    print("Dumping BETY experiments file into "+os.environ.get('BETYDB_LOCAL_CACHE_FOLDER', "/home/extractor/"))
    dump_experiments()

    toollist = [
        os.path.join(top_dir+"/tools", "bin2tif.py"),
        os.path.join(top_dir+"/tools", "nrmac.py"),
        os.path.join(top_dir+"/tools", "canopyCover.py"),
        os.path.join(top_dir+"/tools", "fieldmosaic.py"),
        os.path.join(top_dir+"/tools", "submit_clowder.py"),
        os.path.join(top_dir+"/tools", "submit_bety.py"),
        os.path.join(top_dir+"/tools", "submit_geo.py"),
        os.path.join(top_dir+"/tools", "bety_experiments.json")
    ]

    print("Including /tools directory files")
    for t in toollist:
        tool_daxf = File(my_lfn(t))
        tool_daxf.addPFN(my_pfn(t))
        # Use filename as dict key in case we need it as input later
        out[t.split("/")[-1]] = tool_daxf

    sensor_metadata_list = [
        os.path.join(scan_root, "ua-mac/sensor-metadata/sensors/stereo/sensor_fixed_metadata.json"),
        os.path.join(scan_root, "ua-mac/sensor-metadata/sensors/flirIrCamera/sensor_fixed_metadata.json"),
        os.path.join(scan_root, "ua-mac/sensor-metadata/sensors/scanner3D/sensor_fixed_metadata.json"),
        os.path.join(scan_root, "ua-mac/sensor-metadata/sensors/VNIR/sensor_fixed_metadata.json"),
        os.path.join(scan_root, "ua-mac/sensor-metadata/sensors/scanalyzer/sensor_fixed_metadata.json")
    ]
    print("Including sensor fixed metadata")
    for s in sensor_metadata_list:
        sensor_metadata_daxf = File(my_lfn(s))
        sensor_metadata_daxf.addPFN(my_pfn(s))
        # Use '$SENSOR_fixed' as dict key in case we need it as input later
        out[s.split("/")[-2]+"_fixed"] = sensor_metadata_daxf

    return out

def process_raw_filelist():
    """
    scan raw stereoTop directory and create workflow dax files by scan name
    """
    scan_list = []
    curr_scan = ""

    tools = generate_tools_list()

    print("Beginning scan of %s" % os.path.join(scan_root, "ua-mac/raw_data/stereoTop"))
    dates = sorted(os.listdir(os.path.join(scan_root, "ua-mac/raw_data/stereoTop")))
    for date in dates:
        if date not in limit_dates:
            continue
        date_dir = os.path.join(os.path.join(scan_root, "ua-mac/raw_data/stereoTop"), date)
        print("Scanning %s" % date_dir)

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
                        create_scan_dax(date, curr_scan, scan_list, tools)
                        # TODO: Temporary
                        return

                    scan_list = []
                    curr_scan = scan

                elif len(scan_list) > scan_size_limit and scan_size_limit > 0:
                    print("%s - [%s] %s datasets" % (date, curr_scan, len(scan_list)))
                    create_scan_dax(date, curr_scan, scan_list, tools)
                    return

                # TODO: What do we do if there is no scan in the metadata? "unknown_scan_{date}"?
                scan_list.append({"left": lbin, "right": rbin, "metadata": meta})

    if len(scan_list) > 0:
        print("%s - [%s] %s datasets" % (date, curr_scan, len(scan_list)))
        create_scan_dax(date, curr_scan, scan_list, tools)

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

def create_job(script, args, inputs, outputs, tools):
    """
    shorthand for defining a Job as part of a workflow
    """
    job = Job(script)
    for arg in args:
        job.addArguments(arg)

    # all jobs will have access to python scripts
    for tool in tools:
        job.uses(tools[tool], link=Link.INPUT)

    for input in inputs:
        job.uses(input, link=Link.INPUT)

    for output in outputs:
        job.uses(output, link=Link.OUTPUT, transfer=True)

    #job.addProfile(Profile(Namespace.PEGASUS, 'clusters.size', '20'))
    return job

def create_scan_dax(date, scan_name, scan_list, tools):
    """
    register all jobs in stereoTop workflow and create dax file for single scan
    """

    dax_file = 'workflow/generated/%s__%s.xml' % (date, scan_name)
    print("Creating %s" % dax_file)

    dax = ADAG('stereo_rgb_'+scan_name)

    # Add tools to dax
    for tool in tools:
        dax.addFile(tools[tool])

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
        rgb_geotiff_out_dir = 'ua-mac/Level_1/rgb_geotiff/%s/%s/' % (day, ts)
        if not os.path.exists(rgb_geotiff_out_dir):
            os.makedirs(rgb_geotiff_out_dir)


        """
        ----- bin2tif (convert raw BIN files to geoTIFFs) -----
        """
        # INPUT
        in_left = fileset["left"]
        in_right = fileset["right"]
        in_meta = fileset["metadata"]
        in_left_daxf = File(my_lfn(in_left))
        in_left_daxf.addPFN(my_pfn(in_left))
        dax.addFile(in_left_daxf)
        in_right_daxf = File(my_lfn(in_right))
        in_right_daxf.addPFN(my_pfn(in_right))
        dax.addFile(in_right_daxf)
        in_meta_daxf = File(my_lfn(in_meta))
        in_meta_daxf.addPFN(my_pfn(in_meta))
        dax.addFile(in_meta_daxf)

        # OUTPUT
        out_left = rgb_geotiff_out_dir+'rgb_geotiff_L1_ua-mac_%s_left.tif' % ts
        out_right = rgb_geotiff_out_dir+'rgb_geotiff_L1_ua-mac_%s_right.tif' % ts
        out_meta = rgb_geotiff_out_dir+'clean_metadata.json'
        out_left_daxf = File(my_lfn(out_left))
        out_right_daxf = File(my_lfn(out_right))
        out_meta_daxf = File(my_lfn(out_meta))

        # JOB
        args = [in_left_daxf, in_right_daxf, in_meta_daxf, out_left_daxf, out_right_daxf, out_meta_daxf, ts,
                tools["stereo_fixed"], tools["bety_experiments.json"], tools["bin2tif.py"]]
        inputs = [in_left_daxf, in_right_daxf, in_meta_daxf]
        outputs = [out_left_daxf, out_right_daxf, out_meta_daxf]
        job = create_job('bin2tif.sh', args, inputs, outputs, tools)
        dax.addJob(job)


        """
        ----- nrmac (determine quality score of input geoTIFF and create low-res output geoTIFF) -----
        """
        # OUTPUT
        out_qual_left = rgb_geotiff_out_dir+'rgb_geotiff_L1_ua-mac_%s_nrmac_left.tif' % ts
        out_qual_right = rgb_geotiff_out_dir+'rgb_geotiff_L1_ua-mac_%s_nrmac_right.tif' % ts
        out_nrmac = rgb_geotiff_out_dir+'nrmac_scores.json'
        out_qual_left_daxf = File(my_lfn(out_qual_left))
        out_qual_right_daxf = File(my_lfn(out_qual_right))
        out_nrmac_daxf = File(my_lfn(out_nrmac))

        # JOB
        args = [out_left_daxf, out_right_daxf, out_meta_daxf, out_qual_left_daxf, out_qual_right_daxf,
                out_nrmac_daxf, tools["nrmac.py"]]
        inputs = [out_left_daxf, out_right_daxf, out_meta_daxf]
        outputs = [out_qual_left_daxf, out_qual_right_daxf, out_nrmac_daxf]
        job = create_job('nrmac.sh', args, inputs, outputs, tools)
        dax.addJob(job)

        # needed for upcoming stitching
        fieldmosaic_inputs.append(out_left)
        fieldmosaic_quality_inputs.append(out_qual_left)


        # TODO: TEMPORARY -------------------------------------------------
        # write out the dax
        dax_file = 'workflow/generated/singletest.xml' # % (date, scan_name)
        if not os.path.isdir(os.path.dirname(dax_file)):
            os.makedirs(os.path.dirname(dax_file))
        f = open(dax_file, 'w')
        dax.writeXML(f)
        f.close()
        return
        # TODO: TEMPORARY -------------------------------------------------


        """
        ----- Clowder submission (upload bin2tif files to Clowder) -----
        """
        if dry_run:
            clowder_ids = 'workflow/json/rgb_'+scan_name+'_clowder_ids.json'
            out_cid_daxf = File(my_lfn(clowder_ids))
            out_cid_daxf.addPFN(my_pfn(top_dir+"/"+clowder_ids))
        else:
            clowder_ids = rgb_geotiff_out_dir+scan_name+'_clowder_ids.json'
            out_cid_daxf = File(my_lfn(clowder_ids))
        args = ['rgb_geotiff', scan_name, rgb_geotiff_out_dir]
        inputs = [out_left_daxf, out_right_daxf, out_meta_daxf, out_qual_left_daxf, out_qual_right_daxf, out_nrmac_daxf]
        outputs = [out_cid_daxf]
        job = create_job('submitter.sh', args, inputs, outputs, tools)
        dax.addJob(job)

    # fullfield mosaics and canopy cover CSVs end up here
    fullfield_out_dir = 'ua-mac/Level_1/fullfield/%s/' % fieldmosaic_day
    if not os.path.exists(fullfield_out_dir):
        os.makedirs(fullfield_out_dir)


    """
    ----- fieldmosaic QAQC (create fullfield stitch of the nrmac quality geoTIFFs) -----
    """
    # INPUT
    if dry_run:
        file_paths_q = 'workflow/json/%s/fullfield_L1_ua-mac_%s_%s_nrmac_file_paths.json' % (fieldmosaic_day, fieldmosaic_day, scan_name)
        fieldmosaic_quality_json = File(my_lfn(file_paths_q))
        fieldmosaic_quality_json.addPFN(my_pfn(top_dir+"/"+file_paths_q))
        dax.addFile(fieldmosaic_quality_json)
    else:
        file_paths_q = fullfield_out_dir+'fullfield_L1_ua-mac_%s_%s_nrmac_file_paths.json' % (fieldmosaic_day, scan_name)
        fieldmosaic_quality_json = File(my_lfn(file_paths_q))
        dax.addFile(fieldmosaic_quality_json)
    if not os.path.isdir(os.path.dirname(file_paths_q)):
        os.makedirs(os.path.dirname(file_paths_q))
    with open(file_paths_q, 'w') as j:
        for path in fieldmosaic_quality_inputs:
            j.write("%s\n" % path)

    # OUTPUT
    # when running in condorio mode, lfns are flat, so create a tarball with the deep lfns for the fieldmosaic
    if execution_env == 'condor_pool':
        rgb_geotiff_tar = merge_rgb_geotiffs(dax, "rgb_geotiff_quality_" + scan_name + ".tar.gz",
                                             fieldmosaic_quality_inputs, 0)
        fieldmosaic_quality_inputs = [rgb_geotiff_tar]
    else:
        fieldmosaic_quality_inputs = list(map(lambda x: File(my_lfn(x)), fieldmosaic_quality_inputs))
    # the quality stitched output is small, so don't tar this up even for condorio
    fieldmosaic_quality_outputs = [
        file_paths_q.replace("_file_paths.json", ".vrt"),
        file_paths_q.replace("_file_paths.json", ".tif")]

    # JOB
    args = [file_paths_q, scan_name, 'true']
    inputs = fieldmosaic_quality_inputs + [fieldmosaic_quality_json]
    outputs = list(map(lambda x: File(my_lfn(x)), fieldmosaic_quality_outputs))
    job = create_job('fieldmosaic.sh', args, inputs, outputs, tools)
    dax.addJob(job)


    """
    ----- fieldmosaic (create fullfield stitch of the actual geoTIFFs) -----
    """
    # INPUT
    if dry_run:
        file_paths = 'workflow/json/%s/fullfield_L1_ua-mac_%s_%s_file_paths.json' % (fieldmosaic_day, fieldmosaic_day, scan_name)
        fieldmosaic_json = File(my_lfn(file_paths))
        fieldmosaic_json.addPFN(my_pfn(top_dir+"/"+file_paths))
        dax.addFile(fieldmosaic_json)
    else:
        file_paths = fullfield_out_dir+'fullfield_L1_ua-mac_%s_%s_file_paths.json' % (fieldmosaic_day, scan_name)
        fieldmosaic_json = File(my_lfn(file_paths))
        dax.addFile(fieldmosaic_json)
    if not os.path.isdir(os.path.dirname(file_paths)):
        os.makedirs(os.path.dirname(file_paths))
    with open(file_paths, 'w') as j:
        for path in fieldmosaic_inputs:
            j.write("%s\n" % path)

    # OUTPUT
    # when running in condorio mode, lfns are flat, so create a tarball with the deep lfns for the fieldmosaic
    full_resolution_geotiff = file_paths.replace("_file_paths.json", ".tif")
    if execution_env == 'condor_pool':
        rgb_geotiff_tar = merge_rgb_geotiffs(dax, "rgb_geotiff_" + scan_name + ".tar.gz",
                                             fieldmosaic_inputs, 0)
        fieldmosaic_inputs = [rgb_geotiff_tar]
        fieldmosaic_outputs = ['fullfield_'+scan_name+'.tar.gz']
        canopy_cover_input = 'fullfield_'+scan_name+'.tar.gz'
        canopy_cover_input_daxf = File(my_lfn(canopy_cover_input))
    else:
        fieldmosaic_inputs = list(map(lambda x: File(my_lfn(x)), fieldmosaic_inputs))
        fieldmosaic_outputs = [
            file_paths.replace("_file_paths.json", ".vrt"),
            full_resolution_geotiff,
            file_paths.replace("_file_paths.json", "_thumb.tif"),
            file_paths.replace("_file_paths.json", "_10pct.tif"),
            file_paths.replace("_file_paths.json", ".png")]
        canopy_cover_input = file_paths.replace("_file_paths.json", ".tif")
        canopy_cover_input_daxf = File(my_lfn(canopy_cover_input))

    # JOB
    args = [file_paths, scan_name, 'false']
    inputs = fieldmosaic_inputs + [fieldmosaic_json]
    outputs = list(map(lambda x: File(my_lfn(x)), fieldmosaic_outputs))
    job = create_job('fieldmosaic.sh', args, inputs, outputs, tools)
    dax.addJob(job)


    """
    ----- canopyCover (generate plot-level canopy cover trait CSVs) -----
    """
    # OUTPUT
    cc_bety = file_paths.replace("_file_paths.json", "_canopycover_bety.csv")
    cc_geo = file_paths.replace("_file_paths.json", "_canopycover_geo.csv")
    cc_bety_daxf = File(my_lfn(cc_bety))
    cc_geo_daxf = File(my_lfn(cc_geo))

    # JOB
    args = [canopy_cover_input, scan_name, full_resolution_geotiff, tools["bety_experiments.json"]]
    inputs = [canopy_cover_input_daxf]
    outputs = [cc_bety_daxf, cc_geo_daxf]
    job = create_job('canopy_cover.sh', args, inputs, outputs, tools)
    dax.addJob(job)


    """
    ----- Clowder submission (upload bin2tif files to Clowder) -----
    """
    if dry_run:
        clowder_ids = 'workflow/json/ff_'+scan_name+'_clowder_ids.json'
        out_cid_daxf = File(my_lfn(clowder_ids))
        out_cid_daxf.addPFN(my_pfn(top_dir+"/"+clowder_ids))
    else:
        clowder_ids = fullfield_out_dir+scan_name+'_clowder_ids.json'
        out_cid_daxf = File(my_lfn(clowder_ids))
    args = ['fullfield', scan_name, fullfield_out_dir]
    inputs = ([fieldmosaic_quality_json, fieldmosaic_json] +
              list(map(lambda x: File(my_lfn(x)), fieldmosaic_quality_outputs)) +
              list(map(lambda x: File(my_lfn(x)), fieldmosaic_inputs)))
    outputs = [out_cid_daxf]
    job = create_job('submitter.sh', args, inputs, outputs, tools)
    dax.addJob(job)


    """
    ----- BETY submission (upload trait CSVs) -----
    """
    if dry_run:
        bety_ids = 'workflow/json/'+scan_name+'_bety_ids.json'
        out_bety_daxf = File(my_lfn(bety_ids))
        out_bety_daxf.addPFN(my_pfn(top_dir+"/"+bety_ids))
    else:
        bety_ids = fullfield_out_dir+scan_name+'_bety_ids.json'
        out_bety_daxf = File(my_lfn(bety_ids))
    args = ['bety', 'canopy_cover', cc_bety]
    inputs = [cc_bety_daxf]
    outputs = [out_bety_daxf]
    job = create_job('submitter.sh', args, inputs, outputs, tools)
    dax.addJob(job)


    """
    ----- Geostreams submission (upload geo CSVs - requires fullfield Clowder ID) -----
    """
    if dry_run:
        geo_ids = 'workflow/json/'+scan_name+'_geo_ids.json'
        out_geo_daxf = File(my_lfn(geo_ids))
        out_geo_daxf.addPFN(my_pfn(top_dir+"/"+geo_ids))
    else:
        geo_ids = fullfield_out_dir+scan_name+'_geo_ids.json'
        out_geo_daxf = File(my_lfn(geo_ids))
    args = ['geo', 'canopy_cover', cc_geo]
    inputs = [out_cid_daxf, cc_geo_daxf]
    outputs = [out_geo_daxf]
    job = create_job('submitter.sh', args, inputs, outputs, tools)
    dax.addJob(job)

    # write out the dax
    dax_file = 'workflow/generated/%s__%s.xml' % (date, scan_name)
    if not os.path.isdir(os.path.dirname(dax_file)):
        os.makedirs(os.path.dirname(dax_file))
    f = open(dax_file, 'w')
    dax.writeXML(f)
    f.close()

    print("...wrote %s" % dax_file)


process_raw_filelist()
