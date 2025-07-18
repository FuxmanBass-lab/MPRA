#!/usr/bin/env python3
"""
sam2mpra_cs.py

Convert a SAM file into MPRA mapping output, parsing CIGAR and cs-tags.

Usage:
    sam2mpra_cs.py [-C] [-B] <input.sam> <output_prefix>

Options:
  -C    Use updated CIGAR scoring in score_all (include CIGAR substitutions)
  -B    Only include forward‐strand reads (bitflag 0x10 must be unset)
"""
import argparse
import sys
import re
from pathlib import Path

# Translation table for reverse-complement
_RC_TABLE = str.maketrans('ACGTNacgtn', 'TGCANtgcan')

def reverse_complement(seq: str) -> str:
    return seq.translate(_RC_TABLE)[::-1]

def parse_cigar(cigar: str):
    """Return (match, mismatch, cigar_substitutions, aligned_length)."""
    match = mismatch = cigar_sub = aln_len = 0
    for part in re.findall(r'(\d+[MIDSH=X])', cigar):
        num = int(part[:-1])
        op = part[-1]
        if op in ('M', '='):
            match += num
            aln_len += num
        elif op == 'I':
            mismatch += num
        elif op == 'D':
            mismatch += num
            aln_len += num
        elif op in ('S', 'H'):
            mismatch += num
        elif op == 'X':
            cigar_sub += num
            aln_len += num
        else:
            raise ValueError(f"Unexpected CIGAR op: {part}")
    return match, mismatch, cigar_sub, aln_len

def parse_cs(cs: str):
    """Return (mismatch_from_cs, indel_from_cs)."""
    mismatch_cs = indel_cs = 0
    orig = cs
    while cs:
        if m := re.match(r'^:(\d+)', cs):
            cs = cs[m.end():]
        elif m := re.match(r'^([\+\-])([A-Za-z]+)', cs):
            indel_cs += len(m.group(2))
            cs = cs[m.end():]
        elif m := re.match(r'^\*([A-Za-z]+)', cs):
            mismatch_cs += len(m.group(1)) / 2
            cs = cs[m.end():]
        elif cs == '*':
            cs = ''
        else:
            raise ValueError(f"Unexpected cs element: {orig}")
    return mismatch_cs, indel_cs

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-C', action='store_true', dest='cigar_flag',
                        help='Include CIGAR substitutions in score_all')
    parser.add_argument('-B', action='store_true', dest='bit_flag',
                        help='Filter to forward-strand only (bit 0x10 unset)')
    parser.add_argument('-O', '--oligo_alnmismatchrate_cutoff', type=float, default=0.05,
                        help='Maximum allowed oligo alignment mismatch rate (default: 0.05)')
    parser.add_argument('sam', help='Input SAM file path')
    parser.add_argument('out', help='Output prefix (will write to this file)')
    args = parser.parse_args()

    infile = Path(args.sam)
    outfile = Path(args.out)

    score_cutoff = args.oligo_alnmismatchrate_cutoff
    chr_size = {}

    with infile.open() as fin, outfile.open('w') as fout:
        for line in fin:
            line = line.rstrip('\r\n')
            if line.startswith('@SQ'):
                # header line: @SQ SN:chr LN:length
                fields = line.split('\t')
                sn = next((f.split(':',1)[1] for f in fields if f.startswith('SN:')), None)
                ln = next((f.split(':',1)[1] for f in fields if f.startswith('LN:')), None)
                if sn and ln:
                    chr_size[sn] = int(ln)
                continue
            if line.startswith('@'):
                continue  # other header lines

            cols = line.split('\t')
            flag = int(cols[1])
            # filter by bitflag if requested
            if args.bit_flag and (flag & 0x10):
                continue

            qname = cols[0]
            rname = cols[2]
            mapq = cols[4]  # ← **MAPQ field added**
            cigar = cols[5]
            seq = cols[9]
            size = chr_size.get(rname, 0)
            pos0 = int(cols[3]) - 1

            # extract cs:Z: tag
            cs_field = next((f for f in cols if f.startswith('cs:Z:')), 'cs:Z:*')
            cs_val = cs_field.split(':',2)[2]

            # parse CIGAR and cs
            _, mismatch_cigar, cigar_sub, aln_len = parse_cigar(cigar)
            mismatch_cs, _ = parse_cs(cs_val)

            # determine strand and orientation
            bits = format(flag, '012b')
            rev_strand = bits[7] == '1'
            seq_ori = reverse_complement(seq) if rev_strand else seq

            # compute scores
            if size > 0:
                unaln_len = size - aln_len
                score = mismatch_cigar / size
                if args.cigar_flag:
                    score_all = (mismatch_cigar + cigar_sub + unaln_len) / size
                else:
                    score_all = (mismatch_cigar + mismatch_cs + unaln_len) / size
                score_all_str = f"{score_all:.3f}"
                score_str = f"{score:.3f}"
            else:
                score_all_str = score_str = '-'
                unaln_len = None

            aln_info = f"{pos0}:{aln_len}"
            updated_chr = rname
            if rev_strand:
                parts = rname.split('_')
                updated_chr = parts[0] + "_RC_" + "_".join(parts[1:])

            status = "PASS" if (score_all_str != '-' and float(score_all_str) <= score_cutoff) else "FAIL"

            if '#' in qname:
                bc_id, oligo_id = qname.split('#', 1)
            else:
                bc_id, oligo_id = qname, ''

            out_fields = [
                bc_id,
                oligo_id,
                '1' if not rev_strand else '0',
                updated_chr,
                rname,
                mapq,          # ← added!
                str(size),
                cigar,
                score_all_str,
                seq_ori,
                status,
                score_str,
                cs_val,
                aln_info
            ]
            fout.write("\t".join(out_fields) + "\n")

if __name__ == '__main__':
    main()
