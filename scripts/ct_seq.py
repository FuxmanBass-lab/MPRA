#!/usr/bin/env python3
import argparse
from collections import defaultdict

def process_group(cur_hits, cur_pass_flag, cur_hits_score, cur_cigar, cur_mdtag, cur_pos, ct_pass_flag, last_barcode):
    # Prepare outputs for one barcode group
    keys = list(cur_hits.keys())
    values = [cur_hits[k] for k in keys]
    total = sum(values)
    # Determine pass flag: collision if >1 target
    group_flag = 1 if len(keys) > 1 else ct_pass_flag
    # For each key, pick best index by lowest score
    best_pass = []
    best_score = []
    best_cigar = []
    best_md = []
    best_pos = []
    for k in keys:
        scores = cur_hits_score[k]
        idxs = sorted(range(len(scores)), key=lambda i: scores[i])
        best_i = idxs[0]
        best_pass.append(str(cur_pass_flag[k][best_i]))
        best_score.append(f"{cur_hits_score[k][best_i]:.3f}")
        best_cigar.append(cur_cigar[k][best_i])
        best_md.append(cur_mdtag[k][best_i])
        best_pos.append(cur_pos[k][best_i])
    # Build line
    out_fields = [
        last_barcode,
        ",".join(keys),
        ",".join(str(v) for v in values),
        str(total),
        str(group_flag),
        ",".join(best_pass),
        ",".join(best_score),
        ",".join(best_cigar),
        ",".join(best_md),
        ",".join(best_pos)
    ]
    print("	".join(out_fields))


def main():
    parser = argparse.ArgumentParser(description="Python version of Ct_seq.pl")
    parser.add_argument("input", help="Mapped input file (sam2mpra output)")
    parser.add_argument("ct_col", type=int, help="1-based column index for barcode")
    parser.add_argument("cmp_col", type=int, help="1-based column index for compare id")
    args = parser.parse_args()

    CT_COL = args.ct_col - 1
    CMP_COL = args.cmp_col - 1

    first = True
    cur_hits = defaultdict(int)
    cur_pass_flag = defaultdict(list)
    cur_hits_score = defaultdict(list)
    cur_cigar = defaultdict(list)
    cur_mdtag = defaultdict(list)
    cur_pos = defaultdict(list)
    ct_pass_flag = 2
    last_barcode = None

    with open(args.input) as fin:
        for line in fin:
            parts = line.rstrip().split("	")
            if first:
                last_parts = parts
                last_barcode = last_parts[CT_COL]
                # Initialize flags for group start
                ct_pass_flag = 0 if last_parts[10] == "PASS" else 2
                first = False
                # Initialize accumulators for first record
                cmp_id = last_parts[CMP_COL]
                cur_hits[cmp_id] += 1
                score = float(last_parts[8]) if last_parts[8] != "-" else 1.0
                cur_hits_score[cmp_id].append(score)
                cmp_flag = 0 if last_parts[10] == "PASS" else 2
                cur_pass_flag[cmp_id].append(cmp_flag)
                cur_cigar[cmp_id].append(last_parts[7])
                cur_mdtag[cmp_id].append(last_parts[12])
                cur_pos[cmp_id].append(last_parts[13])
                continue

            barcode = parts[CT_COL]
            # Same group?
            if barcode == last_barcode:
                # Update pass flag
                if parts[10] == "PASS": ct_pass_flag = 0
                cmp_id = parts[CMP_COL]
                cur_hits[cmp_id] += 1
                score = float(parts[8]) if parts[8] != "-" else 1.0
                cur_hits_score[cmp_id].append(score)
                cmp_flag = 0 if parts[10] == "PASS" else 2
                cur_pass_flag[cmp_id].append(cmp_flag)
                cur_cigar[cmp_id].append(parts[7])
                cur_mdtag[cmp_id].append(parts[12])
                cur_pos[cmp_id].append(parts[13])
            else:
                # Flush previous group
                process_group(cur_hits, cur_pass_flag, cur_hits_score,
                              cur_cigar, cur_mdtag, cur_pos,
                              ct_pass_flag, last_barcode)
                # Reset for new group
                cur_hits.clear()
                cur_pass_flag.clear()
                cur_hits_score.clear()
                cur_cigar.clear()
                cur_mdtag.clear()
                cur_pos.clear()
                last_barcode = barcode
                # Initialize new group
                ct_pass_flag = 0 if parts[10] == "PASS" else 2
                cmp_id = parts[CMP_COL]
                cur_hits[cmp_id] = 1
                score = float(parts[8]) if parts[8] != "-" else 1.0
                cur_hits_score[cmp_id] = [score]
                cmp_flag = 0 if parts[10] == "PASS" else 2
                cur_pass_flag[cmp_id] = [cmp_flag]
                cur_cigar[cmp_id] = [parts[7]]
                cur_mdtag[cmp_id] = [parts[12]]
                cur_pos[cmp_id] = [parts[13]]

        # End of file: flush last group
        if not first:
            process_group(cur_hits, cur_pass_flag, cur_hits_score,
                          cur_cigar, cur_mdtag, cur_pos,
                          ct_pass_flag, last_barcode)

if __name__ == '__main__':
    main()
