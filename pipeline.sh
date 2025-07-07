#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# USAGE:
#   ./pipeline.sh [match|count|model|all]
#
# Example:
#   ./pipeline.sh all
# -----------------------------------------------------------------------------

STEP="${1:-all}"

# -----------------------------------------------------------------------------
# EDIT THESE VARIABLES FOR YOUR PROJECT
# -----------------------------------------------------------------------------
SCC_PROJ="vcres"                     # <- SET YOUR SCC PROJECT HERE
BASE_DIR="/projectnb/vcres/myousry/MPRA"
SRC_DIR="$BASE_DIR/src"
LOG_DIR="$BASE_DIR/logs"
CONDA_INIT="/projectnb/vcres/myousry/miniconda3/etc/profile.d/conda.sh"
ENV_NAME="mpra"
MEM="64G"
CORES="16"
RUNTIME="24:00:00"    # max runtime (48 hours)

mkdir -p "$LOG_DIR"

# -----------------------------------------------------------------------------
# HELPER FUNCTION TO CREATE JOB SCRIPT
# -----------------------------------------------------------------------------
write_and_submit_job() {
    local job_name="$1"
    local commands="$2"

    local job_file
    job_file="$(mktemp)"
    cat <<EOF > "$job_file"
#!/bin/bash
#$ -N $job_name
#$ -cwd
#$ -pe smp $CORES
#$ -l h_vmem=$MEM
#$ -l h_rt=$RUNTIME
#$ -o $LOG_DIR/${job_name}.out
#$ -e $LOG_DIR/${job_name}.err

source $CONDA_INIT
conda activate $ENV_NAME

$commands
EOF

    echo "Submitting job: $job_name to SCC project: $SCC_PROJ"
    qsub -P "$SCC_PROJ" "$job_file"

    rm "$job_file"
}

# -----------------------------------------------------------------------------
# DECIDE WHICH STEP(S) TO RUN
# -----------------------------------------------------------------------------
case "$STEP" in
    match)
        write_and_submit_job "MPRAmatch" "$SRC_DIR/01_MPRA_match/run_match.sh"
        ;;
    count)
        write_and_submit_job "MPRAcount" "$SRC_DIR/02_MPRA_count/run_count.sh"
        ;;
    model)
        write_and_submit_job "MPRAmodel" "$SRC_DIR/03_MPRA_model/run_model.sh"
        ;;
    all)
        # Sequential combined job
        cmds="$SRC_DIR/01_MPRA_match/run_match.sh
$SRC_DIR/02_MPRA_count/run_count.sh
$SRC_DIR/03_MPRA_model/run_model.sh"
        write_and_submit_job "MPRAall" "$cmds"
        ;;
    *)
        echo "Usage: ./pipeline.sh [match|count|model|all]"
        exit 1
        ;;
esac

echo "Submission complete! Check jobs with: qstat -u $USER"