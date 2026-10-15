#!/bin/bash
#SBATCH --job-name=cyber_student
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --output=logs/cyber_student_%j.out
#SBATCH --error=logs/cyber_student_%j.err
#SBATCH --time=04:00:00
#SBATCH --mem=60G
#SBATCH --cpus-per-task=15
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=nrapstin@stanford.edu

# Stage 10 on the Yens: hackathon checkpoints 1 and 2. Arguments go to scripts/10_train_student.py.
# Checkpoint 1 (1 H200):  sbatch slurm/10_student_yens.slurm --size 25k --name ckpt1
# Checkpoint 2 (4 H200):  sbatch --gres=gpu:4 --cpus-per-task=60 --mem=240G slurm/10_student_yens.slurm \
#                             --size 25k --name ckpt2-4gpu
# (A Yen GPU node has 4 GPUs and 257 GB; Slurm gives about 3.9 GB per CPU, so keep --mem near the CPU count x 3.9.)
set -euo pipefail
cd /zfs/projects/darc/marlowe_hackathon/cyber-distill
source scripts/yens/env.sh || exit 1   # caches and configs in /scratch/users/$USER, not home
NGPU=$(nvidia-smi -L | wc -l)
nvidia-smi --query-gpu=name,memory.total --format=csv
../.venv/bin/torchrun --standalone --nproc_per_node "$NGPU" scripts/10_train_student.py "$@"
