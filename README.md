# MPRA Pipeline
A modular, reproducible pipeline for Massively Parallel Reporter Assays (MPRA), from raw sequencing reads through count summarization, statistical modeling, and per-condition comparisons. This README provides setup instructions, configuration details, and step-by-step usage examples.

## Table of Contents
1.	Project Overview
2.	Prerequisites
3.	Repository Layout
4.	Download and Setup
5.	Usage: Pipeline Wrapper (pipeline.sh)
6.	Usage: Step-by-Step Commands
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
│   └── 04_compare/                          # pairwise comparison TSVs & summaries
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


## Download and Setup

**1.	Clone the repository**

```bash
git clone https://github.com/FuxmanBass-lab/MPRA.git
cd MPRA
```

**3.	Install Conda environment**

Make sure you have Conda (Miniconda or Anaconda) installed and on your $PATH.
```bash
./setup.sh
```
What setup.sh does:
* Prompts you to confirm (or supply) the following in config/settings.sh:
	* 	PROJECT_NAME: your MPRA project identifier (e.g. OL49)
	* 	ROJECT_SUFFIX: run‐specific tag (e.g. date or batch)
	* 	CONDA_INIT: path to your conda.sh (e.g. ~/miniconda3/etc/profile.d/conda.sh)
	* 	CC_PROJ: your SCC/cluster project name for qsub (e.g. vcres)
* Auto‐detects and sets $BASE_DIR for you.
* Verifies conda is available.
* Creates the Conda environment from env.yml if it doesn’t already exist.
* Checks that all wrapper scripts (run_match.sh, etc.) and pipeline.sh are executable.


**5.	Review and customize**

	Open config/settings.sh in your editor and ensure the four variables above are correctly set for your system. Do not modify other lines unless necessary.


**7.	Verify the layout**

Ensure you have placed:

* **Library FASTA and FASTQ(s)** in data/library/
* **Sample FASTQ(s)** in data/samples/
* **acc_id.txt** and **comparisons.tsv** in config/


**9.	You are ready to run**

	Proceed to Usage to start the pipeline steps.



## Usage: Pipeline Wrapper

Once your config/settings.sh is configured, you can launch one or all steps via the high-level wrapper. This will submit each step as a job to the cluster (qsub):

```bash
# Run only the matching step:
./pipeline.sh match

# Run only the counting step:
./pipeline.sh count

# Run only the modeling step:
./pipeline.sh model

# Run only the comparison step:
./pipeline.sh compare

# Run all steps in sequence:
./pipeline.sh all

```

This submits one or more jobs to your SCC cluster with names MPRAmatch, MPRAcount, MPRAmodel, MPRAcompare, or MPRAall.
Each job sources your Conda environment and invokes the corresponding run_*.sh script under src/. You can monitor each job’s progress by inspecting the log files in the top-level logs/ directory.


## Usage: Step-by-Step Commands

If you prefer to run each stage manually (or debug a single step), here are the direct commands and their required inputs:

### 1.	Matching Oligos to Barcodes

```bash
cd src/01_MPRA_match
./run_match.sh
```
**Inputs:**
* READ1, READ2 FASTQ files
* Reference oligo fasta
  
**Output:**
* Merged .match files, barcode–oligo pairs
* QC plots

### 2.	Counting Barcodes

```bash
cd ../02_MPRA_count
./run_count.sh
```

**Inputs:**

* acc_id.txt (sample ↔ replicate ↔ cell-type ↔ RNA map)
* Parsed .parsed file from match step
* Raw FASTQ replicates

**Output:**

* Per-replicate .count tables
* condition table


### 3.	Modeling Activity
```
cd ../03_MPRA_model
./run_model.sh
```
**Inputs:**

* Barcode count table (.count)
* Attributes and condition files
* Negative/positive control and experimental tiles/oligos FASTAs

**Output:**
* Global and Per cell-type Normalized counts (*_normalized_counts.tsv)
* Per cell-type activity (*_activity.tsv)
* DESeq2 results, bed files, session info
* QC and visualizations

### 4.	Condition Comparisons

```bash
cd ../04_MPRA_compare
./run_compare.sh
```

**Inputs:**

* Comparison design (config/comparisons.tsv)
* Normalized counts TSV

**Output:**

* comparison_<name>.tsv (log₂FC, p-values)
* comparison_<name>_with_replicate_activity.tsv


