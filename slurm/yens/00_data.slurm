#!/bin/bash -l
#SBATCH -J ceo-data
#SBATCH -p normal
#SBATCH -c 2
#SBATCH --mem=16G
#SBATCH -t 00:20:00
#SBATCH -o logs/%x-%j.out

# Build the training, validation and test files from Jev's labels. Submit from the repo:
#   sbatch slurm/yens/00_data.slurm
set -euo pipefail
source env/yens.sh
mkdir -p logs
$PY scripts/look.py
$PY scripts/make_kev_data.py
