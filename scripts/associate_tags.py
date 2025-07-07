#!/usr/bin/env python3
"""
associate_tags.py

Python port of associate_tags.pl:
  - reads matched tag file and parsed mapping file
  - merges counts and mapping info
  - writes a combined tag summary
"""
import argparse
import gzip
import sys

def open_maybe_gz(path):
    if path.endswith(('.gz', '.gzip')):
        return gzip.open(path, 'rt')
    else:
        return open(path, 'r')


def main():
    p = argparse.ArgumentParser(description="Associate matched tags with parsed oligos")
    p.add_argument('matched', help='Matched tag file (.match)')
    p.add_argument('parsed', help='Parsed mapping file from MPRAmatch')
    p.add_argument('out', help='Output tag association file')
    p.add_argument('orientation', nargs='?', default=None,
                   help='Barcode orientation (unused)')
    args = p.parse_args()

    # Step 1: load matched tags
    # Each line: columns split by tab; key is column 1
    tags = {}
    with open(args.matched) as mf:
        for line in mf:
            parts = line.rstrip('\n').split('\t')
            if len(parts) < 2:
                continue
            tag = parts[1]
            # Initialize or increment count
            entry = tags.setdefault(tag, {
                'count': 0,
                'orient': -9,
                'loc': '-',
                'flag': '-',
                'tag': tag,
                'score': 'NA',
                'cigar': 'NA',
                'md': 'NA',
                'pos': 'NA'
            })
            entry['count'] += 1

    # Step 2: overlay parsed mapping info
    with open_maybe_gz(args.parsed) as pf:
        for raw in pf:
            parts = raw.rstrip('\n').split('\t')
            if len(parts) < 10:
                continue
            cur_tag = parts[0]
            cur_loc = parts[1]
            try:
                cur_flag = int(parts[4])
            except ValueError:
                cur_flag = 0
            cur_m_flag = parts[5]
            cur_m_aln  = parts[6]
            cur_m_cigar= parts[7]
            cur_m_md   = parts[8]
            cur_m_pos  = parts[9]

            if cur_tag not in tags:
                continue
            entry = tags[cur_tag]
            # Map flags
            if cur_flag > 0:
                if cur_flag == 1:
                    # simple multimapping: choose primary
                    entry['orient'] = -4
                    entry['loc']    = cur_loc
                    entry['flag']   = str(cur_flag)
                    entry['score']  = cur_m_aln
                    entry['cigar']  = cur_m_cigar
                    entry['md']     = cur_m_md
                    entry['pos']    = cur_m_pos
                elif cur_flag == 2:
                    entry['orient'] = -5
                    entry['loc']    = cur_loc
                    entry['flag']   = str(cur_flag)
                    entry['score']  = cur_m_aln
                    entry['cigar']  = cur_m_cigar
                    entry['md']     = cur_m_md
                    entry['pos']    = cur_m_pos
                else:
                    entry['orient'] = -6
                    entry['loc']    = cur_loc
                    entry['flag']   = str(cur_flag)
                    entry['score']  = cur_m_aln
                    entry['cigar']  = cur_m_cigar
                    entry['md']     = cur_m_md
                    entry['pos']    = cur_m_pos
            else:
                # cur_flag <= 0
                entry['orient'] = 0
                entry['loc']    = cur_loc
                entry['flag']   = str(cur_flag)
                entry['score']  = cur_m_aln
                entry['cigar']  = cur_m_cigar
                entry['md']     = cur_m_md
                entry['pos']    = cur_m_pos

    # Step 3: write out
    with open(args.out, 'w') as out:
        for tag, e in tags.items():
            out.write('\t'.join([
                tag,
                str(e['count']),
                str(e['orient']),
                e['loc'],
                e['flag'],
                e['tag'],
                e['score'],
                e['cigar'],
                e['md'],
                e['pos']
            ]) + '\n')

if __name__ == '__main__':
    main()
