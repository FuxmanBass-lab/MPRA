#!/usr/bin/env bash

# load settings
source config/settings.sh

# _________________ Environment ________________

# verify conda is available and env file exists
if ! command -v conda &>/dev/null; then
  echo "ERROR: conda not found in PATH—please install Conda and/or add it to path." >&2
  exit 1
fi
if [ ! -f env.yml ]; then
  echo "ERROR: env.yml missing in project root." >&2
  exit 1
fi

# check that settings file is present
if [ ! -f config/settings.sh ]; then
  echo "ERROR: config/settings.sh not found. Please create and customize it before running the pipeline."
  exit 1
fi


# create conda env if not already present
if ! conda env list | grep -q "^${ENV_NAME}[[:space:]]"; then
  conda env create -f env.yml
fi

echo "Conda Environment is created"


# _________________ Excutables ________________

# verify presence of pipeline wrapper scripts and ensure pipeline wrapper scripts are executable
for pair in "01_MPRA_match run_match.sh" "02_MPRA_count run_count.sh" "03_MPRA_model run_model.sh" "04_MPRA_compare run_compare.sh"; do
  dir=$(echo $pair | cut -d' ' -f1)
  script=$(echo $pair | cut -d' ' -f2)
  if [ ! -f "$SRC_DIR/$dir/$script" ]; then
    echo "ERROR: missing $script in $SRC_DIR/$dir" >&2
    exit 1
  fi
done
chmod +x "$SRC_DIR"/*/run_*.sh

# verify pipeline.sh is present and executable
if [ ! -f "./pipeline.sh" ]; then
  echo "ERROR: pipeline.sh not found in project root." >&2
  exit 1
fi
chmod +x "./pipeline.sh"

echo "Main pipeline scripts are present and excutable."


# _________________ Notes ________________


# remind user to customize settings
echo "Please customize your config/settings.sh before running the pipeline"


# guide user to usage details place.
echo "For full usage details, please read the README.md in the project root."
