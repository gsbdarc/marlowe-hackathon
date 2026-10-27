#!/bin/bash -l
#SBATCH -J ceo-train-1gpu
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_MODEL:H200
#SBATCH -c 24
#SBATCH --mem=92G
#SBATCH -t 01:00:00
#SBATCH -o logs/%x-%j.out

# Checkpoint 1: fine-tune Kev-4B on one H200 on the Yens.
#   sbatch slurm/yens/01_train_1gpu.slurm
# One GPU keeps the fp32 master weights and optimizer state in host memory (a 30-step test peaked at 65 GB),
# hence 24 CPUs and 92 GB: the gpu partition allows at most 4,000 MB per CPU.
set -euo pipefail
source env/yens.sh
GPUS=1
source slurm/train_args.sh
OUT=$WORK/runs/cp1-1gpu
mkdir -p logs && rm -rf "$OUT"
gpu_log "logs/gpu-$SLURM_JOB_ID.csv"
echo "$(hostname): $(nvidia-smi --query-gpu=name --format=csv,noheader | paste -sd,)"
wandb_watch cp1-1gpu
cd "$KEV_HOME/kev"
$PY -m kev.train $TRAIN_ARGS --out "$OUT"
