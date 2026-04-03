import os
import json
import requests
import urllib.parse
import time

host = 'https://datadryad.org'

# Use "q=vcf" to narrow down to datasets mentioning vcf
search_endpoint = f'{host}/api/v2/search'
headers = {"Accept": "application/json"}

size = 100
page = 1

# Root directory for downloads and metadata
download_root = "dryad_downloads"
os.makedirs(download_root, exist_ok=True)
metadata_file = "dryad_vcf_metadata.json"

# PHASE 1: Download metadata

all_metadata = []

while True:
    params = {
        "q": "vcf",
        "page": page,
        "per_page": size
    }
    
    response = requests.get(search_endpoint, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error retrieving search results on page {page}: {response.status_code} {response.text}")
        break

    json_response = response.json()
    datasets = json_response.get("_embedded", {}).get("stash:datasets", [])
    
    if not datasets:
        print(f"No datasets found on page {page}. Ending metadata retrieval loop.")
        break

    all_metadata.extend(datasets)
    
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(all_metadata, f, indent=2)
    
    page += 1
    time.sleep(2)

# PHASE 2: Use saved metadata to download files

with open(metadata_file, "r", encoding="utf-8") as f:
    all_metadata = json.load(f)

for j, dataset in enumerate(all_metadata):
    doi = dataset.get("identifier", f"dataset_{j}")

    # Create folder for this dataset (replace ':' with '_' for file-system safety)
    dataset_folder = os.path.join(download_root, doi.replace(":", "_"))
    os.makedirs(dataset_folder, exist_ok=True)

    encoded_doi = urllib.parse.quote(doi, safe='')
    dataset_url = f"{host}/api/v2/datasets/{encoded_doi}"
    ds_response = requests.get(dataset_url, headers=headers)
    if ds_response.status_code != 200:
        print(f"Failed to retrieve full metadata for {doi} (status {ds_response.status_code}). Skipping.")
        continue

    ds_json = ds_response.json()
    
    # Get the link for the latest version
    version_link = ds_json.get("_links", {}).get("stash:version", {}).get("href")
    if not version_link:
        print(f"No version information found for {doi}. Skipping.")
        continue
    
    if version_link.startswith("/"):
        version_link = host + version_link
    
    # Extract version ID
    version_id = version_link.rstrip("/").split("/")[-1]

    files_url = f"{host}/api/v2/versions/{version_id}/files"
    files_response = requests.get(files_url, headers=headers)
    if files_response.status_code != 200:
        print(f"Failed to retrieve files list for {doi} (status {files_response.status_code}). Skipping.")
        continue

    files_json = files_response.json()
    # Files are embedded under _embedded -> "stash:files"
    file_list = files_json.get("_embedded", {}).get("stash:files", [])
    if not file_list:
        print(f"No files found for {doi} (version {version_id}).")
        continue

    # Download only files ending with .vcf or .vcf.gz (case-insensitive)
    for f in file_list:
        # Extract file ID from _links.self.href (e.g., "/api/v2/files/200")
        self_href = f.get("_links", {}).get("self", {}).get("href")
        if self_href:
            file_id = self_href.rstrip("/").split("/")[-1]
        else:
            file_id = None

        if not file_id:
            print("Skipping file because no ID is available.")
            continue

        # Get the file name; try "path" field first, else use a default name.
        file_name = f.get("path") or f.get("attributes", {}).get("filename", f"file_{file_id}")
        # Check if file is a .vcf or .vcf.gz (case-insensitive)
        if not (file_name.lower().endswith('.vcf') or file_name.lower().endswith('.vcf.gz')):
            print(f"Skipping '{file_name}' (not a .vcf or .vcf.gz file).")
            continue

        # Build the download URL using /files/{id}/download
        file_download_url = f"{host}/api/v2/files/{file_id}/download"

        # Set header to expect binary data
        download_headers = {"Accept": "application/octet-stream"}
        file_resp = requests.get(file_download_url, headers=download_headers)
        if file_resp.status_code == 200:
            local_file_path = os.path.join(dataset_folder, file_name)
            with open(local_file_path, "wb") as out_file:
                out_file.write(file_resp.content)
        else:
            print(f"Failed to download '{file_name}' (status code {file_resp.status_code})")

        time.sleep(1)

    time.sleep(2)



