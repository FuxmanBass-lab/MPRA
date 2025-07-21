# config/settings.sh

# ─── Project identity
export PROJECT_NAME="OL49"         # set to your MPRA project identifier (e.g., OL49)
export PROJECT_SUFFIX="trial"      # set to a run-specific suffix (e.g., date or replicate group)
export ID_OUT="${PROJECT_NAME}_${PROJECT_SUFFIX}"

# ─── Directory layout
export BASE_DIR="/projectnb/vcres/myousry/MPRA"         # root directory of this pipeline
export LOG_DIR="${BASE_DIR}/logs"
export SCRIPTS_DIR="${BASE_DIR}/scripts"                # path to helper scripts directory
export SRC_DIR="${BASE_DIR}/src"                        # path to source code directory
export SAMPLES_DIR="${BASE_DIR}/data/samples"           # directory containing your sample FASTQs
export LIBRARY_DIR="${BASE_DIR}/data/library"           # directory containing library FASTA files
export RESULTS_MATCH="${BASE_DIR}/results/01_match"     # output directory for match step results
export RESULTS_COUNT="${BASE_DIR}/results/02_count"     # output directory for count step results
export RESULTS_MODEL="${BASE_DIR}/results/03_model"     # output directory for model step results
export RESULTS_COMPARE="${BASE_DIR}/results/04_compare" # output directory for compare step results

# ─── Pipeline settings
export SCC_PROJ="vtrs"                                      # your SCC project name for qsub
export CONDA_INIT="/projectnb/vcres/myousry/miniconda3/etc/profile.d/conda.sh"  # path to your conda init script
export ENV_NAME="mpra"                                       # name of the conda environment to activate
export MEM="64G"                                             # memory per job (e.g., 64G)
export CORES=24                                              # number of CPU cores per job
export RUNTIME="24:00:00"                                    # walltime limit for jobs (HH:MM:SS)

# ─── MPRAmatch inputs
export READ1="${LIBRARY_DIR}/${PROJECT_NAME}_r1.fastq.gz"    # path to your R1 FASTQ file
export READ2="${LIBRARY_DIR}/${PROJECT_NAME}_r2.fastq.gz"    # path to your R2 FASTQ file
export REFERENCE="${LIBRARY_DIR}/${PROJECT_NAME}_reference.fasta.gz"   # path to the MPRA reference FASTA
# export ATTRIBUTES_FILE="${BASE_DIR}/data/library/${PROJECT_NAME}_attributes.tsv"  # path to attributes TSV (if used)
export OLIGO_ALN_MISMATCH_RATE_CUTOFF="0.05"    # maximum allowed oligo alignment mismatch rate (default 0.05)

# ─── MPRAcount inputs
export ACC_ID_FILE="${BASE_DIR}/config/acc_id.txt"           # path to accession ID mapping file
export PARSED="${RESULTS_MATCH}/${ID_OUT}.merged.match.enh.mapped.barcode.ct.parsed"  # path to parsed match output from step 1

# ─── MPRAmodel inputs
export NEG_CTRL="negCtrl"                                    # name of your negative control group
export POS_CTRL="posCtrl"                                    # name of your positive control group
export EXP="exp"                                             # name of your experimental group
export EXP_FASTA="${LIBRARY_DIR}/${EXP}.fasta.gz"            # path to experiment FASTA
export NEG_FASTA="${LIBRARY_DIR}/${NEG_CTRL}.fasta.gz"       # path to negative control FASTA
export POS_FASTA="${LIBRARY_DIR}/${POS_CTRL}.fasta.gz"       # path to positive control FASTA

# ─── MPRAcompare inputs
export COMP_FILE="${BASE_DIR}/config/comparisons.tsv"        # path to comparisons definition TSV
export NORM_COUNTS="${RESULTS_MODEL}/out/results/${ID_OUT}_normalized_counts.tsv"  # path to normalized counts TSV from modeling step