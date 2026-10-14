#!/bin/bash
#SBATCH --job-name=kev_look
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --time=00:30:00
#SBATCH --mem=48G
#SBATCH --cpus-per-task=12
#SBATCH --output=kev/logs/kev_look_%j.out
#SBATCH --error=kev/logs/kev_look_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=jeffott@stanford.edu

# Zero-shot look at one Kev checkpoint on 18 training paragraphs (kev/scripts/k01_look.py). Answers print to the .out log
# and go to kev/runs/look/. Submit from cyber-distill/; the argument is the checkpoint (default Kev-4B):
#   sbatch kev/slurm/k01_look.slurm
#   sbatch kev/slurm/k01_look.slurm jaredpalmer/kev-9b@v1.0
#   sbatch --mem=96G --cpus-per-task=24 kev/slurm/k01_look.slurm jaredpalmer/kev-27b@v1.0   (51 GB loads through host memory)
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
source kev/env.sh
export HF_HUB_OFFLINE=1   # weights come from the cache filled by k00_download
RUN=${1:-$KEV_4B}
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
"$KEV_VENV/bin/python" kev/scripts/k01_look.py --run "$RUN" --out "kev/runs/look/$(basename "${RUN%@*}")-$SLURM_JOB_ID.jsonl"
