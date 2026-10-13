#!/bin/bash
#SBATCH --job-name=cyber_samples
#SBATCH --partition=normal
#SBATCH --output=logs/cyber_samples_%j.out
#SBATCH --error=logs/cyber_samples_%j.err
#SBATCH --time=01:00:00
#SBATCH --mem=64G
#SBATCH --cpus-per-task=4
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=nrapstin@stanford.edu

# Stage 4 report, then Stage 6 samples. Run after every task of slurm/04_prefilter.slurm
# and after scripts/05_split.py. Loads the whole candidate pool (a few million rows with text).
cd /zfs/projects/darc/marlowe_hackathon/cyber-distill
../.venv/bin/python scripts/04_report.py
../.venv/bin/python scripts/06_samples.py "$@"
