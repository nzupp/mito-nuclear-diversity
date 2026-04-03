# Simpler metadata + donwload in one pass with resume

import os
import csv
import requests
import time

host = "https://api.figshare.com/v2"

# Use "q=vcf" to narrow down to datasets mentioning vcf
q = "vcf"
size = 100
page = 1

headers = {}
total_vcf_count = 0

# Root directory for downloads and metadata
base_download_dir = "Figshare_downloads"
os.makedirs(base_download_dir, exist_ok=True)

vcf_metadata_list = []

while True:
    params = {
        'search_for': q,
        'page': page,
        'page_size': size
    }
    
    response = requests.get(f"{host}/articles", headers=headers, params=params)
    
    if response.status_code != 200:
        print("Error:", response.status_code)
        print(response.text)
        break
    
    articles = response.json()
    
    if not articles:
        break
    
    for article in articles:
        article_id = article.get("id")
        
        # Get full article details
        detail_response = requests.get(f"{host}/articles/{article_id}", headers=headers)
        if detail_response.status_code != 200:
            print(f"Error retrieving details for article {article_id}")
            continue
        
        details = detail_response.json()
        record_doi = details.get("doi", "")
        title = details.get("title", "No Title")
        
        keywords = details.get("tags", [])
        keywords_str = ", ".join(keywords) if isinstance(keywords, list) else keywords
        
        if record_doi and "/" in record_doi:
            doi_parts = record_doi.split("/", 1)
            part1 = doi_parts[0]
            part2 = doi_parts[1]
        else:
            part1 = "unknown_doi_prefix"
            part2 = record_doi or "unknown_doi_suffix"
        
        vcf_files = []
        for file_info in details.get("files", []):
            file_name = file_info.get("name", "")
            if file_name.lower().endswith(".vcf"):
                vcf_files.append(file_info)
        
        if not vcf_files:
            continue
        
        # Only create directory if this article has VCFs
        record_download_dir = os.path.join(base_download_dir, part1, part2)
        os.makedirs(record_download_dir, exist_ok=True)
        
        for file_info in vcf_files:
            file_name = file_info.get("name", "")
            download_url = file_info.get("download_url")
            
            if download_url:
                total_vcf_count += 1
                local_filepath = os.path.join(record_download_dir, file_name)
                if os.path.exists(local_filepath):
                    print(f"{file_name} already exists in {record_download_dir}. Skipping download.")
                else:
                    print(f"Downloading {file_name} ...")
                    file_response = requests.get(download_url, headers=headers, stream=True)
                    if file_response.status_code == 200:
                        with open(local_filepath, 'wb') as f:
                            for chunk in file_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        print(f"Downloaded {file_name} successfully!")
                    else:
                        print(f"Failed to download {file_name}. Status: {file_response.status_code}")
                
                # Append metadata regardless of download status to track all known VCF files
                vcf_metadata_list.append({
                    "Figshare DOI": record_doi,
                    "Title": title,
                    "Paper DOI": None,
                    "Species": keywords_str,
                    "vcf_file": file_name
                })
            else:
                print(f"No download URL found for {file_name}")
    
    page += 1
    time.sleep(2)

metadata_filepath = "figshare_metadata.csv"
with open(metadata_filepath, mode='w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ["Figshare DOI", "Title", "Paper DOI", "Species", "vcf_file"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    writer.writeheader()
    for data in vcf_metadata_list:
        writer.writerow(data)
    
    
    
    
