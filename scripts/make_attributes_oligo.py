#!/usr/bin/env python3
"""
make_attributes_oligo.py

Create an attributes file based on a project file containing the oligo ID and the project(s) to which it belongs.
Oligo example ID: chr:pos:ref:alt:allele:window(:haplotype)

Output columns:
  ID, SNP, chr, pos, ref_allele, alt_allele, allele, window, strand, project, haplotype
"""

import sys

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 make_attributes_oligo.py <oligo_project_file> <project_name>", file=sys.stderr)
        sys.exit(1)

    oligo_project = sys.argv[1]
    out_prefix = sys.argv[2]
    out_file = f"{out_prefix}.attributes"

    oligo_proj = {}

    try:
        with open(oligo_project, 'r') as proj_f:
            for line in proj_f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('\t')
                oligo_proj[parts[0]] = parts[1]
    except Exception as e:
        print(f"ERROR: cannot read file ({oligo_project}): {e}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(out_file, 'w') as out:
            header = ["ID", "SNP", "chr", "pos", "ref_allele", "alt_allele",
                      "allele", "window", "strand", "project", "haplotype"]
            out.write("\t".join(header) + "\n")

            for oligo, project in oligo_proj.items():
                attributes = oligo.split(':')
                length = len(attributes)

                if length < 4:
                    print(f"Need at least 4 attributes in ID. Only {length} found in {oligo}", file=sys.stderr)
                    sys.exit(1)

                chr_ = attributes[0]
                snp_pos = attributes[1]
                ref_allele = attributes[2]
                alt_allele = attributes[3]

                allele = "NA"
                if length >= 5:
                    allele = attributes[4]
                    if allele == "R":
                        allele = "ref"
                    elif allele == "A":
                        allele = "alt"
                if allele not in ("ref", "alt"):
                    print(f"Allele should be R or A, set as '{allele}' in {oligo}", file=sys.stderr)

                window = "NA"
                if length >= 6:
                    window = attributes[5]
                    if window == "wL":
                        window = "left"
                    elif window == "wC":
                        window = "center"
                    elif window == "wR":
                        window = "right"
                if window not in ("left", "center", "right", "NA"):
                    print(f"Window should be wL, wC or wR, set as '{window}' in {oligo}", file=sys.stderr)

                snp = f"{chr_}:{snp_pos}:{ref_allele}:{alt_allele}"
                strand = "fwd"
                haplotype = "ref"

                # Additional attributes check (haplotype)
                if length > 5:
                    for attr in attributes[5:]:
                        if attr.startswith("Alt"):
                            haplotype = "alt"

                out.write("\t".join([oligo, snp, chr_, snp_pos, ref_allele,
                                     alt_allele, allele, window, strand,
                                     project, haplotype]) + "\n")
    except Exception as e:
        print(f"ERROR: cannot write to file ({out_file}): {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()