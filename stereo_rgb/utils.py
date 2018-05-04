import requests
from terrautils.metadata import get_terraref_metadata

def get_clowder_metadata(key, timestamp):
    resp = requests.get("https://terraref.ncsa.illinois.edu/clowder/api/datasets?key=%s&exact=true&title=stereoTop - %s" % (key, timestamp))
    resp.raise_for_status()
    
    datasetId = resp.json()[0]["id"]

    resp = requests.get("https://terraref.ncsa.illinois.edu/clowder/api/datasets/%s/metadata.jsonld?key=%s" % (datasetId, key))
    resp.raise_for_status()
    
    content = resp.json()[1]["content"]

    metadata = get_terraref_metadata(content, 'stereoTop')

    return metadata