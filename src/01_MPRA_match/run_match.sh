#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# USAGE:
#   ./run_match.sh
#
# -----------------------------------------------------------------------------
# EDIT THESE PATHS/VARIABLES for your run:
# -----------------------------------------------------------------------------

# --- REQUIRED INPUTS (EDIT HERE) ---
BASE_DIR="/projectnb/vcres/myousry/MPRA"

SRC="$BASE_DIR/src"                    # wrapper python code for each step
SCRIPTS="$BASE_DIR/scripts"            # Directory containing helper scripts
READ1="$BASE_DIR/data/library/OL49_r1.fastq.gz"
READ2="$BASE_DIR/data/library/OL49_r2.fastq.gz"
REF="$BASE_DIR/data/library/OL49_reference.fasta.gz"
OUTDIR="$BASE_DIR/results/01_match"
ID_OUT="OL49_trial"
#ATTR="/projectnb/vcres/myousry/MPRA/data/reference/OL49_attributes.tsv"   # (uncomment if needed)

# --- OPTIONAL: if you want to specify attributes file, uncomment and set ATTR ---
ATTR=""

# -----------------------------------------------------------------------------
# NO NEED TO EDIT BELOW THIS LINE
# -----------------------------------------------------------------------------

for f in "$READ1" "$READ2" "$REF" "$SRC/01_MPRA_match/match.py"; do
  if [ ! -e "$f" ]; then
    echo "ERROR: cannot find required input: $f" >&2
    exit 1
  fi
done

mkdir -p "$OUTDIR"

if [ -n "${ATTR}" ]; then
  ATTR_ARG="--attributes $ATTR"
else
  ATTR_ARG=""
fi

python3 "$SRC/01_MPRA_match/match.py" \
  --read_a           "$READ1" \
  --read_b           "$READ2" \
  --reference_fasta  "$REF" \
  $ATTR_ARG \
  --scripts_dir      "$SCRIPTS" \
  --out_dir          "$OUTDIR" \
  --id_out           "$ID_OUT"

echo "MPRAmatch complete; results in $OUTDIR/"