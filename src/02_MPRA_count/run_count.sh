#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# USAGE:
#   ./run_model.sh
# -----------------------------------------------------------------------------

# load project-wide settings
source "$(dirname "${BASH_SOURCE[0]}")/../../config/settings.sh"

# derive paths from settings.sh
ID_OUT="$ID_OUT"
SRC_DIR="$SRC_DIR"
SCRIPTS_DIR="$SCRIPTS_DIR"
RAW_DIR="$SAMPLES_DIR"
ACC_FILE="$ACC_ID_FILE"
PARSED="$PARSED"
OUTDIR="$RESULTS_COUNT"

# -----------------------------------------------------------------------------
# NO NEED TO EDIT BELOW THIS LINE
# -----------------------------------------------------------------------------

# Sanity check for required files
for f in "$ACC_FILE" "$PARSED" "$SRC_DIR/02_MPRA_count/count.py"; do
  if [ ! -e "$f" ]; then
    echo "ERROR: cannot find required input: $f" >&2
    exit 1
  fi
done

# Build comma-separated lists of FASTQs with full path & replicate IDs from acc_id
FASTQS=$(awk -v dir="$RAW_DIR" '{print dir "/" $1}' "$ACC_FILE" | paste -sd, -)
IDS=$(awk '{print $2}' "$ACC_FILE" | paste -sd, -)

mkdir -p "$OUTDIR"

python3 "$SRC_DIR/02_MPRA_count/count.py" \
  --replicate_fastq  "$FASTQS" \
  --replicate_id     "$IDS" \
  --parsed           "$PARSED" \
  --acc_id           "$ACC_FILE" \
  --scripts_dir      "$SCRIPTS_DIR" \
  --out_dir          "$OUTDIR" \
  --id_out           "$ID_OUT"

echo "MPRAcount complete; results in $OUTDIR/"