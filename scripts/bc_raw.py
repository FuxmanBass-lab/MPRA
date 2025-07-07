#!/usr/bin/env python3
"""
bc_raw.py

Split the full MPRA count table into DNA vs. each cell-type:
  - cond_file:  two-column TSV (celltype, replicate_count), includes DNA
  - count_table: full .count table from MPRAcount
  - id_out:      project prefix (used in output filenames)
  - out_dir:     directory to write the per-cell counts
"""

import sys
import pandas as pd
from pathlib import Path

def main():
    cond_file, count_file, id_out, out_dir = sys.argv[1:]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load condition metadata
    cond = pd.read_csv(cond_file, sep='\t', header=None, index_col=0, names=['condition'])
    cond['condition'] = pd.Categorical(cond['condition'], categories=['DNA'] + [c for c in cond.index if c != 'DNA'], ordered=True)

    # Load the full barcode-level count table
    df = pd.read_csv(count_file, sep='\t', dtype=str)

    # For each non-DNA celltype, write out subset
    for cell in cond['condition'].cat.categories:
        if cell == 'DNA':
            continue
        # pick columns: Barcode, Oligo, plus any replicates labeled DNA or this cell
        reps = cond.index[(cond['condition']=='DNA') | (cond['condition']==cell)]
        cols = ['Barcode','Oligo'] + list(reps)
        subset = df.loc[:, cols]
        subset.to_csv(out_dir / f"{id_out}_{cell}.counts", sep='\t', index=False, quoting=False)

if __name__ == '__main__':
    if len(sys.argv) != 5:
        print("Usage: bc_raw.py <cond_file> <count_table> <id_out> <out_dir>", file=sys.stderr)
        sys.exit(1)
    main()
