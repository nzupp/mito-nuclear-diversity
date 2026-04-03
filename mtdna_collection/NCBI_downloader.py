from Bio import Entrez, SeqIO
import time
import pandas as pd
import os
Entrez.email = "zuppas.3@osu.edu"

def download_sequences(species, gene_variations, max_sequences=50, min_length=200):
    best_count = 0
    best_gene = ""
    best_sequences = []
    
    for gene in gene_variations:
        try:
            query = f'"{species}"[Organism] AND {gene}[Gene] AND {min_length}:10000[SLEN]'
            search_handle = Entrez.esearch(db="nucleotide", term=query, retmax=max_sequences)
            search_results = Entrez.read(search_handle)
            search_handle.close()
            id_list = search_results["IdList"]
            
            if len(id_list) > best_count:
                best_count = len(id_list)
                best_gene = gene
                if id_list:
                    fetch_handle = Entrez.efetch(db="nucleotide", id=id_list, rettype="fasta", retmode="text")
                    sequences = list(SeqIO.parse(fetch_handle, "fasta"))
                    fetch_handle.close()
                    best_sequences = sequences
            time.sleep(0.5)
        except Exception as e:
            print(f"Error downloading {species} - {gene}: {e}")
            continue
    
    return best_sequences, best_count, best_gene

def check_species_has_sequences(species_folder):
    if not os.path.exists(species_folder):
        return False
    
    for root, dirs, files in os.walk(species_folder):
        for file in files:
            if file.endswith('.fasta'):
                return True
    return False

gene_counts = pd.read_csv('gene_counts_improved.csv')
gene_counts = gene_counts.replace("50+", 50)

cols = ["COI_count", "CYTB_count", "ND2_count", "ND4_count"]
gene_counts[cols] = gene_counts[cols].apply(pd.to_numeric, errors="coerce")
mask = (gene_counts[cols] >= 5).any(axis=1)

viable_species = gene_counts[mask]['Species'].tolist()

coi_variations = ["COI", "COX1", "CO1", "cytochrome c oxidase subunit I"]
cytb_variations = ["CYTB", "cytochrome b", "cytochrome B", "COB", "CYT-B", "CYTBL", "CYB"]
nd2_variations = ["ND2", "NAD2", "NADH2", "NDHB"]
nd4_variations = ["ND4", "NAD4", "NADH4", "NDHD", "ND4L", "NAD4L", "NADH4L"]

download_log = []

for i, species in enumerate(viable_species):
    print(f"Processing {i+1}/{len(viable_species)}: {species}")
    
    species_clean = species.replace(" ", "-")
    species_folder = os.path.join(".", species_clean)
    
    if check_species_has_sequences(species_folder):
        print(f"  Species {species} already has sequences. Skipping...")
        continue
    
    os.makedirs(species_folder, exist_ok=True)
    
    coi_seqs, coi_count, coi_gene = download_sequences(species, coi_variations)
    cytb_seqs, cytb_count, cytb_gene = download_sequences(species, cytb_variations)
    nd2_seqs, nd2_count, nd2_gene = download_sequences(species, nd2_variations)
    nd4_seqs, nd4_count, nd4_gene = download_sequences(species, nd4_variations)
    
    if coi_count >= cytb_count and coi_count >= nd2_count and coi_count >= nd4_count and coi_seqs:
        coi_folder = os.path.join(species_folder, "COI")
        os.makedirs(coi_folder, exist_ok=True)
        output_file = os.path.join(coi_folder, f"{species_clean}_COI.fasta")
        SeqIO.write(coi_seqs, output_file, "fasta")
        print(f"  COI: {coi_count} sequences saved to {output_file}")
        download_log.append({
            "Species": species,
            "Gene": "COI",
            "Downloaded": coi_count,
            "Gene_used": coi_gene
        })
    
    elif cytb_count >= nd2_count and cytb_count >= nd4_count and cytb_seqs:
        cytb_folder = os.path.join(species_folder, "CYTB")
        os.makedirs(cytb_folder, exist_ok=True)
        output_file = os.path.join(cytb_folder, f"{species_clean}_CYTB.fasta")
        SeqIO.write(cytb_seqs, output_file, "fasta")
        print(f"  CYTB: {cytb_count} sequences saved to {output_file}")
        download_log.append({
            "Species": species,
            "Gene": "CYTB",
            "Downloaded": cytb_count,
            "Gene_used": cytb_gene
        })
    
    elif nd2_count >= nd4_count and nd2_seqs:
        nd2_folder = os.path.join(species_folder, "ND2")
        os.makedirs(nd2_folder, exist_ok=True)
        output_file = os.path.join(nd2_folder, f"{species_clean}_ND2.fasta")
        SeqIO.write(nd2_seqs, output_file, "fasta")
        print(f"  ND2: {nd2_count} sequences saved to {output_file}")
        download_log.append({
            "Species": species,
            "Gene": "ND2",
            "Downloaded": nd2_count,
            "Gene_used": nd2_gene
        })
    
    elif nd4_seqs:
        nd4_folder = os.path.join(species_folder, "ND4")
        os.makedirs(nd4_folder, exist_ok=True)
        output_file = os.path.join(nd4_folder, f"{species_clean}_ND4.fasta")
        SeqIO.write(nd4_seqs, output_file, "fasta")
        print(f"  ND4: {nd4_count} sequences saved to {output_file}")
        download_log.append({
            "Species": species,
            "Gene": "ND4",
            "Downloaded": nd4_count,
            "Gene_used": nd4_gene
        })
    
    time.sleep(2)

log_df = pd.DataFrame(download_log)
log_df.to_csv('download_log.csv', index=False)
print("Download complete!")
