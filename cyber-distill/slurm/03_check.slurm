#!/bin/bash
#SBATCH --job-name=cyber_check
#SBATCH --partition=normal
#SBATCH --output=logs/cyber_check_%j.out
#SBATCH --error=logs/cyber_check_%j.err
#SBATCH --time=00:30:00
#SBATCH --mem=48G
#SBATCH --cpus-per-task=4
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=nrapstin@stanford.edu

# Stage 2-3 checks; run after every task of slurm/02_extract.slurm has finished.
# Reads five small columns of every paragraph (about 120M rows), hence the memory.
cd /zfs/projects/darc/marlowe_hackathon/cyber-distill
../.venv/bin/python scripts/03_check.py
