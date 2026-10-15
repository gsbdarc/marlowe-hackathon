#!/bin/bash
#SBATCH --job-name=cyber_prefilter
#SBATCH --partition=normal
#SBATCH --array=0-63
#SBATCH --output=logs/cyber_prefilter_%A_%a.out
#SBATCH --error=logs/cyber_prefilter_%A_%a.err
#SBATCH --time=01:00:00
#SBATCH --mem=24G
#SBATCH --cpus-per-task=8
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=nrapstin@stanford.edu

# Stage 4: keyword prefilter, one paragraph shard per task (about 1.8M paragraphs,
# ~2,600 paragraphs/s/core measured, so a few minutes on 8 CPUs).
# Submit from the project root: sbatch slurm/04_prefilter.slurm
cd /zfs/projects/darc/marlowe_hackathon/cyber-distill
source scripts/yens/env.sh || exit 1   # caches and configs in /scratch/users/$USER, not home
../.venv/bin/python scripts/04_prefilter.py --workers "$SLURM_CPUS_PER_TASK"
