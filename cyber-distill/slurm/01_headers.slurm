#!/bin/bash
#SBATCH --job-name=cyber_headers
#SBATCH --partition=normal
#SBATCH --array=0-30
#SBATCH --output=logs/cyber_headers_%A_%a.out
#SBATCH --error=logs/cyber_headers_%A_%a.err
#SBATCH --time=00:30:00
#SBATCH --mem=4G
#SBATCH --cpus-per-task=4
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=nrapstin@stanford.edu

# Stage 1a: read SEC headers for one filing year per array task (task 0 = 1996, task 30 = 2026).
# Test runs read ~2,000 headers/s with 16 threads; a full year is under 30,000 filings.
# Submit from the project root: sbatch slurm/01_headers.slurm
cd /zfs/projects/darc/marlowe_hackathon/cyber-distill
../.venv/bin/python scripts/01_headers.py --year $((1996 + SLURM_ARRAY_TASK_ID)) --threads 16
