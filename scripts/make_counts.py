#!/usr/bin/env python3
"""
make_counts.py

Extract barcode sequences from an MPRA FASTQ file.

Usage:
    make_counts.py <fastq> <out_id> <read_number> <bc_len>

Outputs:
    <out_id>.match         — Tab-delimited file of record_id and barcode
    <out_id>.reject.fastq  — FASTQ of reads whose barcodes were rejected (currently unused)
    <out_id>.reject.bc     — Tab-delimited file of record_id and rejected barcode (currently unused)
"""
import sys
import os
import gzip
from pathlib import Path
from Bio import SeqIO

def open_by_suffix(filename):
    if filename.endswith('.gz'):
        return gzip.open(filename, 'rt')
    else:
        return open(filename, 'r')

def main():
    fastqfile = sys.argv[1]
    out_id = sys.argv[2]
    read_number = int(sys.argv[3])
    bc_len = int(sys.argv[4])

    current_path = os.getcwd()

    match_path = Path(current_path) / f"{out_id}.match"
    reject_fastq_path = Path(current_path) / f"{out_id}.reject.fastq"
    reject_bc_path = Path(current_path) / f"{out_id}.reject.bc"

    with match_path.open('w') as match_oligo, \
         reject_fastq_path.open('w') as reject_fastq, \
         reject_bc_path.open('w') as reject_bc, \
         open_by_suffix(fastqfile) as handle:

        print("Reading Records...")
        for record in SeqIO.parse(handle, "fastq"):
            seq_only = record.seq
            if read_number != 2:
                seq_only = seq_only.reverse_complement()
            seq_only = str(seq_only)

            if read_number == 2:
                bc_seq = seq_only[0:bc_len]
            else:
                bc_seq = seq_only[-bc_len:]

            # Placeholder for dictionary check
            # if bc_seq in BC_dict:
            match_oligo.write(f"{record.name}\t{bc_seq}\n")
            # else:
            #     SeqIO.write(record, reject_fastq, "fastq")
            #     reject_bc.write(f"{record.name}\t{bc_seq}\n")

if __name__ == "__main__":
    main()