#!/bin/bash
#SBATCH --job-name=cyber_student_2n
#SBATCH --account=FILL_ACCOUNT
#SBATCH --partition=FILL_PARTITION
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:8
#SBATCH --exclusive
#SBATCH --output=logs/cyber_student_2n_%j.out
#SBATCH --error=logs/cyber_student_2n_%j.err
#SBATCH --time=04:00:00
#SBATCH --mail-type=ALL
#SBATCH --mail-user=nrapstin@stanford.edu

# Stage 10, checkpoint 5: two Marlowe nodes (16 H100), one torchrun per node.
#   sbatch slurm/marlowe/10_student_2node.slurm --size 400k --name ckpt5
# Resume after a stop (same name):  sbatch slurm/marlowe/10_student_2node.slurm --size 400k --name ckpt5 --resume
# Multi-node runs need DARC's go-ahead (runbook ground rule 5).
set -euo pipefail
source scripts/marlowe/env.sh
export MASTER_ADDR=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)
export MASTER_PORT=29500
srun "$VENV/bin/torchrun" --nnodes "$SLURM_NNODES" --nproc_per_node 8 \
    --rdzv_id "$SLURM_JOB_ID" --rdzv_backend c10d --rdzv_endpoint "$MASTER_ADDR:$MASTER_PORT" \
    scripts/10_train_student.py "$@"
