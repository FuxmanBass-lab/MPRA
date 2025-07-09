#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# USAGE:
#   ./run_model.sh
#
# EDIT THESE PATHS/VARIABLES for your run:
# -----------------------------------------------------------------------------

SRC="/projectnb/vcres/myousry/MPRA/src"                # source code root (python + R)
SCRIPTS="/projectnb/vcres/myousry/MPRA/scripts"        # helper scripts directory
REF_FASTA="/projectnb/vcres/myousry/MPRA/data/library/OL49_reference.fasta.gz"
COUNT_DIR="/projectnb/vcres/myousry/MPRA/results/02_count"
MODEL_IN="/projectnb/vcres/myousry/MPRA/results/03_model/inputs"
MODEL_OUT="/projectnb/vcres/myousry/MPRA/results/03_model/out"
ID_OUT="OL49_trial"
PROJ="OL49"
PREFIX="trial"
NEG_CTRL="negCtrl"
POS_CTRL="posCtrl"
EXP="exp"
EXP_FASTA="/projectnb/vcres/myousry/MPRA/data/library/exp.fasta.gz"
NEG_CTRL_FASTA="/projectnb/vcres/myousry/MPRA/data/library/negCtrl.fasta.gz"
POS_CTRL_FASTA="/projectnb/vcres/myousry/MPRA/data/library/posCtrl.fasta.gz"

# -----------------------------------------------------------------------------
# NO NEED TO EDIT BELOW THIS LINE
# -----------------------------------------------------------------------------

# Sanity check for required files and scripts
for f in "$SCRIPTS/make_project_list.py" "$SCRIPTS/make_attributes_oligo.py"; do
  if [ ! -e "$f" ]; then
    echo "ERROR: cannot find required script: $f" >&2
    exit 1
  fi
done

# Check FASTA files
for f in "$EXP_FASTA" "$NEG_CTRL_FASTA" "$POS_CTRL_FASTA"; do
  if [ ! -e "$f" ]; then
    echo "ERROR: cannot find required FASTA: $f" >&2
    exit 1
  fi
done

mkdir -p "$MODEL_IN"
mkdir -p "$MODEL_OUT"

cd "$MODEL_IN"

# Remove existing combined proj_list if exists
rm -f "${ID_OUT}.proj_list"

# Process EXP
echo "Creating project list for EXP..."
python3 "$SCRIPTS/make_project_list.py" "$EXP_FASTA" "$EXP"
cat "${EXP}.proj_list" >> "${ID_OUT}.proj_list"

# Process NEG_CTRL
echo "Creating project list for NEG_CTRL..."
python3 "$SCRIPTS/make_project_list.py" "$NEG_CTRL_FASTA" "$NEG_CTRL"
cat "${NEG_CTRL}.proj_list" >> "${ID_OUT}.proj_list"

# Process POS_CTRL
echo "Creating project list for POS_CTRL..."
python3 "$SCRIPTS/make_project_list.py" "$POS_CTRL_FASTA" "$POS_CTRL"
cat "${POS_CTRL}.proj_list" >> "${ID_OUT}.proj_list"

# Optionally clean up individual proj_list files
rm -f "${EXP}.proj_list" "${NEG_CTRL}.proj_list" "${POS_CTRL}.proj_list"

# Create attributes file from merged proj_list
echo "Creating attributes file..."
python3 "$SCRIPTS/make_attributes_oligo.py" "${ID_OUT}.proj_list" "$ID_OUT" 2> make_attributes_warnings.txt

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
source("${SRC}/03_MPRA_model/model.r")
proj_out <- MPRAmodel(count_proj, attr_proj, cond_proj, filePrefix=paste0(proj, "_", prefix), negCtrlName=negCtrl, posCtrlName=posCtrl, projectName=proj, prior=FALSE, method='ssn', runAllelic=FALSE)
writeLines(capture.output(sessionInfo()), "sessionInfo.txt")
EOF

cd "$MODEL_OUT"
Rscript "$MODEL_OUT/custom.r"
echo "R model run complete!"