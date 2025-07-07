#!/usr/bin/env python3
"""
read_stats.py

Generate read-stats PDF summarizing good barcodes and read counts per replicate.

Usage:
    read_stats.py <stats_out_file> <acc_file> <id_out> <out_dir>

Outputs:
    <out_dir>/<id_out>_read_stats.pdf
"""
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import MaxNLocator

def main():
    parser = argparse.ArgumentParser(description="Generate read-stats PDF summarizing good barcodes and read counts per replicate.")
    parser.add_argument('stats_file', help='Tab-delimited stats file with Sample, Key, Count, Sum')
    parser.add_argument('acc_file', help='Accumulator file: file_name<tab>rep<tab>cell<tab>source')
    parser.add_argument('id_out', help='Output prefix')
    parser.add_argument('out_dir', help='Output directory')
    args = parser.parse_args()

    # Load stats file
    stats_df = pd.read_csv(args.stats_file, sep='\t')

    # Define valid keys for total
    valid_keys = ["0", "1", "2"]

    # Total reads
    total_df = stats_df[stats_df["Key"].isin(valid_keys)].groupby("Sample").agg({"Sum": "sum"}).reset_index()
    total_df = total_df.rename(columns={"Sum": "Sum_total"})

    # Good reads (key 0)
    good_df = stats_df[stats_df["Key"] == "0"].copy()
    good_df = good_df[["Sample", "Sum", "Count"]].rename(columns={"Sum": "Sum_good", "Count": "Count_good"})

    # Merge
    merged = pd.merge(total_df, good_df, on="Sample", how="left")
    merged.fillna(0, inplace=True)

    # Load rep-to-cell mapping with correct columns
    acc_df = pd.read_csv(args.acc_file, sep='\t', header=None, names=["file_name", "rep", "cell", "source"])

    # Strip whitespaces
    acc_df["rep"] = acc_df["rep"].astype(str).str.strip()
    acc_df["cell"] = acc_df["cell"].astype(str).str.strip()
    merged["Sample"] = merged["Sample"].astype(str).str.strip()

    # Map cell types
    sample_to_cell = dict(zip(acc_df["rep"], acc_df["cell"]))
    merged["cell"] = merged["Sample"].map(sample_to_cell)

    if merged["cell"].isna().any():
        print("Warning: Some samples were not assigned to a cell type! Check acc_file and Sample column.")

    # Define color map for cells
    cell_types = sorted(merged["cell"].dropna().unique())
    color_palette = plt.get_cmap("tab10")
    cell_color_map = {cell: color_palette(i % 10) for i, cell in enumerate(cell_types)}

    # Sort by cell type and total reads (descending)
    merged = merged.sort_values(by=["cell", "Sum_total"], ascending=[True, False]).reset_index(drop=True)

    # Assign colors
    colors = merged["cell"].map(cell_color_map)

    # PDF output
    pdf_path = f"{args.out_dir}/{args.id_out}_read_stats.pdf"
    with PdfPages(pdf_path) as pdf:
        # Good barcodes plot
        fig1, ax1 = plt.subplots(figsize=(8, 10))
        ax1.barh(merged["Sample"], merged["Count_good"], color=colors)
        ax1.set_xlabel("Good Barcodes (Count)")
        ax1.set_title("Good Barcodes per Replicate")
        ax1.xaxis.set_major_locator(MaxNLocator(integer=True, prune='both', nbins=6))
        handles = [plt.Rectangle((0,0),1,1, color=cell_color_map[cell]) for cell in cell_color_map]
        ax1.legend(handles, cell_color_map.keys(), title="Cell Type")
        ax1.set_yticks(range(len(merged["Sample"])))
        ax1.set_yticklabels(merged["Sample"])
        pdf.savefig(fig1)
        plt.close(fig1)

        # Total vs Good Reads plot
        fig2, ax2 = plt.subplots(figsize=(8, 10))
        ax2.barh(merged["Sample"], merged["Sum_total"], color=colors, alpha=0.3, label="Total Reads")
        ax2.barh(merged["Sample"], merged["Sum_good"], color=colors, label="Good Reads")
        ax2.set_xlabel("Read Counts")
        ax2.set_title("Total vs Good Reads per Replicate")
        ax2.legend()
        ax2.xaxis.set_major_locator(MaxNLocator(prune='both', nbins=6))
        ax2.set_yticks(range(len(merged["Sample"])))
        ax2.set_yticklabels(merged["Sample"])
        pdf.savefig(fig2)
        plt.close(fig2)

    print(f"PDF written to: {pdf_path}")

if __name__ == "__main__":
    main()
