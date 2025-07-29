#!/usr/bin/env python3
"""
Split a FASTA into separate files, one per project defined in `tile_proj_map.tsv`.
Handles composite record IDs (e.g., "(tile1; tile2; tile3)") by splitting on `;`.
Produces a FASTA for each unique project plus `unassigned.fasta.gz` for any tiles without a mapping.
Also prints a list of expected FASTA filenames.
"""

import gzip
import csv
import sys
from collections import Counter
from Bio import SeqIO
import argparse
import os

parser = argparse.ArgumentParser(
    description="Split a FASTA into per-project files based on a TSV map of tiles to projects"
)
parser.add_argument(
    '-m', '--map',
    dest='map_tsv',
    required=True,
    help='Path to the tile-to-project TSV file'
)
parser.add_argument(
    '-f', '--fasta',
    dest='ref_fasta',
    required=True,
    help='Path to the input reference FASTA (.gz)'
)
parser.add_argument(
    '-o', '--outdir',
    dest='outdir',
    required=True,
    help='Output directory for FASTA files and reports'
)
args = parser.parse_args()

# Ensure output directory exists
os.makedirs(args.outdir, exist_ok=True)

# -- 1) Read the TSV map file into a dictionary: ID -> project
id_to_proj = {}
projects = set()
try:
    with open(args.map_tsv, newline='') as tsv:
        reader = csv.DictReader(tsv, delimiter='\t')
        for row in reader:
            tile = row['ID']
            proj = row['project']
            id_to_proj[tile] = proj
            projects.add(proj)
except Exception as e:
    print(f"Error reading TSV map file: {e}", file=sys.stderr)
    sys.exit(1)

# Track TSV IDs and FASTA-seen IDs
# (for reporting which TSV entries never appear in the FASTA)
tsv_ids = set(id_to_proj.keys())
seen_ids = set()

# -- 2) Prepare output handles
handles = {}
for proj in sorted(projects):
    fname = os.path.join(args.outdir, f"{proj}.fasta.gz")
    handles[proj] = gzip.open(fname, 'wt')
# handle unmapped IDs
handles['unassigned'] = gzip.open(os.path.join(args.outdir, 'unassigned.fasta.gz'), 'wt')

# -- 3) Initialize counters
counts = Counter()
unassigned_ids = []
total_records = 0

# -- 4) Parse the reference FASTA and distribute records
with gzip.open(args.ref_fasta, 'rt') as ref_in:
    for record in SeqIO.parse(ref_in, 'fasta'):
        total_records += 1
        # Preserve full composite header (record.description holds the full header line)
        full_header = record.description
        # Overwrite record identifiers so output FASTA uses the complete composite header
        record.id = full_header
        record.name = full_header
        record.description = full_header

        # Extract individual tile IDs from the composite header
        # e.g. "(tile1; tile2; tile3)" -> ["tile1","tile2","tile3"]
        id_str = full_header.strip('()')
        tile_ids = [tid.strip() for tid in id_str.split(';')]

        # Track which TSV IDs were seen in this FASTA record
        for tid in tile_ids:
            seen_ids.add(tid)

        # Determine unique projects for this record
        matched_projects = {id_to_proj[tid] for tid in tile_ids if tid in id_to_proj}

        if matched_projects:
            for proj in matched_projects:
                SeqIO.write(record, handles[proj], 'fasta')
                counts[proj] += 1
        else:
            SeqIO.write(record, handles['unassigned'], 'fasta')
            counts['unassigned'] += 1
            unassigned_ids.append(full_header)

# -- 5) Close all file handles
for handle in handles.values():
    handle.close()

# -- 6) Print summary and expected FASTA list
print("FASTA splitting complete!")
print(f"Total records processed: {total_records}\n")
print("Records per output:")
for proj, cnt in counts.items():
    print(f"  {proj}: {cnt}")

expected = [f"{proj}.fasta.gz" for proj in sorted(projects)] + ['unassigned.fasta.gz']
print("\nExpected FASTA files:")
for fname in expected:
    print(f"  {fname}")

# Save list of expected project FASTA files (excluding unassigned)
project_files = [f"{proj}.fasta.gz" for proj in sorted(projects)]
expected_list_path = os.path.join(args.outdir, 'expected_fastas.txt')
with open(expected_list_path, 'w') as ef:
    for fname in project_files:
        ef.write(fname + '\n')
print(f"Expected project FASTA filenames saved to {expected_list_path}")

# Report any FASTA records with no mapping (unassigned)
unassigned_count = counts.get('unassigned', 0)
if unassigned_count:
    print(f"Tiles in FASTA without mapping (unassigned): {unassigned_count} (see unassigned.fasta.gz)")
else:
    print("All FASTA records were assigned to a project.")

# Report any TSV IDs that never appeared in the FASTA
missing_tsv_ids = sorted(tsv_ids - seen_ids)
if missing_tsv_ids:
    with open(os.path.join(args.outdir, 'tsv_ids_not_in_fasta.txt'), 'w') as fout:
        for tid in missing_tsv_ids:
            fout.write(tid + '\n')
    print(f"Tiles in TSV not found in FASTA: {len(missing_tsv_ids)} (written to tsv_ids_not_in_fasta.txt)")
else:
    print("All TSV IDs were found in the FASTA.")

# -- 7) Write unassigned IDs if any
if unassigned_ids:
    with open(os.path.join(args.outdir, 'unassigned_ids.txt'), 'w') as fout:
        for uid in unassigned_ids:
            fout.write(uid + '\n')
    print("Written unassigned IDs to unassigned_ids.txt")
