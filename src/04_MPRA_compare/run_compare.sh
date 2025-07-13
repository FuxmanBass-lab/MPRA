#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# USAGE:
#   ./run_compare.sh
#   (uses built-in COMP_FILE, NORM_COUNTS, OUTDIR variables)
# -----------------------------------------------------------------------------

# load all project-wide settings
source "$(dirname "${BASH_SOURCE[0]}")/../../config/settings.sh"

# compare inputs from settings.sh
COMP_FILE="$COMP_FILE"
NORM_COUNTS="$NORM_COUNTS"
OUTDIR="$RESULTS_COMPARE"

# -----------------------------------------------------------------------------
# NO NEED TO EDIT BELOW THIS LINE
# -----------------------------------------------------------------------------

# Resolve script directory and compare.R path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPARE_R="${SCRIPT_DIR}/compare.r"

# Check files exist
for f in "$NORM_COUNTS" "$COMP_FILE" "$COMPARE_R"; do
  if [ ! -e "$f" ]; then
    echo "ERROR: cannot find file: $f" >&2
    exit 1
  fi
done

# Run the comparison
Rscript "$COMPARE_R" "$NORM_COUNTS" "$COMP_FILE" "$OUTDIR"