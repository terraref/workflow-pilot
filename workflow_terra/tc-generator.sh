#!/bin/bash

if [ "X$1" == "Xcondor_pool" ]; then

    cat <<EOF

cont terraref {
    type "singularity"
    image "docker://terraref/workflow-pilot"
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


