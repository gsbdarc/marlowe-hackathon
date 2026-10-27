#!/bin/bash -l
#SBATCH -J ceo-train-2gpu
#SBATCH -p gpu
#SBATCH -G 2
#SBATCH -C GPU_MODEL:H200
#SBATCH -c 16
#SBATCH --mem=64G
#SBATCH -t 01:00:00
#SBATCH -o logs/%x-%j.out

# Checkpoint 2: the same job on both H200s of yen-gpu4, sharded with FSDP2.
#   sbatch slurm/yens/02_train_2gpu.slurm
set -euo pipefail
source env/yens.sh
GPUS=2
source slurm/train_args.sh
OUT=$WORK/runs/cp2-2gpu
mkdir -p logs && rm -rf "$OUT"
gpu_log "logs/gpu-$SLURM_JOB_ID.csv"
echo "$(hostname): $(nvidia-smi --query-gpu=name --format=csv,noheader | paste -sd,)"
wandb_watch cp2-2gpu
cd "$KEV_HOME/kev"
$KEV_HOME/kev/.venv/bin/torchrun --standalone --nproc_per_node 2 -m kev.train $TRAIN_ARGS --out "$OUT"
