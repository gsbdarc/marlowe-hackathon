#!/bin/bash
#SBATCH --job-name=cyber_extract
#SBATCH --partition=normal
#SBATCH --array=0-63
#SBATCH --output=logs/cyber_extract_%A_%a.out
#SBATCH --error=logs/cyber_extract_%A_%a.err
#SBATCH --time=04:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=8
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=nrapstin@stanford.edu

# Stages 2-3: extract main-document text and paragraphs, one shard of filings.parquet per task.
# Submit from the project root: sbatch slurm/02_extract.slurm
# Test on three fiscal years instead (single task):
#   sbatch --array=0 slurm/02_extract.slurm --test-years 1998 2008 2022 --limit 200
cd /zfs/projects/darc/marlowe_hackathon/cyber-distill
../.venv/bin/python scripts/02_extract.py --n-shards 64 --workers "$SLURM_CPUS_PER_TASK" "$@"
