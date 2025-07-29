#!/usr/bin/env bash

set -euo pipefail

# -----------------------------------------------------------------------------
# USAGE:
#   ./run_model.sh
# -----------------------------------------------------------------------------

# load project-wide settings
source "$(dirname "${BASH_SOURCE[0]}")/../../config/settings.sh"

# derive script-specific paths from settings
SRC_DIR="$SRC_DIR"
SCRIPTS_DIR="$SCRIPTS_DIR"
COUNT_DIR="${RESULTS_COUNT}"
MODEL_IN="${RESULTS_MODEL}/inputs"
MODEL_OUT="${RESULTS_MODEL}/out"
PROJ="$PROJECT_NAME"
PREFIX="$PROJECT_SUFFIX"
LIBRARY="$LIBRARY_DIR"
# controls and experiment come from settings.sh: NEG_CTRL, POS_CTRL
NEG_CTRL="$NEG_CTRL"
POS_CTRL="$POS_CTRL"
ID_OUT="$ID_OUT"


# -----------------------------------------------------------------------------
# NO NEED TO EDIT BELOW THIS LINE
# -----------------------------------------------------------------------------

# Sanity check for required files and scripts
for f in "$SCRIPTS_DIR/make_project_list.py" "$SCRIPTS_DIR/make_attributes_oligo.py"; do
  if [ ! -e "$f" ]; then
    echo "ERROR: cannot find required script: $f" >&2
    exit 1
  fi
done

mkdir -p "$MODEL_IN"
mkdir -p "$MODEL_OUT"

cd "$MODEL_IN"

# Remove existing combined proj_list if exists
rm -f "${ID_OUT}.proj_list"

# Split reference FASTA into per-project FASTAs
echo "Splitting reference FASTA by project..."
python3 "$SCRIPTS_DIR/map_oligos_proj.py" \
  --map "$LIBRARY/tile_proj_map.tsv" \
  --fasta "$LIBRARY/OL49_reference.fasta.gz" \
  --outdir "$MODEL_IN"

# Loop over expected project FASTAs to build combined proj_list
while read fasta_file; do
  proj=$(basename "$fasta_file" .fasta.gz)
  echo "Creating project list for $proj..."
  python3 "$SCRIPTS_DIR/make_project_list.py" "$MODEL_IN/$fasta_file" "$proj"
  cat "${proj}.proj_list" >> "${ID_OUT}.proj_list"
done < "$MODEL_IN/expected_fastas.txt"

# Clean up individual proj_list files, except the combined list
for f in *.proj_list; do
  if [ "$f" != "${ID_OUT}.proj_list" ]; then
    rm -f "$f"
  fi
done

# Create attributes file from merged proj_list
echo "Creating attributes file..."
python3 "$SCRIPTS_DIR/make_attributes_oligo.py" "${ID_OUT}.proj_list" "$ID_OUT" 2> make_attributes_warnings.txt

# Create custom R script
echo "Generating custom.r..."

cat << EOF > "$MODEL_OUT/custom.r"
proj <- "$PROJ"
prefix <- "$PREFIX"
negCtrl <- "$NEG_CTRL"
posCtrl <- "$POS_CTRL"
attr_proj <- read.delim("${MODEL_IN}/${ID_OUT}.attributes", stringsAsFactors=FALSE)
count_proj <- read.delim("${COUNT_DIR}/${ID_OUT}.count", stringsAsFactors=FALSE)
cond_proj <- read.delim("${COUNT_DIR}/${ID_OUT}_condition.txt", stringsAsFactors=FALSE, row.names=1, header=FALSE)
colnames(cond_proj) <- "condition"
source("${SRC_DIR}/03_MPRA_model/model.r")
proj_out <- MPRAmodel(count_proj, attr_proj, cond_proj, filePrefix=paste0(proj, "_", prefix), negCtrlName=negCtrl, posCtrlName=posCtrl, projectName=proj, prior=FALSE, method='ssn', anchorDNA=TRUE, runAllelic=FALSE, writeBed=FALSE)
writeLines(capture.output(sessionInfo()), "sessionInfo.txt")
EOF

cd "$MODEL_OUT"
Rscript "$MODEL_OUT/custom.r"
echo "R model run complete!"