#!/bin/bash
#SBATCH -J a2-27b-1gpu
#SBATCH --account=marlowe-m000106
#SBATCH --partition=preempt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=480G
#SBATCH --time=00:30:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu

# A2, part 1: the Qwen3.8-27B full fine-tune on one H100. On one GPU, Kev's trainer keeps the fp32 master weights and
# optimizer state in host memory (~310 GB), hence --mem=480G.
#   sbatch slurm/marlowe/advanced/a2_train_1gpu.slurm
set -euo pipefail
module load slurm mps                  # mps avoids CUDA_ERROR_MPS_CONNECTION_FAILED (Marlowe docs)
source env/marlowe.sh
GPUS=1
source slurm/train_27b_args.sh
job_timer
OUT=$WORK/runs/a2-1gpu
mkdir -p logs && rm -rf "$OUT"
gpu_log "logs/gpu-$SLURM_JOB_ID.csv"
cd "$KEV_HOME/kev"
$PY -m kev.train $TRAIN_ARGS --out "$OUT" 2>&1 | stamp
