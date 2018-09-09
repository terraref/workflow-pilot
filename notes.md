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


