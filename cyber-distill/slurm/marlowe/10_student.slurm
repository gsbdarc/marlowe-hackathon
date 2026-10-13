#!/bin/bash
#SBATCH --job-name=cyber_student
#SBATCH --account=FILL_ACCOUNT
#SBATCH --partition=FILL_PARTITION
#SBATCH --nodes=1
#SBATCH -G 1
#SBATCH --output=logs/cyber_student_%j.out
#SBATCH --error=logs/cyber_student_%j.err
#SBATCH --time=04:00:00
#SBATCH --mail-type=ALL
#SBATCH --mail-user=nrapstin@stanford.edu

# Stage 10 on one Marlowe node. Arguments go to scripts/10_train_student.py.
# Checkpoint 3 (1 H100):  sbatch slurm/marlowe/10_student.slurm --size 25k --name ckpt3
# Checkpoint 4 (8 H100):  sbatch -G 8 --exclusive slurm/marlowe/10_student.slurm --size 200k --name ckpt4
# FILL per our allocation (Marlowe Slurm docs): partition preempt with account marlowe-m000106,
# or batch with marlowe-m000106-pm01 (hero: -pl01). Preempted jobs restart from the beginning:
# the teacher skips finished shards; add --resume to a student run.
set -euo pipefail
# Marlowe Slurm docs: load mps to avoid CUDA_ERROR_MPS_CONNECTION_FAILED (and slurm for srun).
module load slurm mps
source scripts/marlowe/env.sh
NGPU=$(nvidia-smi -L | wc -l)
nvidia-smi --query-gpu=name,memory.total --format=csv
"$VENV/bin/torchrun" --standalone --nproc_per_node "$NGPU" scripts/10_train_student.py "$@"
