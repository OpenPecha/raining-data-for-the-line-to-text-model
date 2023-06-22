import re
from pathlib import Path
from openpecha.buda import api
import requests
import rdflib
from rdflib import Graph


def get_work_id(img_group):
    url = f"https://purl.bdrc.io/resource/{img_group}.ttl"
    res = requests.get(url)
    g = Graph()
    try:
        g.parse(data=res.text, format="ttl")
    except:
        print(f"ttl Contains bad syntax")
        return {}
    namespaces = {
    "bdo": rdflib.Namespace("http://purl.bdrc.io/ontology/core/"),
    "bdr": rdflib.Namespace("http://purl.bdrc.io/resource/"),
    }

    # Iterate over the triples and extract the value of bdo:volumeOf
    for subject, predicate, obj in g:
        if predicate == namespaces["bdo"].volumeOf:
            volume_of = obj
    
    pattern = r"/resource/([A-Z0-9]+)$"

    # Search for the pattern in the URL
    match = re.search(pattern, volume_of)

    if match:
        work_id = match.group(1)
        return work_id
    else:
        print("Resource ID not found in the URL.")


def get_img_group_and_image(url):
    ex = re.compile(r"bdr:(.*)::(.*)/")
    match = ex.search(url)
    img_group = match.group(1)
    img_name = match.group(2)
    return img_group,img_name

def get_url(text_path):
    text = Path(text_path).read_text(encoding="utf-8")
    ex = re.compile(r"(.*)\n\-")
    match = ex.search(text)
    return match.group(1)


def main(text_path):
    url = get_url(text_path)
    img_group,img_name = get_img_group_and_image(url)
    work_id = get_work_id(img_group)
    print(work_id)

if __name__ == "__main__":
    test_path = "tests/data/test.txt"
    main(test_path)