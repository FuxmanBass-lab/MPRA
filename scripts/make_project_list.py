#!/usr/bin/env python3
"""
make_project_list.py

Create a project list file from a FASTA reference, with correct colon formatting.

Arguments:
  - oligo_seqs: reference FASTA used in MPRAMatch pipeline
  - project_name: project prefix (used in output filename)

The FASTA should be grouped by "project" (e.g., controls, experimental).
Any oligos belonging to more than one project should be processed separately
and projects separated by commas.

Outputs a tab-separated .proj_list file with:
  oligo_id (with colons filled) <tab> project_name
"""

import sys
import gzip

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 make_project_list.py <oligo_seqs.fasta(.gz)> <project_name>", file=sys.stderr)
        sys.exit(1)

    oligo_seqs = sys.argv[1]
    project_name = sys.argv[2]
    output_file = f"{project_name}.proj_list"

    try:
        if oligo_seqs.endswith('.gz'):
            fasta = gzip.open(oligo_seqs, 'rt')
        else:
            fasta = open(oligo_seqs, 'r')
    except Exception as e:
        print(f"ERROR: cannot open file ({oligo_seqs}): {e}", file=sys.stderr)
        sys.exit(1)

    try:
        with fasta, open(output_file, 'w') as out:
            for line in fasta:
                if line.startswith('>'):
                    header = line.strip().split()
                    array = header[0].split('|')
                    id_str = array[0]
                    id_str = id_str.lstrip('>@')
                    # Remove only the exact trailing '/1' (not all '1' or '/' chars)
                    if id_str.endswith('/1'):
                        id_str = id_str[:-2]

                    # Add missing colons if fewer than 3
                    n_colons = id_str.count(':')
                    if n_colons < 3:
                        id_str += (":NA" * (3 - n_colons))

                    out.write(f"{id_str}\t{project_name}\n")
    except Exception as e:
        print(f"ERROR during writing: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
