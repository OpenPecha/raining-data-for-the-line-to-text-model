from pathlib import Path
import re
import requests
import hashlib
import rdflib
import boto3
import os

os.environ["AWS_SHARED_CREDENTIALS_FILE"] = "~/.aws/credentials"
OCR_OUTPUT_BUCKET = "archive.tbrc.org"
S3_client = boto3.client("s3")

def get_work_id(img_group):
    url = f"https://purl.bdrc.io/resource/{img_group}.ttl"
    res = requests.get(url)
    g = rdflib.Graph()
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
        print("Work ID not found in the URL.")

def get_img_group_and_image(url):
    ex = re.compile(r"bdr:(.*?)::([^/]+)")
    match = ex.search(url)
    img_group = match.group(1)
    img_name = match.group(2)
    return img_group,img_name

def get_url(text_path):
    text = Path(text_path).read_text(encoding="utf-8")
    ex = re.compile(r"(.*)\n\-")
    match = ex.search(text)
    return match.group(1)

def get_no_of_images(text_path):
    text = Path(text_path).read_text(encoding="utf-8")
    ex = re.compile(r"-\n-\n(.*)")
    match = ex.search(text)
    images_text = match.group(1)
    images_text = images_text.strip()
    images = text.split("\n\n")
    num_images = len(images)
    return num_images

def get_images_name(img_name,no_of_images):
    images = [img_name]
    pattern = r"^(.*?)(\d+)\.(.*)$"
    match = re.search(pattern, img_name)
    if match:
        prefix_chars = match.group(1)
        last_number = match.group(2)
        file_extension = match.group(3)
    cur_postfix = int(last_number)+1
    if no_of_images == 1:
        return images
    for i in range(no_of_images-1):
        images.append(prefix_chars+str(cur_postfix)+"."+file_extension)
        cur_postfix+=1
    return images

def get_hash(work_id):
    md5 = hashlib.md5(str.encode(work_id))
    two = md5.hexdigest()[:2]
    return two


def download_images(work_id,img_group,images,download_path):
    images_path = []
    if download_path is None:
        download_path = "./images"
        Path(download_path).mkdir(parents=False)
    hash_two = get_hash(work_id)
    for image in images:
        object_key = f"Works/{hash_two}/{work_id}/images/{work_id}-{img_group}/{image}"
        try:
            S3_client.download_file(OCR_OUTPUT_BUCKET, object_key, download_path+f"/{image}")
            images_path.append(download_path)
            print("Object downloaded successfully.")
        except boto3.botocore.errorfactory.ClientError as e:
            print("Error:", str(e))
    return images_path

def get_images(text_path,download_path=None):
    url = get_url(text_path)
    img_group,img_name = get_img_group_and_image(url)
    no_of_images = get_no_of_images(text_path)
    work_id = get_work_id(img_group)
    images = get_images_name(img_name,no_of_images)
    images_path = download_images(work_id,img_group,images,download_path)
    return images_path


if __name__ == "__main__":
    text_path = "tests/data/test.txt"
    get_images(text_path)