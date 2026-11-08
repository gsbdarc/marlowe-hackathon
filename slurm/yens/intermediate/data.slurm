#!/bin/bash -l
#SBATCH -J ceo-data
#SBATCH -p normal
#SBATCH -c 2
#SBATCH --mem=16G
#SBATCH -t 00:20:00
#SBATCH -o logs/%x-%j.out

# Build the training, validation and test files from your copy of Jev's labels, with valid.parquet for scoring
# exercise 2 on validation. Submit from the repo:
#   sbatch slurm/yens/intermediate/data.slurm
set -euo pipefail
source scripts/intermediate/yens.sh
mkdir -p logs
$PY scripts/intermediate/make_kev_data.py
