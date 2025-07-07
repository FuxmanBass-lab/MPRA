#!/usr/bin/env python3
import argparse
import sys
import logging
from collections import defaultdict, OrderedDict

def parse_args():
    p = argparse.ArgumentParser(description="Compile barcode counts with optional CIGAR/MD/Score/Position info")
    p.add_argument('-E', action='store_true', dest='err_flag', help='Append error rates')
    p.add_argument('-C', action='store_true', dest='cigar_flag', help='Append CIGAR strings')
    p.add_argument('-M', action='store_true', dest='md_flag', help='Append MD tags')
    p.add_argument('-S', action='store_true', dest='pos_flag', help='Append alignment start/stop')
    p.add_argument('-A', dest='aln_cutoff', type=float, default=0.05, help='Alignment error cutoff (default 0.05)')
    p.add_argument('list_file', help='TSV: sample_id<tab>counts_file')
    p.add_argument('out_file', help='Output combined count table')
    return p.parse_args()

def load_file_list(path):
    file_list = OrderedDict()
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            sample, fname = line.split()[:2]
            file_list[sample] = fname
    return file_list

def main():
    args = parse_args()

    # Setup logging to a dedicated log file
    log_file = args.out_file + '.log'
    logging.basicConfig(
        filename=log_file,
        filemode='w',
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    logger = logging.getLogger()

    if args.err_flag:
        logger.info("Appending alignment scores")
    if args.cigar_flag:
        logger.info("Appending CIGAR strings")
    if args.md_flag:
        logger.info("Appending MD tags")
    if args.pos_flag:
        logger.info("Appending start/stop positions")
    logger.info(f"Using {args.aln_cutoff} error rate for alignment cutoff")

    file_list = load_file_list(args.list_file)

    counts = defaultdict(dict)
    oligo_id = {}
    aln = {}
    cigar = {}
    md = {}
    pos = {}
    sample_stats = defaultdict(lambda: defaultdict(lambda: {'ct': 0, 'sum': 0}))

    for sample_id, fname in file_list.items():
        logger.info(f"Reading {sample_id} from {fname}")
        with open(fname) as f:
            for line in f:
                parts = line.rstrip('\n').split('\t')
                if len(parts) < 10:
                    continue
                barcode = parts[0]
                try:
                    bc_ct = int(parts[1])
                except ValueError:
                    continue
                flag_B = parts[2]
                oligo = parts[3]
                bc_flag = parts[4]
                bc_aln_str = parts[6]
                bc_cigar_str = parts[7]
                bc_md_str = parts[8]
                bc_pos_str = parts[9]

                sample_stats[sample_id][bc_flag]['ct'] += 1
                sample_stats[sample_id][bc_flag]['sum'] += bc_ct

                if ',' in bc_aln_str or bc_aln_str == "NA":
                    continue
                try:
                    bc_aln = float(bc_aln_str)
                except Exception as e:
                    logger.warning(f"Could not parse alignment score '{bc_aln_str}' for barcode {barcode} in sample {sample_id}: {e}")
                    continue

                if bc_flag in ('0', '2') and oligo != '*':
                    if bc_aln <= args.aln_cutoff:
                        if sample_id in counts[barcode]:
                            logger.error(f"Duplicate barcode/sample combo {barcode}/{sample_id}")
                            raise RuntimeError(f"Duplicate barcode/sample combo {barcode}/{sample_id}")
                        counts[barcode][sample_id] = bc_ct
                        if barcode in oligo_id:
                            if oligo_id[barcode] != oligo:
                                logger.error(f"Oligo ID mismatch for {barcode}")
                                raise RuntimeError(f"Oligo ID mismatch for {barcode}")
                            if aln[barcode] != bc_aln:
                                logger.error(f"Alignment mismatch for {barcode}")
                                raise RuntimeError(f"Alignment mismatch for {barcode}")
                            if cigar[barcode] != bc_cigar_str:
                                logger.error(f"CIGAR mismatch for {barcode}")
                                raise RuntimeError(f"CIGAR mismatch for {barcode}")
                            if md[barcode] != bc_md_str:
                                logger.error(f"MD mismatch for {barcode}")
                                raise RuntimeError(f"MD mismatch for {barcode}")
                            if pos[barcode] != bc_pos_str:
                                logger.error(f"Position mismatch for {barcode}")
                                raise RuntimeError(f"Position mismatch for {barcode}")
                        else:
                            oligo_id[barcode] = oligo
                            aln[barcode] = bc_aln
                            cigar[barcode] = bc_cigar_str
                            md[barcode] = bc_md_str
                            pos[barcode] = bc_pos_str

    logger.info("Writing output file")
    with open(args.out_file, 'w') as out:
        header = ['Barcode', 'Oligo']
        if args.err_flag: header.append('Error')
        if args.cigar_flag: header.append('CIGAR')
        if args.md_flag: header.append('cs')
        if args.pos_flag: header.append('Aln_Start:Stop')
        header.extend(file_list.keys())
        out.write('\t'.join(header) + '\n')

        for bc in counts:
            row = [bc, oligo_id[bc]]
            if args.err_flag: row.append(str(aln[bc]))
            if args.cigar_flag: row.append(cigar[bc])
            if args.md_flag: row.append(md[bc])
            if args.pos_flag: row.append(pos[bc])
            for sample_id in file_list.keys():
                row.append(str(counts[bc].get(sample_id, 0)))
            out.write('\t'.join(row) + '\n')

        # Append summary pseudo-barcode lines for each sample
        logger.info("Writing summary stats to output file")
        for sample_id in file_list.keys():
            for key in sorted(sample_stats[sample_id].keys()):
                st = sample_stats[sample_id][key]
                row = [key, args.out_file]
                if args.err_flag: row.append("NA")
                if args.cigar_flag: row.append("NA")
                if args.md_flag: row.append("NA")
                if args.pos_flag: row.append("NA")
                for id_check in file_list.keys():
                    if id_check == sample_id:
                        row.append(str(st['sum']))
                    else:
                        row.append("0")
                out.write('\t'.join(row) + '\n')
                # Log summary stats for this sample/key
                logger.info(f"Summary for sample={sample_id}, key={key}: count={st['ct']}, sum={st['sum']}")

if __name__ == '__main__':
    main()