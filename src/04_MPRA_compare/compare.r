#!/usr/bin/env Rscript
# compare.r: robust per-cell-type comparisons using DESeq2

library(DESeq2)

# 0. Read comparison file (requires Sample and Group columns)
args <- commandArgs(trailingOnly=TRUE)
if (length(args) < 3) {
  stop("Usage: Rscript compare.r <normalized_counts_file.tsv> <comparison_file.tsv> <output_dir>")
}
norm_file <- args[1]
comp_file <- args[2]
out_dir   <- args[3]

# Ensure output directory exists
if (!dir.exists(out_dir)) {
  dir.create(out_dir, recursive=TRUE)
}

comp <- read.delim(comp_file, header=TRUE, stringsAsFactors=FALSE)
required_cols <- c("Comparison","Group1","Group2")
if (!all(required_cols %in% colnames(comp))) {
  stop("Comparison file must contain columns: Comparison, Group1, Group2")
}

# 1. Read resolved normalized counts TSV with explicit ID column
df <- read.delim(norm_file,
                 header=TRUE,
                 stringsAsFactors=FALSE,
                 check.names=FALSE)
if (!"ID" %in% colnames(df)) {
  stop("Normalized counts TSV must contain an 'ID' column")
}
# Build count matrix from all columns except ID, preserving order
counts_mat <- as.matrix(df[, setdiff(colnames(df), "ID")])
rownames(counts_mat) <- df$ID

# 2. Loop over provided comparisons
for(i in seq_len(nrow(comp))) {
  comp_name <- comp$Comparison[i]
  # split comma-separated sample names and trim whitespace
  grp1 <- trimws(unlist(strsplit(comp$Group1[i], ",")))
  grp2 <- trimws(unlist(strsplit(comp$Group2[i], ",")))
  samp  <- c(grp1, grp2)
  # check samples exist
  missing <- setdiff(samp, colnames(counts_mat))
  if(length(missing)>0) stop("Unknown samples: ", paste(missing, collapse=", "))
  # build colData
  group_factor <- factor(c(rep("Group1", length(grp1)), rep("Group2", length(grp2))),
                         levels=c("Group1","Group2"))
  colData <- data.frame(row.names=samp, Group=group_factor)
  # subset counts
  sub_counts <- counts_mat[, samp, drop=FALSE]
  # DESeq2 on RNA counts with plasmid baseline offset
  # Identify plasmid columns in counts_mat
  plasmid_idx <- grep("^Plasmid", colnames(counts_mat))
  # Compute plasmid baseline (mean normalized count per feature)
  dna_baseline <- rowMeans(counts_mat[, plasmid_idx, drop=FALSE])
  # Build integer matrix for RNA samples
  rna_counts <- round(counts_mat[, samp, drop=FALSE])
  # Create DESeqDataSet
  dds_ct <- DESeqDataSetFromMatrix(
    countData = rna_counts,
    colData   = colData,
    design    = ~ Group
  )
  # Set the offset matrix for plasmid baseline (ignore dimnames to avoid mismatch)
  assays(dds_ct, withDimnames=FALSE)[["offset"]] <- log(matrix(
    dna_baseline, nrow=nrow(dds_ct), ncol=ncol(dds_ct),
    byrow=FALSE))
  # No additional size-factor estimation
  sizeFactors(dds_ct) <- rep(1, ncol(dds_ct))
  # Estimate dispersions and test
  dds_ct <- DESeq(dds_ct, fitType="local", minReplicatesForReplace=Inf)
  res <- results(dds_ct, contrast=c("Group","Group2","Group1"))
  # Gather feature IDs
  feats <- rownames(res)
  # Extract plasmid counts per feature
  plasmid_counts <- counts_mat[feats, plasmid_idx, drop=FALSE]
  # Extract group1 and group2 counts per feature
  grp1_counts     <- counts_mat[feats, grp1,      drop=FALSE]
  grp2_counts     <- counts_mat[feats, grp2,      drop=FALSE]
  # Compute means
  dna_mean  <- rowMeans(plasmid_counts, na.rm=TRUE)
  grp1_mean <- rowMeans(grp1_counts,   na.rm=TRUE)
  grp2_mean <- rowMeans(grp2_counts,   na.rm=TRUE)

  # Build core output table (no per-replicate activity)
  core_out <- data.frame(
    ID             = feats,
    dna_mean       = dna_mean,
    grp1_mean      = grp1_mean,
    grp2_mean      = grp2_mean,
    log2FoldChange = res$log2FoldChange,
    pvalue         = res$pvalue,
    padj           = res$padj,
    stringsAsFactors = FALSE,
    check.names    = FALSE
  )
  # Write core results
  write.table(core_out,
              file = file.path(out_dir, paste0("comparison_", comp_name, ".tsv")),
              sep = "\t", quote = FALSE, row.names = FALSE)
  message("Wrote ", file.path(out_dir, paste0("comparison_", comp_name, ".tsv")))

  # Now add per-replicate activity columns and write extended file
  ext_out <- core_out
  for (s in grp1) {
    ext_out[[paste0(s, "_activity")]] <- log2(grp1_counts[, s] / dna_mean)
  }
  for (s in grp2) {
    ext_out[[paste0(s, "_activity")]] <- log2(grp2_counts[, s] / dna_mean)
  }
  write.table(ext_out,
              file = file.path(out_dir, paste0("comparison_", comp_name, "_with_replicate_activity.tsv")),
              sep = "\t", quote = FALSE, row.names = FALSE)
  message("Wrote ", file.path(out_dir, paste0("comparison_", comp_name, "_with_replicate_activity.tsv")))
}
