library(adegenet)
library(ape)
library(apex)
library(ggplot2)
library(maps)
library(pegas)
library(phangorn)
library(seqinr)
library(tools)
library(vcfR)
library(stringr)

phylogatr_files <- list.files(path = ".", 
                             pattern = "_aligned\\.(fasta|fa)$", 
                             full.names = TRUE, 
                             recursive = TRUE)

cat("Found", length(phylogatr_files), "files:\n")

results <- data.frame(Species = character(), 
                     Gene = character(), 
                     Pi = numeric(), 
                     N_sequences = integer(),
                     stringsAsFactors = FALSE)

for (f in phylogatr_files) {
  cat("\nProcessing:", f, "\n")
  
  filename <- basename(f)
  filename_no_ext <- file_path_sans_ext(filename)
  
  # Clean data
  name_no_ext <- sub("\\.(fasta|fa)$", "", filename)
  
  if (grepl("_aligned$", name_no_ext)) {
    name_no_aligned <- sub("_aligned$", "", name_no_ext)
  } else {
    cat("Warning: File doesn't end with _aligned:", filename, "\n")
    next
  }
  
  # Split on the last underscore to get gene
  last_underscore_pos <- regexpr("_[^_]*$", name_no_aligned)
  
  if (last_underscore_pos > 0) {
    gene <- substr(name_no_aligned, last_underscore_pos + 1, nchar(name_no_aligned))
    
    species_raw <- substr(name_no_aligned, 1, last_underscore_pos - 1)
    species <- gsub("-+$", "", species_raw)  # Remove trailing hyphens
    species <- gsub("-", " ", species)       # Convert hyphens to spaces
    
    cat("Species:", species, "| Gene:", gene, "\n")
    
    tryCatch({
      seq <- fasta2DNAbin(f, quiet = TRUE)
      
      n <- nrow(seq)
      cat("Number of sequences:", n, "\n")
      
      # Calculate nucleotide diversity (pi)
      if (n > 1) {
        pi <- nuc.div(seq)
        cat("Pi value:", pi, "\n")
      } else {
        pi <- NA
        cat("Warning: Only 1 sequence found, cannot calculate pi\n")
      }
      
      results <- rbind(results, data.frame(Species = species, 
                                          Gene = gene, 
                                          Pi = pi, 
                                          N_sequences = n))
      
    }, error = function(e) {
      cat("Error processing file:", f, "\n")
      cat("Error message:", e$message, "\n")
      
      results <<- rbind(results, data.frame(Species = species, 
                                           Gene = gene, 
                                           Pi = NA, 
                                           N_sequences = NA))
    })
    
  } else {
    cat("Warning: Could not parse gene from filename:", filename)
    next
  }
}

=output_file <- "nucleotide_diversity_results.csv"
write.csv(results, file = output_file, row.names = FALSE)

cat("\nResults saved to:", output_file, "\n")
cat("Total files processed:", nrow(results), "\n")


