export MPRA_ROOT=/projectnb/vcres/myousry/MPRA
export MPRA_SRC=$MPRA_ROOT/src
export PROJ_NAME=mpra_run

mkdir -p $MPRA_SRC
mkdir -p $MPRA_ROOT/$PROJ_NAME/{inputs,out/{MPRAmatch,MPRAcount,MPRAmodel}}


export ENV_DIR=$MPRA_ROOT/env
export ENV_NAME=mpra_env

mkdir -p $ENV_DIR
cd $ENV_DIR


conda env create -f /projectnb/vcres/myousry/MPRA/env.yml

conda activate mpra


cd src 

git clone https://github.com/tewhey-lab/MPRA_oligo_barcode_pipeline.git
git clone https://github.com/tewhey-lab/MPRAmodel.git