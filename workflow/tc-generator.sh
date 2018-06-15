#!/bin/bash

if [ "X$1" == "Xcondor_pool" ]; then

    cat <<EOF

cont terraref {
    type "singularity"
    image "http://workflow.isi.edu/TERRAREF/terraref.img"
}

tr bin2tif.sh {
    site local {
        type "STAGEABLE"
        container "terraref"
        pfn "file://$PWD/workflow/wrappers/bin2tif.sh"
    }
}

tr merge.sh {
    site local {
        type "STAGEABLE"
        container "terraref"
        pfn "file://$PWD/workflow/wrappers/merge.sh"
    }
}

tr fieldmosaic.sh {
    site local {
        type "STAGEABLE"
        container "terraref"
        pfn "file://$PWD/workflow/wrappers/fieldmosaic.sh"
    }
}

tr canopy_cover.sh {
    site local {
        type "STAGEABLE"
        container "terraref"
        pfn "file://$PWD/workflow/wrappers/canopy_cover.sh"
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


