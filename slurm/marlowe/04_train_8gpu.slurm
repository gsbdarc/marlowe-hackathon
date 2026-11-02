#!/bin/bash
#SBATCH -J ceo-cp4
#SBATCH --account=marlowe-m000106
#SBATCH --partition=preempt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=8
#SBATCH --exclusive
#SBATCH --time=01:00:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu

# The same job on all 8 H100s of one Marlowe node, sharded with FSDP2.
#   sbatch slurm/marlowe/04_train_8gpu.slurm
set -euo pipefail
module load slurm mps
source env/marlowe.sh
GPUS=8
source slurm/train_args.sh
OUT=$WORK/runs/cp4-8gpu
mkdir -p logs && rm -rf "$OUT"
gpu_log "logs/gpu-$SLURM_JOB_ID.csv"
wandb_watch cp4-8gpu
cd "$KEV_HOME/kev"
$KEV_HOME/kev/.venv/bin/torchrun --standalone --nproc_per_node 8 -m kev.train $TRAIN_ARGS --out "$OUT"
