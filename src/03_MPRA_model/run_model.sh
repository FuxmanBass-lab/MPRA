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
POS_CTRL="expCtrl"

# -----------------------------------------------------------------------------
# NO NEED TO EDIT BELOW THIS LINE
# -----------------------------------------------------------------------------

# Sanity check for required files and scripts
for f in "$REF_FASTA" "$SCRIPTS/make_project_list.py" "$SCRIPTS/make_attributes.py"; do
  if [ ! -e "$f" ]; then
    echo "ERROR: cannot find required input: $f" >&2
    exit 1
  fi
done

mkdir -p "$MODEL_IN"
mkdir -p "$MODEL_OUT"

cd "$MODEL_IN"

# Create project list
echo "Creating project list..."
python3 "$SCRIPTS/make_project_list.py" "$REF_FASTA" "$ID_OUT"

# Create attributes file
echo "Creating attributes file..."
python3 "$SCRIPTS/make_attributes_oligo.py" "${ID_OUT}.proj_list" "$ID_OUT" 2> make_attributes_warnings.txt

# Create custom R script
echo "Generating custom.R..."

cat << EOF > "$MODEL_OUT/custom.R"
proj <- "$PROJ"
prefix <- "$PREFIX"
negCtrl <- "$NEG_CTRL"
posCtrl <- "$POS_CTRL"
attr_proj <- read.delim("${MODEL_IN}/${ID_OUT}.attributes", stringsAsFactors=FALSE)
count_proj <- read.delim("${COUNT_DIR}/${ID_OUT}.count", stringsAsFactors=FALSE)
cond_proj <- read.delim("${COUNT_DIR}/${ID_OUT}_condition.txt", stringsAsFactors=FALSE, row.names=1, header=FALSE)
colnames(cond_proj) <- "condition"
source("${SRC}/03_MPRAmodel/model.r")
proj_out <- MPRAmodel(count_proj, attr_proj, cond_proj, filePrefix=paste0(proj,prefix, sep=""), negCtrlName=negCtrl, posCtrlName=posCtrl, projectName=proj, cSkew=FALSE, prior=FALSE, method='ss')
writeLines(capture.output(sessionInfo()), "sessionInfo.txt")
EOF

echo "Preparation complete. To run R model:"
echo "  cd $MODEL_OUT"
echo "  module load R/4.4.0"
echo "  Rscript custom.R"

echo "All done!"