# Notes from Pegasus/Condor integration for TERRA-REF

Ran into several problems getting Docker, Singularity or even just straight python working.

## LFN and PFN

* The LFN is not just a label, it's the name of the copied file in the working directory during execution

## `nobody`?

Jobs running as `nobody` were a bit of a surprise:

```
vi /etc/condor/config.d/50-central-manager.config
TRUST_UID_DOMAIN = True
sudo systemctl restart condor
```

## Debugging
Lots of lessons learned in debugging
* `pegasus-status` is useful
* `pegasus-analyzer` is even more useful
* sudo ls -lR /var/lib/condor/execute can show the current state of things
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

