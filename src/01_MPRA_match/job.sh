#!/bin/bash
#$ -N MPRAmatch
#$ -cwd
#$ -pe smp 8
#$ -l h_vmem=64G
#$ -o ../../logs/MPRAmatch.out
#$ -e ../../logs/MPRAmatch.err

# activate conda env
source /projectnb/vcres/myousry/miniconda3/etc/profile.d/conda.sh
conda activate mpra

# run
./run_match.sh