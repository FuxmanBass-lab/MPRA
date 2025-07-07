#!/usr/bin/env python3
"""
parse_map.py

Faithful translation of the original Perl script by Ryan Tewhey.
Handles barcode–oligo mapping data, resolves conflicts based on coverage,
and applies saturation mutagenesis logic if enabled.

Usage:
    parse_map.py <mapped_file> [-S] [-A <attributes_file>]

Arguments:
    mapped_file : input TSV file
    -S          : enable saturation mutagenesis mode
    -A file     : attributes file (required if -S)

Output:
    Prints resolved mapping lines to stdout in tab-separated format.
"""

import sys
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Faithful port of Perl parse_map.pl for MPRA barcode resolution")
    parser.add_argument("mapped_file", help="Input mapped file")
    parser.add_argument("-S", "--saturation", action="store_true", help="Enable saturation mutagenesis mode")
    parser.add_argument("-A", "--attributes", type=str, help="Attributes file (required if -S)")
    return parser.parse_args()

def load_attributes(file_path):
    ref_hash = {}
    sat_ref_col = None
    ID_col = None
    with open(file_path) as f:
        header = f.readline().strip().split("\t")
        for i, col in enumerate(header):
            if col == "sat_ref_parent":
                sat_ref_col = i
            if col == "ID":
                ID_col = i
        if sat_ref_col is None or ID_col is None:
            raise ValueError("sat_ref_parent or ID column not found in attributes file")
        for line in f:
            cols = line.strip().split("\t")
            ref_hash[cols[ID_col]] = cols[sat_ref_col]
    print(f"ID Col: {ID_col}\nSat Ref Col: {sat_ref_col}", file=sys.stderr)
    return ref_hash

def split_ID(full_id):
    full_id = full_id.strip("()")
    return full_id.split(";")

def main():
    args = parse_args()

    ref_hash = {}
    if args.saturation:
        if not args.attributes:
            sys.exit("ERROR: Attributes file must be provided when using -S.")
        ref_hash = load_attributes(args.attributes)

    with open(args.mapped_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            cols = line.split("\t")
            ids = cols[1].split(",")
            cov = list(map(int, cols[2].split(",")))
            passes = cols[5].split(",")
            aln = cols[6].split(",")
            cigars = cols[7].split(",")
            mds = cols[8].split(",")
            poss = cols[9].split(",")

            if len(ids) > 1:
                max_cov = max(cov)
                max_idx = cov.index(max_cov)
                keep = 0

                for i in range(len(cov)):
                    if cov[i] == max_cov and i != max_idx:
                        keep = 1
                    elif cov[i] == max_cov and max_idx == i:
                        pass
                    elif args.saturation:
                        frac = cov[i] / max_cov
                        if frac > 0.1 and int(aln[i]) == 0 and int(aln[max_idx]) == 0:
                            keep = 1
                        elif frac > 0:
                            id_arry = split_ID(ids[i])
                            max_id_arry = split_ID(ids[max_idx])
                            for id1 in id_arry:
                                for id2 in max_id_arry:
                                    if id1 != "*" and id2 != "*" and ref_hash.get(id1) == ref_hash.get(id2):
                                        if frac > 0.5:
                                            keep = 1
                                    elif frac > 0.1:
                                        keep = 1
                    elif not args.saturation and cov[i] / max_cov > 0.1:
                        keep = 1

                if keep == 0:
                    out_line = [
                        cols[0],
                        ids[max_idx],
                        str(cov[max_idx]),
                        cols[3],
                        passes[max_idx],
                        passes[max_idx],
                        aln[max_idx],
                        cigars[max_idx],
                        mds[max_idx],
                        poss[max_idx]
                    ]
                    print("\t".join(out_line))
                else:
                    print("\t".join(cols))
            else:
                print("\t".join(cols))

if __name__ == "__main__":
    main()