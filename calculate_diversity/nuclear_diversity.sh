#!/bin/bash
#SBATCH --account="placeholder"
#SBATCH --job-name=phylogatr
#SBATCH --output=phylogatr.out
#SBATCH --error=phylogatr.err
#SBATCH --time=48:00:00
#SBATCH --mem=16G 
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1

module load vcftools/0.1.16

find . -name "*.vcf" -type f | while read vcf_file; do
    vcf_dir=$(dirname "$vcf_file")
    filename=$(basename "$vcf_file" .vcf)
    
    vcf_version=$(head -1 "$vcf_file" | grep -o "VCFv[0-9]\+\.[0-9]\+")
    
    if [[ "$vcf_version" == "VCFv4.3" ]]; then
        working_vcf="${vcf_dir}/${filename}_temp_4.2.vcf"
        sed 's/^##fileformat=VCFv4.3/##fileformat=VCFv4.2/' "$vcf_file" > "$working_vcf"
    else
        working_vcf="$vcf_file"
    fi
    
    # Run 10k window
    output_prefix_10k="${vcf_dir}/${filename}_nucleotide_diversity_10k"
    vcftools --vcf "$working_vcf" \
             --window-pi 10000 \
             --out "$output_prefix_10k"
    
    # Run 1k window
    output_prefix_1k="${vcf_dir}/${filename}_nucleotide_diversity_1k"
    vcftools --vcf "$working_vcf" \
             --window-pi 1000 \
             --out "$output_prefix_1k"
    
    if [[ "$vcf_version" == "VCFv4.3" ]]; then
        rm "$working_vcf"
    fi
done

CSV_OUTPUT="pi_summary_combined.csv"
echo "species,mean_pi_10k,mean_pi_1k" > "$CSV_OUTPUT"

find . -name "*_nucleotide_diversity_10k.windowed.pi" -type f | while read pi_file_10k; do
    species_name=$(basename "$pi_file_10k" "_nucleotide_diversity_10k.windowed.pi")
    
    pi_file_1k="${pi_file_10k/_nucleotide_diversity_10k.windowed.pi/_nucleotide_diversity_1k.windowed.pi}"
    
    if [ -s "$pi_file_10k" ]; then
        mean_10k=$(awk 'NR>1 && $5!="nan" && $5!="" && $5!="-nan" {
            sum+=$5; count++
        } 
        END {
            if(count>0) printf "%.6f", sum/count
            else printf "NA"
        }' "$pi_file_10k")
    else
        mean_10k="NA"
    fi
    
    if [ -s "$pi_file_1k" ]; then
        mean_1k=$(awk 'NR>1 && $5!="nan" && $5!="" && $5!="-nan" {
            sum+=$5; count++
        } 
        END {
            if(count>0) printf "%.6f", sum/count
            else printf "NA"
        }' "$pi_file_1k")
    else
        mean_1k="NA"
    fi
    
    echo "$species_name,$mean_10k,$mean_1k" >> "$CSV_OUTPUT"
done
