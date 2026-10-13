#!/bin/bash
#SBATCH --job-name=cyber_student
#SBATCH --account=FILL_ACCOUNT
#SBATCH --partition=FILL_PARTITION
#SBATCH --nodes=1
#SBATCH --gres=gpu:1
#SBATCH --output=logs/cyber_student_%j.out
#SBATCH --error=logs/cyber_student_%j.err
#SBATCH --time=04:00:00
#SBATCH --mail-type=ALL
#SBATCH --mail-user=nrapstin@stanford.edu

# Stage 10 on one Marlowe node. Arguments go to scripts/10_train_student.py.
# Checkpoint 3 (1 H100):  sbatch slurm/marlowe/10_student.slurm --size 25k --name ckpt3
# Checkpoint 4 (8 H100):  sbatch --gres=gpu:8 --exclusive slurm/marlowe/10_student.slurm --size 200k --name ckpt4
set -euo pipefail
source scripts/marlowe/env.sh
NGPU=$(nvidia-smi -L | wc -l)
nvidia-smi --query-gpu=name,memory.total --format=csv
"$VENV/bin/torchrun" --standalone --nproc_per_node "$NGPU" scripts/10_train_student.py "$@"
