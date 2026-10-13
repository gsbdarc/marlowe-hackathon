#!/bin/bash
#SBATCH --job-name=cyber_teacher
#SBATCH --account=FILL_ACCOUNT
#SBATCH --partition=FILL_PARTITION
#SBATCH --nodes=1
#SBATCH -G 8
#SBATCH --exclusive
#SBATCH --output=logs/cyber_teacher_%j.out
#SBATCH --error=logs/cyber_teacher_%j.err
#SBATCH --time=02:00:00
#SBATCH --mail-type=ALL
#SBATCH --mail-user=nrapstin@stanford.edu

# Stage 7 teacher labeling on one Marlowe node (8 H100): vLLM server in the container
# (gsbdarc/vllm_helper), client scripts/07_teacher.py. Arguments go to the client.
# Pilot (by Oct 23):  sbatch slurm/marlowe/07_teacher.slurm --run-id pilot --samples train --limit 10000
# Full run:           sbatch --time=12:00:00 slurm/marlowe/07_teacher.slurm --run-id full \
#                         --samples train val test test_incident_slice
# Submit from the code directory; mkdir -p logs first. If vLLM rejects tensor parallel 8 for the
# FP8 checkpoint, set VLLM_EXTRA="--enable-expert-parallel" (or VLLM_TP=4) and record what worked.
# FILL per our allocation (Marlowe Slurm docs): partition preempt with account marlowe-m000106,
# or batch with marlowe-m000106-pm01 (hero: -pl01). Preempted jobs restart from the beginning:
# the teacher skips finished shards; add --resume to a student run.
set -euo pipefail
command -v apptainer >/dev/null || module load apptainer
source scripts/marlowe/env.sh
source scripts/vllm/env.sh
source "$VLLM_HELPER/vllm.sh"
export VLLM_MODEL=$TEACHER_MODEL VLLM_TP=${VLLM_TP:-8} VLLM_MAX_LEN=4096
nvidia-smi
vllm serve --max-logprobs 20 --seed 20261106 ${TEACHER_REVISION:+--revision "$TEACHER_REVISION"} \
    ${VLLM_EXTRA:-} > "logs/vllm_server_${SLURM_JOB_ID}.log" 2>&1 &
bash scripts/vllm/wait_ready.sh 3600
"$VENV/bin/python" scripts/07_teacher.py "$@"
vllm stop
