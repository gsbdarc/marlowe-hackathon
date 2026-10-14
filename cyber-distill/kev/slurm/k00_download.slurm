#!/bin/bash
#SBATCH --job-name=kev_download
#SBATCH --partition=normal
#SBATCH --time=02:00:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=2
#SBATCH --output=kev/logs/kev_download_%j.out
#SBATCH --error=kev/logs/kev_download_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=jeffott@stanford.edu

# One-time: Kev-4B, Kev-9B and Kev-27B (v1.0) plus their Qwen3.5 bases into HF_HOME, about 80 GB.
# Submit from cyber-distill/ after kev/setup.sh:  mkdir -p kev/logs && sbatch kev/slurm/k00_download.slurm
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
source kev/env.sh
df -h "$HF_HOME" | tail -1
"$KEV_VENV/bin/python" kev/scripts/k00_download.py "$KEV_4B" "$KEV_9B" "$KEV_27B"
du -sh "$HF_HOME"
