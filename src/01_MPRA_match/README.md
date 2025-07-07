# MPRAmatch Step — MPRA Barcode–Oligo Matching Pipeline

### Overview

The MPRAmatch step matches experimental barcodes to their corresponding oligo sequences. This produces a high-confidence barcode–oligo dictionary that will be used to quantify barcode counts across replicates in the next stages of the MPRA pipeline.

This step takes raw paired-end FASTQ files from your MPRA library and a reference oligo FASTA, and outputs a parsed mapping of barcodes to oligos along with detailed QC metrics.

⸻

### Key Steps

1️⃣ Merge paired-end reads
	•	Merges R1 and R2 reads into single “pseudo-reads” using FLASH.
	•	Ensures barcode and oligo sequences appear in one contiguous read.

2️⃣ Extract barcodes and oligos
	•	Uses known linker sequences to extract the barcode and corresponding oligo fragment from each merged read.

3️⃣ Convert to FASTA and prepare for alignment
	•	Rearranges matched reads into FASTA format for alignment.

4️⃣ Align to oligo reference
	•	Aligns extracted oligo sequences to the reference FASTA using minimap2.
	•	Filters ambiguous or low-confidence matches.

5️⃣ Generate barcode–oligo association file
	•	Summarizes each barcode’s best mapped oligo from the alignment.

6️⃣ Sort and count
	•	Sorts associations by barcode.
	•	Counts the number of times each barcode–oligo pair is seen.

7️⃣ Parse and filter
	•	Resolves barcodes mapping to multiple oligos (ambiguities).
	•	Optionally handles saturation mutagenesis attributes.

8️⃣ Library complexity prediction
	•	Uses preseq to estimate expected barcode diversity at higher sequencing depths.

9️⃣ Generate QC plots
	•	Produces a PDF summarizing barcode distributions and mapping quality.

🔟 Organize outputs
	•	Moves all key intermediate and final outputs into your output directory.

⸻

### key Outputs

File Extension	Description
*.parsed	Final parsed barcode–oligo dictionary
*.plothist	Barcode count histogram
*.hist	Preseq input histogram
*.hist.preseq	Preseq predicted library complexity
*.pdf	QC plots summarizing barcode metrics
*.sam, *.bam	Alignment files
*.match, *.reject	Raw barcode–oligo matches and rejects


⸻

### Detailed Intermediate Files

.merged.match

Columns:
	1.	Sequence ID
	2.	Found barcode sequence
	3.	Found oligo sequence
	4.	Found oligo length
	5.	Flashed sequence length


.merged.match.enh.mapped

Columns:
	1.	Sequence ID
	2.	Barcode
	3.	Mapping flag from minimap2
	4.	Best mapped oligo ID
	5.	All mapped IDs (comma-separated if multiple)
	6.	Count
	7.	Mapped length
	8.	CIGAR string
	9.	Adjusted error score: (mismatched bp + inserted bp + deleted bp + non-aligned length) / total oligo length
	10.	Oligo sequence
	11.	PASS/FAIL flag (PASS if adjusted score ≤ 0.05)
	12.	Raw error
	13.	MD/cs tag
	14.	Start/stop coordinates in reference oligo


.merged.match.enh.mapped.barcode.ct

Columns:
	1.	Barcode
	2.	Oligo(s) (comma-separated if multiple)
	3.	Individual seen (comma-separated per oligo)
	4.	Total seen
	5.	Overall flag:
	•	0: Pass (single oligo, no conflict)
	•	1: Conflict (multiple oligos)
	•	2: Fail (no oligo or failed mapping)
	6.	Individual flags (comma-separated per oligo)
	7.	Error (best for barcode–oligo pair)
	8.	CIGAR (best pair)
	9.	MD/cs tag (best pair)
	10.	Start/stop coordinates in reference oligo (best pair)

.merged.match.enh.mapped.barcode.ct.parsed
	•	Same columns as .merged.match.enh.mapped.barcode.ct.
	•	Barcodes flagged as “conflict” (flag = 1) are examined for dominant assignments and rescued if possible.


⸻
### Summary
This step builds a reliable barcode–oligo map and sets the foundation for robust quantification and modeling of MPRA activity.