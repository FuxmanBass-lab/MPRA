# MPRA Pipeline
A modular, reproducible pipeline for Massively Parallel Reporter Assays (MPRA), from raw sequencing reads through count summarization, statistical modeling, and per-condition comparisons. This README provides setup instructions, configuration details, and step-by-step usage examples.

## Table of Contents
1.	Project Overview
2.	Prerequisites
3.	Repository Layout
4.	Download and Setup
5.	Pipeline Wrapper (pipeline.sh)
6.	Step-by-Step Commands
  	1. Matching Oligos to Barcodes (run_match.sh)
  	2. Counting Barcodes (run_count.sh)
  	3. Modeling Activity (run_model.sh)
  	4. Condition Comparisons (run_compare.sh)
7.	Input/Output File Descriptions
8.	Troubleshooting
9.	Collaboration
11.	License & Citation


## Project Overview
This MPRA pipeline processes paired‐end or single‐end FASTQ reads from reporter assays:

1.	Match reads to reference oligo sequences and extract barcodes.
2.	Count barcode occurrences across replicates and conditions.
3.	Model RNA vs. DNA counts to estimate activity (log₂ RNA/DNA) per oligo using DESeq2–based normalization, dispersion estimation, and optional summit shift.
4.	Compare activity between user‐defined groups (e.g., treatment vs. control) with robust statistical testing.

All steps are implemented as modular scripts, orchestrated by a job‐submission wrapper for HPC clusters (SGE).

## Prerequisites
	•	Linux or macOS
	•	Conda (Miniconda or Anaconda)
	•	SGE or compatible job scheduler (optional; pipeline can run locally if desired).

## Repository Layout

```
MPRA/
├── config/                                  # all user‐provided configuration
│   ├── acc_id.txt                           # sample fastq ↔ replicate ID mappings
│   ├── comparisons.tsv                      # which groups to compare (Comparison, Group1, Group2)
│   └── settings.sh                          # MUST EDIT: PROJECT_NAME, PROJECT_SUFFIX,
│                                              CONDA_INIT, SCC_PROJ
├── data/
│   ├── library/                             # place your cloned‐library FASTA & controls here
│   └── samples/                             # place your raw plasmid/RNA FASTQs here
│
├── logs/                                    # auto‐generated qsub stdout/err files
│
├── results/                                 # pipeline outputs by step
│   ├── 01_match/                            # reconstructed oligo-barcode mapping
│   ├── 02_count/                            # per-replicate count tables & QC
│   ├── 03_model/                            # DESeq2 results, normalized counts, plots
│   └──04_compare/                          # pairwise comparison TSVs & summaries
│
├── scripts/                                 # utility Python scripts (don’t edit)
│   ├── associate_tags.py
│   ├── bc_raw.py
│   ├── compile_bc_cs.py
│   ├── count_qc.py
│   ├── ct_seq.py
│   ├── make_attributes_oligo.py
│   ├── make_counts.py
│   ├── make_infile.py
│   ├── make_project_list.py
│   ├── map_project_annot_fastq.py
│   ├── mapping_qc_plots.py
│   ├── parse_map.py
│   ├── pull_barcodes.py
│   ├── read_stats.py
│   └── sam2mpra_cs.py
│
├── src/                                     # entrypoints for each pipeline step
│   ├── 01_MPRA_match/
│   │   ├── match.py                         # core matching logic
│   │   └── run_match.sh                     # wrapper script
│   ├── 02_MPRA_count/
│   │   ├── count.py                         # count aggregation logic
│   │   └── run_count.sh		     # wrapper script
│   ├── 03_MPRA_model/
│   │   ├── model.r                          # R script doing DESeq2 modeling
│   │   └── run_model.sh		     # wrapper script
│   └── 04_MPRA_compare/
│       ├── compare.r                        # R script for group1 vs group2 tests
│       └── run_compare.sh		     # wrapper script
│
├── .gitignore                               # ignore logs, results, etc.
├── env.yml                                  # conda environment spec (run `setup.sh`)
├── pipeline.sh                              # submits each step via qsub (calls run_*.sh)
├── README.md                                # ← you’re here: this overview and instructions
└── setup.sh                                 # checks conda, prompts for your 4 settings,
                                              creates env, makes sure scripts are executable
```
