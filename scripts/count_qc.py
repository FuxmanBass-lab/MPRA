#!/usr/bin/env python3
"""
count_qc.py

Generate celltype-specific QC plots from MPRA count table.

Usage:
    count_qc.py <celltypes_file> <count_table> <id_out> <out_dir>
"""
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def main(celltypes_file, count_table_file, id_out, floc):
    out_dir = Path(floc)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Load and write condition mapping
    ct = pd.read_csv(celltypes_file, sep='\t', header=None,
                     names=['file_loc','replicate','celltype','material'],
                     dtype=str)
    ct = ct[['replicate','celltype']].drop_duplicates()
    cond = pd.DataFrame({'condition': ct['celltype'].values},
                        index=ct['replicate'].values)
    cond['condition'] = pd.Categorical(cond['condition'],
        categories=['DNA']+[c for c in ct['celltype'].unique() if c!='DNA'],
        ordered=True)
    cond_path = out_dir / f"{id_out}_condition.txt"
    cond.to_csv(cond_path, sep='\t', header=False)
    print(f"Wrote condition file to {cond_path}", file=sys.stderr)

    # 2) Load and clean count table
    df = pd.read_csv(count_table_file, sep='\t', dtype=str)
    # drop extra QC columns if present
    for col in ['Error','CIGAR','MD','cs','Aln_Start.Stop']:
        if col in df.columns:
            df.drop(columns=col, inplace=True)
    print("\t".join(df.columns), file=sys.stderr)

    # 3) Loop over cell types
    for cell in cond['condition'].cat.categories:
        if cell == 'DNA':
            continue
        reps = cond.index[cond['condition']==cell].tolist()
        print(f"\nCelltype: {cell}", file=sys.stderr)
        print("Replicates:", *reps, file=sys.stderr)

        # Aggregated barcode-per-oligo
        mask = (df[reps].astype(int) > 0).any(axis=1)
        bc_counts = df.loc[mask, 'Oligo'].value_counts()
        agg_gt10 = (bc_counts > 10).sum()

        # Aggregated counts-per-oligo means
        df[reps] = df[reps].astype(int)
        agg_counts = df.groupby('Oligo')[reps].sum()
        agg_counts['means'] = agg_counts.mean(axis=1)
        mean_bound = np.percentile(agg_counts['means'], 90)
        tot_bound = 0.5 * agg_counts['means'].max()
        xup = max(mean_bound, tot_bound) if cell=='DNA' else min(mean_bound, tot_bound)
        agg_ct_gt20 = (agg_counts['means'] > 20).sum()
        total_oligos = agg_counts.shape[0]

        # Plot aggregated barcode histogram
        plt.figure()
        bc_counts.plot.hist(bins=200)
        plt.axvline(10, color='red')
        plt.xlabel("Barcodes per aggregated Oligo")
        plt.title(f"Aggregated Barcode Count\n"
                  f"{agg_gt10} >10 ("
                  f"{agg_gt10/total_oligos*100:.1f}% of {total_oligos})")
        plt.tight_layout()
        plt.savefig(out_dir / f"{id_out}_{cell}_agg_barcode_QC.pdf")
        plt.close()

        # Clip means to xup to match R logic and fix histogram shape
        agg_counts_clipped = agg_counts[agg_counts['means'] <= xup]
        plt.figure()
        ax = agg_counts_clipped['means'].plot.hist(bins=300)
        plt.axvline(20, color='red')
        plt.xlim(0, xup)
        plt.xlabel("Mean Count per aggregated Oligo")
        plt.title(f"Mean Oligo Counts\n"
                  f"{agg_ct_gt20} >20 ("
                  f"{agg_ct_gt20/total_oligos*100:.1f}% of {total_oligos})")
        plt.tight_layout()
        plt.savefig(out_dir / f"{id_out}_{cell}_agg_counts_QC.pdf")
        plt.close()

        # Per-replicate histograms
        for rep in reps:
            rep_series = df.loc[df[rep].astype(int) > 0, 'Oligo'].value_counts()
            indv_gt10 = (rep_series > 10).sum()
            plt.figure()
            rep_series.plot.hist(bins=200)
            plt.axvline(10, color='red')
            plt.xlabel("Barcodes per Oligo")
            plt.title(f"{cell} {rep} Barcode Count\n"
                      f"{indv_gt10} >10")
            plt.tight_layout()
            plt.savefig(out_dir / f"{id_out}_{cell}_{rep}_barcode_QC.pdf")
            plt.close()

            rep_counts = df.groupby('Oligo')[rep].sum().astype(int)
            clip_val = np.percentile(rep_counts, 80)
            rep_counts_clipped = rep_counts[rep_counts <= clip_val]
            indv_ct_gt20 = (rep_counts > 20).sum()
            max_ct = rep_counts.max()
            plt.figure()
            rep_counts_clipped.plot.hist(bins=200)
            plt.axvline(10, color='red')
            plt.xlabel("Counts per Oligo")
            plt.title(f"{cell} {rep} Oligo Counts\n"
                      f"{indv_ct_gt20} >20, max={max_ct}")
            plt.tight_layout()
            plt.savefig(out_dir / f"{id_out}_{cell}_{rep}_counts_QC.pdf")
            plt.close()

if __name__ == '__main__':
    if len(sys.argv) != 5:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    main(*sys.argv[1:])
