#!/bin/bash
#SBATCH -J ceo-cp3
#SBATCH --account=marlowe-m000106
#SBATCH --partition=preempt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=01:00:00
#SBATCH --output=logs/%x-%j.out

# The Yens training job on one H100 on Marlowe. Compare its time per step with the Yens.
#   sbatch slurm/marlowe/03_train_1gpu.slurm
# Basic access: account marlowe-m000106 on the preempt partition (4-hour limit; a preempted job restarts).
set -euo pipefail
module load slurm mps                  # mps avoids CUDA_ERROR_MPS_CONNECTION_FAILED (Marlowe docs)
source env/marlowe.sh
GPUS=1
source slurm/train_args.sh
OUT=$WORK/runs/cp3-1gpu
mkdir -p logs && rm -rf "$OUT"
gpu_log "logs/gpu-$SLURM_JOB_ID.csv"
wandb_watch cp3-1gpu
cd "$KEV_HOME/kev"
$PY -m kev.train $TRAIN_ARGS --out "$OUT"
