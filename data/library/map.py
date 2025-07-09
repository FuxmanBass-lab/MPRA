#!/usr/bin/env python3
import gzip
import csv
from Bio import SeqIO
import sys

# 1) Define which project names map to which output FASTA files
pos_projects = {'ctrl_pos'}
neg_projects = {'ctrl_neg', 'ctrl_ORF', 'ctrl_shuffle'}
ol49_projects = {'viral_NCE', 'exp'}  # Include 'exp' here explicitly

# 2) Read the TSV map file into a dictionary: ID → project
id_to_proj = {}
try:
    with open('tile_proj_map.tsv', newline='') as tsv:
        reader = csv.DictReader(tsv, delimiter='\t')
        for row in reader:
            id_to_proj[row['ID']] = row['project']
except Exception as e:
    print(f"Error reading TSV map file: {e}", file=sys.stderr)
    sys.exit(1)

# 3) Open the reference FASTA and output FASTA files
try:
    with gzip.open('OL49_reference.fasta.gz', 'rt') as ref_in, \
         gzip.open('posCtrl.fasta.gz', 'wt') as pos_out, \
         gzip.open('negCtrl.fasta.gz', 'wt') as neg_out, \
         gzip.open('exp.fasta.gz', 'wt') as ol49_out:

        for record in SeqIO.parse(ref_in, 'fasta'):
            proj = id_to_proj.get(record.id)

            # If not found in map, default to exp
            if proj is None:
                proj = 'exp'

            if proj in pos_projects:
                SeqIO.write(record, pos_out, 'fasta')
            elif proj in neg_projects:
                SeqIO.write(record, neg_out, 'fasta')
            elif proj in ol49_projects:
                SeqIO.write(record, ol49_out, 'fasta')
            else:
                # Optional: Print warning for truly unexpected projects
                print(f"Warning: Project '{proj}' for ID '{record.id}' not assigned to any group!", file=sys.stderr)

    print("FASTA splitting complete!")
except Exception as e:
    print(f"Error during FASTA splitting: {e}", file=sys.stderr)
    sys.exit(1)