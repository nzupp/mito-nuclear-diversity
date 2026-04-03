# make one CSV row per VCF file

import os
import pandas as pd

df = pd.read_csv("dryad_metadata_csv.csv")

new_rows = []

for idx, row in df.iterrows():
    dryad_doi = row["Dryad DOI"]
    try:
        folder1, folder2 = dryad_doi.split("/")
    except ValueError:
        print(f"Unexpected DOI format: {dryad_doi}")
        continue

    folder1 = "doi_" + folder1
    dataset_dir = os.path.join("dryad_downloads", folder1, folder2)
    
    if not os.path.isdir(dataset_dir):
        print(f"Directory not found: {dataset_dir}")
        continue

    for file in os.listdir(dataset_dir):
        if file.endswith(".vcf"):
            new_row = row.copy()
            new_row["vcf_file"] = file
            new_rows.append(new_row)

df_exploded = pd.DataFrame(new_rows)

df_exploded.to_csv("dryad_metadata_expanded.csv", index=False)


