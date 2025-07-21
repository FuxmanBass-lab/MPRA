#!/usr/bin/env python3
"""
mapping_qc_plots.py

Translate the R mapping_QC_plots.R script into Python using matplotlib.

Usage:
    mapping_qc_plots.py <parsed_file> <hist_file> <preseq_out> <preseq_in> <fasta_file> <id_out>

Produces a PDF "<id_out>_barcode_qc.pdf" with 5 QC plots.
"""

import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import gzip

def open_text_file(path):
    if path.endswith(".gz"):
        return gzip.open(path, "rt")
    else:
        return open(path, "r")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('parsed_file', help='Parsed counts file')
    parser.add_argument('hist_file', help='Histogram counts file')
    parser.add_argument('preseq_out', help='Preseq output file')
    parser.add_argument('preseq_in', help='Preseq input histogram file')
    parser.add_argument('fasta_file', help='Reference fasta file')
    parser.add_argument('id_out', help='Output prefix / project ID')
    args = parser.parse_args()

    # Load data
    count_hist = pd.read_csv(args.hist_file, sep='\t', header=None)
    flags = pd.read_csv(args.parsed_file, sep='\t', header=None, usecols=[4,6])
    preseq_out = pd.read_csv(args.preseq_out, sep='\t', header=0)
    preseq_in = pd.read_csv(args.preseq_in, sep='\t', header=None)

    # Read fasta IDs (support gzipped input)
    with open_text_file(args.fasta_file) as f:
        lines = f.read().splitlines()
    fasta_ids = [line.lstrip(">") for line in lines[::2]]
    fasta_seqs = lines[1::2]
    fasta_df = pd.DataFrame({'ID': fasta_ids, 'seq': fasta_seqs})

    # Print diagnostics
    print("First row of count.hist:", *count_hist.iloc[0].tolist(), sep='\t')
    print("First row of preseq_out:", *preseq_out.iloc[0].tolist(), sep='\t')
    print("First row of preseq_in:", *preseq_in.iloc[0].tolist(), sep='\t')
    print("Max error rate in flags:", flags.iloc[:,1].max())
    print("Min error rate in flags:", flags.iloc[:,1].min())

    # Plot A — Barcode count histogram (truncated)
    parsed_hist = count_hist[count_hist[1] < count_hist[1].quantile(0.99)]
    maxb = count_hist[1].max()

    # Plot B — Oligo coverage CDF
    xlim_val = count_hist[2].quantile(0.99)
    mean_cov = count_hist[2].mean()
    max_cov = count_hist[2].max()

    # Plot C — Error rate histogram for passing barcodes
    pass_flags = flags[flags.iloc[:,0] == 0].copy()
    pass_flags.iloc[:,1] = pd.to_numeric(pass_flags.iloc[:,1], errors='coerce')

    # Plot D — Mapping flag bar chart
    flag_ct = flags.iloc[:,0].value_counts().reset_index()
    flag_ct.columns = ["Flag", "Freq"]
    flag_ct["Flag"] = flag_ct["Flag"].astype(str)
    flag_ct.loc[flag_ct["Flag"] == "0", "Flag"] = "Passing"
    flag_ct.loc[flag_ct["Flag"] == "2", "Flag"] = "Failed or No Mapping"
    flag_ct.loc[flag_ct["Flag"] == "1", "Flag"] = "Conflict"
    flag_ct["percent"] = (flag_ct["Freq"] / flag_ct["Freq"].sum()) * 100

    # Plot E — Preseq extrapolation
    total_found = (preseq_in[1] * preseq_in[0]).sum()
    total_distinct = preseq_in[1].sum()

    # Create figure
    fig, axs = plt.subplots(3, 2, figsize=(14, 12))

    # A
    axs[0,0].hist(parsed_hist[1], bins=200)
    axs[0,0].set_xlabel("Barcodes per Oligo")
    axs[0,0].set_title(f"Barcode Count - truncated, max: {maxb}")
    # axs[0,0].grid(True, linestyle='--', alpha=0.5)

    # B
    sorted_cov = np.sort(count_hist[2])
    ecdf = np.arange(1, len(sorted_cov)+1) / len(sorted_cov)
    axs[0,1].step(sorted_cov, ecdf, where='post')
    axs[0,1].axvline(mean_cov, linestyle='-', color='red', lw=0.8)
    axs[0,1].axvline(mean_cov*5, linestyle='--', color='red', lw=0.8)
    axs[0,1].axvline(mean_cov/5, linestyle='--', color='red', lw=0.8)
    axs[0,1].set_xlim(0, xlim_val)
    axs[0,1].set_xlabel("Per Oligo Seq Coverage")
    axs[0,1].set_title(f"Oligo Cov CDF - truncated, max: {max_cov}")
    # axs[0,1].grid(True, linestyle='--', alpha=0.5)

    # C
    axs[1,0].hist(pass_flags.iloc[:,1].dropna(), bins=50)
    axs[1,0].set_xlabel("Error Rate for Passing Barcodes")
    axs[1,0].set_title("Oligo Error Rate")
    # axs[1,0].grid(True, linestyle='--', alpha=0.5)

    # D
    axs[1,1].bar(flag_ct["Flag"], flag_ct["Freq"])
    for i, (flag, freq, percent) in enumerate(zip(flag_ct["Flag"], flag_ct["Freq"], flag_ct["percent"])):
        axs[1,1].text(i, freq/2, f"{percent:.1f}%", ha='center', va='center')
    axs[1,1].set_ylabel("Frequency")
    axs[1,1].set_title("Sequence Mapping")

    # E
    axs[2,0].plot(preseq_out['TOTAL_READS'], preseq_out['EXPECTED_DISTINCT'], marker='o', label="Preseq Prediction")
    axs[2,0].fill_between(preseq_out['TOTAL_READS'], preseq_out['LOWER_0.95CI'], preseq_out['UPPER_0.95CI'], alpha=0.3, label="95% CI")
    axs[2,0].scatter([total_found], [total_distinct], color="red", zorder=5, label="Observed")
    axs[2,0].set_xlabel("Total Reads")
    axs[2,0].set_ylabel("Expected Distinct Reads")
    axs[2,0].set_title(f"Expected Distinct per Total Reads\nTotal found: {total_found}, Total distinct: {total_distinct}")
    axs[2,0].legend()
    # axs[2,0].grid(True, linestyle='--', alpha=0.5)

    # Hide last empty panel
    axs[2,1].axis("off")

    # Overall title
    seen = len(count_hist)
    total = len(fasta_df)
    per = round(seen / total, 4) * 100
    fig.suptitle(f"{args.id_out} - {per:.2f}% captured - {seen}/{total}", fontsize=16)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(f"{args.id_out}_barcode_qc.pdf")

if __name__ == "__main__":
    main()