#!/usr/bin/env python3
"""
make_infile.py

Given comma-separated lists of sample IDs and tag files, produce a two-column samples file.

Usage:
    make_infile.py <tag_ids_comma> <tag_files_comma> <out_id>

Outputs:
    <out_id>_samples.txt — Tab-delimited file with sample_id and corresponding tag file path
"""
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tag_ids', help='Comma-separated list of sample IDs')
    parser.add_argument('tag_files', help='Comma-separated list of tag file paths')
    parser.add_argument('out_id', help='Output prefix')
    args = parser.parse_args()

    ids = args.tag_ids.split(',')
    files = args.tag_files.split(',')
    if len(ids) != len(files):
        raise ValueError(f"Number of IDs ({len(ids)}) != number of files ({len(files)})")

    out_path = Path(f"{args.out_id}_samples.txt")
    with out_path.open('w') as fh:
        for sample_id, tag_file in zip(ids, files):
            fh.write(f"{sample_id}\t{tag_file}\n")

if __name__ == "__main__":
    main()
