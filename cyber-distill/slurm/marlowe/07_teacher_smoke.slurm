#!/bin/bash
#SBATCH --job-name=cyber_teacher_smoke
#SBATCH --account=marlowe-m000106
#SBATCH --partition=preempt
#SBATCH --nodes=1
#SBATCH -G 1
#SBATCH --output=logs/cyber_teacher_smoke_%j.out
#SBATCH --error=logs/cyber_teacher_smoke_%j.err
#SBATCH --time=00:45:00
#SBATCH --mail-type=ALL
#SBATCH --mail-user=nrapstin@stanford.edu

# First job on Marlowe, before downloading the 240 GB teacher: the same container, wrapper and
# client as the pilot, with a small model (Qwen3-1.7B) on one GPU and 200 + 200 items. Checks
# Apptainer, MPS inside the container, the model download and the client. Same as the Yens test
# (slurm/07_teacher_test_yens.slurm). Labels from this model are not used.
#   sbatch slurm/marlowe/07_teacher_smoke.slurm
# Basic access: account marlowe-m000106 on partition preempt (Marlowe Slurm docs).
set -euo pipefail
# Marlowe Slurm docs: load mps to avoid CUDA_ERROR_MPS_CONNECTION_FAILED (and slurm for srun).
module load slurm mps
source scripts/marlowe/env.sh
source scripts/vllm/env.sh
source "$VLLM_HELPER/vllm.sh"
export VLLM_MODEL=Qwen/Qwen3-1.7B VLLM_MAX_LEN=4096
nvidia-smi
vllm serve --max-logprobs 20 --seed 20261106 > "logs/vllm_server_${SLURM_JOB_ID}.log" 2>&1 &
bash scripts/vllm/wait_ready.sh 1800
"$VENV/bin/python" scripts/07_teacher.py --run-id marlowe-smoke --samples train val --limit 200 --concurrency 64
"$VENV/bin/python" scripts/07_report.py --run-id marlowe-smoke --gpus 1
vllm stop
