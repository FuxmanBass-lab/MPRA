#!/usr/bin/env bash
set -euo pipefail

# load project-wide settings
source "$(dirname "${BASH_SOURCE[0]}")/config/settings.sh"

# -----------------------------------------------------------------------------
# USAGE:
#   ./pipeline.sh [match|count|model|compare|all]
#
# Example:
#   ./pipeline.sh all
# -----------------------------------------------------------------------------

STEP="${1:-all}"


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
    compare)
        write_and_submit_job "MPRAcompare" "$SRC_DIR/04_MPRA_compare/run_compare.sh"
        ;;
    all)
        # Sequential combined job
        cmds="$SRC_DIR/01_MPRA_match/run_match.sh
$SRC_DIR/02_MPRA_count/run_count.sh
$SRC_DIR/03_MPRA_model/run_model.sh
$SRC_DIR/04_MPRA_compare/run_compare.sh"
        write_and_submit_job "MPRAall" "$cmds"
        ;;
    *)
        echo "Usage: ./pipeline.sh [match|count|model|compare|all]"
        exit 1
        ;;
esac

echo "Submission complete! Check jobs with: qstat -u $USER"