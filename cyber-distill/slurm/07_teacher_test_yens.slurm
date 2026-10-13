#!/bin/bash
#SBATCH --job-name=cyber_teacher_test
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --output=logs/cyber_teacher_test_%j.out
#SBATCH --error=logs/cyber_teacher_test_%j.err
#SBATCH --time=00:45:00
#SBATCH --mem=60G
#SBATCH --cpus-per-task=15
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=nrapstin@stanford.edu

# Smoke test of the Stage 7 path on one Yen GPU: the same container, wrapper and client as on
# Marlowe, with a small model (Qwen3-1.7B, the student's base) on 200 training and 200 validation
# items. These labels are not used for anything. Needs scripts/vllm/setup.sh done once.
set -euo pipefail
cd /zfs/projects/darc/marlowe_hackathon/cyber-distill
module load apptainer
source scripts/vllm/env.sh
source "$VLLM_HELPER/vllm.sh"
export VLLM_MODEL=Qwen/Qwen3-1.7B VLLM_MAX_LEN=4096
nvidia-smi --query-gpu=name,memory.total --format=csv
vllm serve --max-logprobs 20 --seed 20261106 > "logs/vllm_server_${SLURM_JOB_ID}.log" 2>&1 &
bash scripts/vllm/wait_ready.sh 1200
../.venv/bin/python scripts/07_teacher.py --run-id yens-test --samples train val --limit 200 --concurrency 64
../.venv/bin/python scripts/07_report.py --run-id yens-test --gpus 1
vllm stop
