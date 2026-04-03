import subprocess
import os
from Bio import SeqIO, AlignIO

def align_sequences(input_fasta, output_fasta):
    try:
        # Run MAFFT alignment
        cmd = ["mafft", "--auto", input_fasta]
        with open(output_fasta, "w") as outfile:
            subprocess.run(cmd, stdout=outfile, check=True)
        print(f"Aligned: {input_fasta} -> {output_fasta}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"MAFFT failed for {input_fasta}: {e}")
        return False

def align_all_sequences():
    for species_folder in os.listdir("."):
        if os.path.isdir(species_folder):
            for gene_folder in ["COI", "CYTB", "ND2", "ND4"]:
                gene_path = os.path.join(species_folder, gene_folder)
                if os.path.exists(gene_path):
                    input_file = os.path.join(gene_path, f"{species_folder}_{gene_folder}.fasta")
                    aligned_file = os.path.join(gene_path, f"{species_folder}_{gene_folder}_aligned.fasta")
                    
                    if os.path.exists(input_file):
                        if os.path.exists(aligned_file):
                            print(f"Skipping (already aligned): {aligned_file}")
                        else:
                            align_sequences(input_file, aligned_file)

align_all_sequences()
