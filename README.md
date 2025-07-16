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
