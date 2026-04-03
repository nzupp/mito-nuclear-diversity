# Missing resume from figshare.py implementation, could add later

import os
import csv
import requests
import time

# Zenodo requires access token; removed for open source version
ACCESS_TOKEN = 'placeholder'
host = 'https://zenodo.org/api/records'

# Use "q=vcf" to narrow down to datasets mentioning vcf
q = 'vcf'
headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

size = 100
page = 1

total_vcf_count = 0

# Root directory for downloads and metadata
base_download_dir = "Zenodo_vcfs"
os.makedirs(base_download_dir, exist_ok=True)

vcf_metadata_list = []

while True:
    params = {
        'q': q,
        'page': page,
        'size': size
    }
    
    response = requests.get(host, headers=headers, params=params)
    
    if response.status_code != 200:
        print("Error:", response.status_code)
        print(response.text)
        break
    
    results = response.json()
    records = results.get('hits', {}).get('hits', [])
    
    if not records:
        break
    
    for record in records:
        # Get the metadata
        metadata = record.get('metadata', {})
        record_doi = metadata.get('doi', record.get('doi', ''))
        title = metadata.get('title', 'No Title')
        keywords = metadata.get('keywords', [])
        keywords_str = ", ".join(keywords) if isinstance(keywords, list) else keywords
        
        if record_doi and "/" in record_doi:
            doi_parts = record_doi.split("/", 1)
            part1 = doi_parts[0]
            part2 = doi_parts[1]
        else:
            part1 = "unknown_doi_prefix"
            part2 = record_doi or "unknown_doi_suffix"
        
        vcf_files = []
        for file_info in record.get('files', []):
            file_name = file_info.get('key', '')
            if file_name.lower().endswith('.vcf'):
                vcf_files.append(file_info)
        
        if not vcf_files:
            continue
        
        # Only create directory if this article has VCFs
        record_download_dir = os.path.join(base_download_dir, part1, part2)
        os.makedirs(record_download_dir, exist_ok=True)
        
        for file_info in vcf_files:
            file_name = file_info.get('key', '')
            download_url = file_info.get('links', {}).get('self')
            
            if download_url:
                total_vcf_count += 1
                print(f"Downloading {file_name} ...")
                file_response = requests.get(download_url, headers=headers, stream=True)
                if file_response.status_code == 200:
                    local_filepath = os.path.join(record_download_dir, file_name)
                    with open(local_filepath, 'wb') as f:
                        for chunk in file_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"Downloaded {file_name} successfully!")
                else:
                    print(f"Failed to download {file_name}. Status: {file_response.status_code}")
                
                # Append metadata regardless of download status to track all known VCF files
                vcf_metadata_list.append({
                    "Zenodo DOI": record_doi,
                    "Title": title,
                    "Paper DOI": None,
                    "Species": keywords_str,
                    "vcf_file": file_name
                })
            else:
                print(f"No download URL found for {file_name}")
    
    page += 1
    time.sleep(2)
    

metadata_filepath = "zenodo_metadata.csv"
with open(metadata_filepath, mode='w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ["Zenodo DOI", "Title", "Paper DOI", "Species", "vcf_file"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    writer.writeheader()
    for data in vcf_metadata_list:
        writer.writerow(data)
    
    
    
    
