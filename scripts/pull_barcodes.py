#!/usr/bin/env python3
"""
pull_barcodes.py

Extract barcodes and oligo sequences from flashed FASTQ output.

Usage:
    pull_barcodes.py <fastq> <read_orientation> <out_prefix> <link_A_bc> \
<link_A_oligo> <end_A_oligo> <min_seq_size> <min_enh_size> \
<max_enh_size> <bc_len> <link_A_size> <link_end_size>

Writes:
    <out_prefix>.match   -- matched barcodes and oligos
    <out_prefix>.reject  -- rejected reads with reasons
"""
import argparse
import re

# translation for reverse complement
_RC_TABLE = str.maketrans('ACGTNacgtn', 'TGCANtgcan')

def reverse_complement(seq: str) -> str:
    return seq.translate(_RC_TABLE)[::-1]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('fastq', help='Flashed FASTQ file')
    p.add_argument('read_orientation', type=int, help='1 if R1 is reverse complement')
    p.add_argument('out_prefix', help='Prefix for output files')
    p.add_argument('link_A_bc', help='Barcode-oligo linker sequence')
    p.add_argument('link_A_oligo', help='Oligo linker sequence')
    p.add_argument('end_A_oligo', help='End oligo linker sequence')
    p.add_argument('min_seq_size', type=int, help='Minimum sequence length to keep')
    p.add_argument('min_enh_size', type=int, help='Minimum enhancer length')
    p.add_argument('max_enh_size', type=int, help='Maximum enhancer length')
    p.add_argument('bc_len', type=int, help='Barcode length')
    p.add_argument('link_A_size', type=int, help='Adapter length before enhancer')
    p.add_argument('link_end_size', type=int, help='Adapter length after enhancer')
    args = p.parse_args()

    # compute adjustments
    link_A_adj = args.link_A_size - 8
    link_end_adj = args.link_end_size - 18
    if link_end_adj < 0:
        link_end_adj = args.link_end_size + 2

    match_out = open(f"{args.out_prefix}.match", 'w')
    reject_out = open(f"{args.out_prefix}.reject", 'w')

    with open(args.fastq) as fq:
        while True:
            # read four lines of FASTQ
            id_line = fq.readline()
            if not id_line:
                break
            seq_line = fq.readline()
            plus_line = fq.readline()
            qual_line = fq.readline()
            if not qual_line:
                break

            rid = id_line.strip().lstrip('@')
            if rid.endswith('/1'):
                rid = rid[:-2]

            r1 = seq_line.strip()
            if len(r1) < args.min_seq_size:
                continue

            if args.read_orientation == 1:
                r1 = reverse_complement(r1)

            # find linker near barcode end
            seg = r1[args.bc_len-2 : args.bc_len-2 + 10]
            idx = seg.find(args.link_A_bc)
            if idx == -1:
                reject_out.write(f"{rid}\tLinker Sequence Not Found\n")
                continue
            link_index = idx + (args.bc_len - 2)

            # extract barcode
            if link_index - args.bc_len <= 0:
                barcode_seq = r1[:args.bc_len]
            else:
                start_bc = link_index - args.bc_len
                barcode_seq = r1[start_bc : start_bc + args.bc_len]

            # find oligo start
            sub = r1[link_index + link_A_adj : link_index + link_A_adj + 12]
            oligo_start = sub.find(args.link_A_oligo)
            if oligo_start == -1:
                m = re.search(r'A[ACTG][ACTG]G', sub)
                oligo_start = m.start() if m else 0
            oligo_start += link_A_adj + 4 + link_index

            # find oligo end
            end_sub = r1[-link_end_adj:] if link_end_adj > 0 else ''
            oligo_end = end_sub.find(args.end_A_oligo)
            if oligo_end == -1:
                oligo_end = 2
            oligo_end -= link_end_adj

            oligo_length = len(r1) + oligo_end - oligo_start
            oligo_seq = r1[oligo_start : oligo_start + oligo_length]
            oligo_seq = reverse_complement(oligo_seq)

            if args.min_enh_size <= oligo_length <= args.max_enh_size:
                match_out.write(f"{rid}\t{barcode_seq}\t{oligo_seq}\t{oligo_length}\t{len(r1)}\n")
            else:
                reject_out.write(f"{rid}\tOligo Outside Length Bounds\t{barcode_seq}\t{oligo_length}\n")

    match_out.close()
    reject_out.close()

if __name__ == '__main__':
    main()
