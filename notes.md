# Notes from Pegasus/Condor integration for TERRA-REF

We've started integrating with the TERRA-REF pipeline based on the pilot workflow example https://github.com/terraref/workflow-pilot/tree/master/workflow. This documents a few of the problems we encountered along the way.

## LFN and PFN

We've had some difficulty understanding the role of LFNs and PFNs. At first, we understood the LFN to simply be a label for reference, but it is also the name of the file in the working directory during execution. The process of replacing `/` with `___` was also problematic, as we used fully-qualified paths (which we now understand should've been relative).

## `nobody`?

We ran into problems with access to the `docker` daemon or when `pip` installing Python packages. It was a surprise to find that jobs were running as `nobody` and not `centos`. This was due to a condor configuration related to the `UID_DOMAIN` and resolved via:

```
vi /etc/condor/config.d/50-central-manager.config
TRUST_UID_DOMAIN = True
sudo systemctl restart condor
```

## Debugging

Debugging problems was challening. 
* `pegasus-status` is useful
* `pegasus-analyzer` is even more useful
* `sudo ls -lR /var/lib/condor/execute` can show the current state of things in condor
* Don't forget the condor tools, e.g., `condor_q`


## Docker
* On Centos, the group is `dockerroot` not `docker`...
* However, our current approach of trying to use the NFS mounted `/data` won't work due to https://jira.isi.edu/browse/PM-1298

## Singularity
* Singularity seemed more promising, since we could modify the image to mount `/data`
* This works fine, but the data is still copied
```
Bootstrap: docker
From: terraref/workflow-pilot

%post
   mkdir /data
```

## /data, symlinks, and container
* Symlinking seems to be the right approach for what we're trying to achieve https://pegasus.isi.edu/documentation/transfer.php#transfer_symlink
* But apparently it's disabled when using containers


## Using the UIUC Condor Cluster

`ssh htc-login.campuscluster.illinois.edu`

## Running on PSC

On `terra-condor`, activate the virtual environment with the correct version of Tornado and start the `pyglidein_server`:
```
. ~/venv/bin/activate
 pyglidein_server --debug --delay 20 --port 22001 --constraint "'WantPSCBridges == True'"
```

Make sure the webserver is running to serve the Singularity image
```
ps -ef | grep SimpleHttpServer
# if not running
sudo su - 
cd /images
nohup python -m SimpleHTTPServer 80 & 
```

Run the workflow:
```
cd workflow-pilot/workflow_terra
./submit.sh
```

On PSC, start the `glidein`, which is simply a Slurm job that allocates some resources to be condor nodes:
```
cd terraref-glidein
. pyglidein/bin/activate
pyglidein_client --config=bridges-RM.conf --secrets=secrets.conf
```

Debugging tips:
* Use `pegasus-status` to look at the status of the workflow -- i.e., which job is currently running
```
$ pegasus-status -l /home/centos/workflows/stereo_rgb-1541238701/stereo_rgb-1541238701
STAT  IN_STATE  JOB
Run      02:42  stereo_rgb_stereovis_ir_sensors_partialplots_sorghum6_sun_flir_eastedge_mn_2_9ec3c25e-a155-410d-8cb6-5a26f12a5436-0 ( /home/centos/workflows/stereo_rgb-1541238701/stereo_rgb-1541238701 )
Run      00:45   ┣━bin2tif_sh_ID0000001
Run      00:44   ┣━bin2tif_sh_ID0000003
Run      00:44   ┣━bin2tif_sh_ID0000005
Run      00:43   ┗━bin2tif_sh_ID0000007
```
* `tail workflow/00/00/*` for quick debugging
* `condor-status` will show you whether the glidein is running
* If a condor task is `held`, use `condor_q -l | grep HoldReason` to get the details
* `squeue -u $USER` on PSC will show you whats running in Slurm


