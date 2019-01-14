#!/bin/bash

if [ "X$1" == "Xcondor_pool" ]; then

    cat <<EOF

cont terraref {
    type "docker"
    image "docker:///terraref/workflow-pilot:latest"
}

cont terraref_sing {
    type "singularity"
    image "http://localhost/terraref.img"
}

tr bin2tif.sh {
    site local {
        type "STAGEABLE"
        container "terraref"
        pfn "file://$PWD/wrappers/bin2tif.sh"
    }
}

tr nrmac.sh {
    site local {
        type "STAGEABLE"
        container "terraref"
        pfn "file://$PWD/wrappers/nrmac.sh"
    }
}

tr merge.sh {
    site local {
        type "STAGEABLE"
        container "terraref"
        pfn "file://$PWD/wrappers/merge.sh"
    }
}

tr fieldmosaic.sh {
    site local {
        type "STAGEABLE"
        container "terraref"
        pfn "file://$PWD/wrappers/fieldmosaic.sh"
    }
}

tr canopy_cover.sh {
    site local {
        type "STAGEABLE"
        container "terraref"
        pfn "file://$PWD/wrappers/canopy_cover.sh"
    }
}

tr submitter.sh {
    site local {
        type "STAGEABLE"
        container "terraref"
        pfn "file://$PWD/wrappers/submitter.sh"
    }
}

EOF

elif [ "X$1" == "Xpsc_bridges" ]; then

    cat <<EOF

cont terraref {
    type "singularity"
    #image "go://terraref#403204c4-6004-11e6-8316-22000b97daec/tests/workflow/workflow-pilot/workflow_terra/images/terraref.img"
    #image "http://localhost/terraref.img"
    #image "http://141.142.209.167/terraref.img"
    image "shub://craig-willis/terraref-singularity:def"
}

tr bin2tif.sh {
    site psc_bridges {
        type "STAGEABLE"
        container "terraref"
        #pfn "go://terraref#403204c4-6004-11e6-8316-22000b97daec/tests/workflow/workflow-pilot/workflow_terra/wrappers/bin2tif.sh"
        pfn "scp://centos@141.142.209.167$PWD/wrappers/bin2tif.sh"
    }
}

tr nrmac.sh {
    site psc_bridges {
        type "STAGEABLE"
        container "terraref"
        #pfn "go://terraref#403204c4-6004-11e6-8316-22000b97daec/tests/workflow/workflow-pilot/workflow_terra/wrappers/nrmac.sh"
        pfn "scp://centos@141.142.209.167$PWD/wrappers/nrmac.sh"
    }
}

tr merge.sh {
    site psc_bridges {
        type "STAGEABLE"
        container "terraref"
        #pfn "go://terraref#403204c4-6004-11e6-8316-22000b97daec/tests/workflow/workflow-pilot/workflow_terra/wrappers/merge.sh"
        pfn "scp://centos@141.142.209.167$PWD/wrappers/merge.sh"
    }
}

tr fieldmosaic.sh {
    site psc_bridges {
        type "STAGEABLE"
        container "terraref"
        pfn "scp://centos@141.142.209.167$PWD/wrappers/fieldmosaic.sh"
        #pfn "go://terraref#403204c4-6004-11e6-8316-22000b97daec/tests/workflow/workflow-pilot/workflow_terra/wrappers/fieldmosaic.sh"
    }
}

tr canopy_cover.sh {
    site psc_bridges {
        type "STAGEABLE"
        container "terraref"
        pfn "scp://centos@141.142.209.167$PWD/wrappers/canopy_cover.sh"
        #pfn "go://terraref#403204c4-6004-11e6-8316-22000b97daec/tests/workflow/workflow-pilot/workflow_terra/wrappers/canopy_cover.sh"
    }
}

tr submitter.sh {
    site psc_bridges {
        type "STAGEABLE"
        container "terraref"
        pfn "scp://centos@141.142.209.167$PWD/wrappers/submitter.sh"
        #pfn "go://terraref#403204c4-6004-11e6-8316-22000b97daec/tests/workflow/workflow-pilot/workflow_terra/wrappers/submitter.sh"
    }
}

EOF

else


    cat <<EOF

tr bin2tif.sh {
    site isi_shared {
        type "INSTALLED"
        pfn "/lizard/projects/terraref/bin/bin2tif.sh"
    }
}

tr merge.sh {
    site isi_shared {
        type "INSTALLED"
        pfn "/lizard/projects/terraref/bin/merge.sh"
    }
}

tr fieldmosaic.sh {
    site isi_shared {
        type "INSTALLED"
        pfn "/lizard/projects/terraref/bin/fieldmosaic.sh"
    }
}

tr canopy_cover.sh {
    site isi_shared {
        type "INSTALLED"
        pfn "/lizard/projects/terraref/bin/canopy_cover.sh"
    }
}

EOF

fi


