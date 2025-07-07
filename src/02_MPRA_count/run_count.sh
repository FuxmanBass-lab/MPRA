#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# USAGE:
#   ./run_count.sh
#
# EDIT THESE PATHS/VARIABLES for your run:
# -----------------------------------------------------------------------------

SRC="/projectnb/vcres/myousry/MPRA/src"          # wrapper python code
SCRIPTS="/projectnb/vcres/myousry/MPRA/scripts"  # helper scripts
RAW_DIR="/projectnb/vcres/myousry/MPRA/data/samples" # directory containing actual FASTQ files
ACC_FILE="/projectnb/vcres/myousry/MPRA/config/acc_id.txt"
PARSED="/projectnb/vcres/myousry/MPRA/results/01_match/OL49_trial.merged.match.enh.mapped.barcode.ct.parsed"
OUTDIR="/projectnb/vcres/myousry/MPRA/results/02_count"
ID_OUT="OL49_trial"

# -----------------------------------------------------------------------------
# NO NEED TO EDIT BELOW THIS LINE
# -----------------------------------------------------------------------------

# Sanity check for required files
for f in "$ACC_FILE" "$PARSED" "$SRC/02_MPRA_count/count.py"; do
  if [ ! -e "$f" ]; then
    echo "ERROR: cannot find required input: $f" >&2
    exit 1
  fi
done

# Build comma-separated lists of FASTQs with full path & replicate IDs from acc_id
FASTQS=$(awk -v dir="$RAW_DIR" '{print dir "/" $1}' "$ACC_FILE" | paste -sd, -)
IDS=$(awk '{print $2}' "$ACC_FILE" | paste -sd, -)

mkdir -p "$OUTDIR"

python3 "$SRC/02_MPRA_count/count.py" \
  --replicate_fastq  "$FASTQS" \
  --replicate_id     "$IDS" \
  --parsed           "$PARSED" \
  --acc_id           "$ACC_FILE" \
  --scripts_dir      "$SCRIPTS" \
  --out_dir          "$OUTDIR" \
  --id_out           "$ID_OUT"

echo "MPRAcount complete; results in $OUTDIR/"