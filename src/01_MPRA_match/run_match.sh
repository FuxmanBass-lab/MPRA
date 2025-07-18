#!/usr/bin/env bash
set -euo pipefail


# -----------------------------------------------------------------------------
# USAGE:
#   ./run_match.sh
# -----------------------------------------------------------------------------

# load project-wide settings
source "$(dirname "${BASH_SOURCE[0]}")/../../config/settings.sh"

# derive paths and filenames from settings.sh
SRC_DIR="$SRC_DIR"
SCRIPTS_DIR="$SCRIPTS_DIR"
READ1="$READ1"
READ2="$READ2"
REF="$REFERENCE"
OUTDIR="$RESULTS_MATCH"
ID_OUT="$ID_OUT"
# optional attributes file
ATTR="${ATTRIBUTES_FILE:-}"
# optional oligo alignment mismatch cutoff
OLISMATCH="${OLIGO_ALN_MISMATCH_RATE_CUTOFF:-}"
if [ -n "${OLISMATCH}" ]; then
  OLISMATCH_ARG="--oligo_alnmismatchrate_cutoff ${OLISMATCH}"
else
  OLISMATCH_ARG=""
fi

# -----------------------------------------------------------------------------
# NO NEED TO EDIT BELOW THIS LINE
# -----------------------------------------------------------------------------

for f in "$READ1" "$READ2" "$REF" "$SRC_DIR/01_MPRA_match/match.py"; do
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

python3 "$SRC_DIR/01_MPRA_match/match.py" \
  --read_a           "$READ1" \
  --read_b           "$READ2" \
  --reference_fasta  "$REF" \
  $ATTR_ARG \
  $OLISMATCH_ARG \
  --scripts_dir      "$SCRIPTS_DIR" \
  --out_dir          "$OUTDIR" \
  --id_out           "$ID_OUT"

echo "MPRAmatch complete; results in $OUTDIR/"