#!/bin/bash
#SBATCH -J a4-qwen235b-server
#SBATCH --account=marlowe-m000106
#SBATCH --partition=preempt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=8
#SBATCH --exclusive
#SBATCH --mem=0
#SBATCH --time=02:00:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu

# A4: serve Qwen3-235B-A22B-Instruct-2507-FP8 with vLLM on all 8 H100s of one node. Tensor parallel: every layer is
# split across the 8 GPUs. The job writes its address to $WORK/qwen-235b.server and serves until you scancel it or it
# reaches its time limit; label from the login node with scripts/label.py --api chat.
#   sbatch slurm/marlowe/advanced/a4_serve_qwen235b.slurm
set -euo pipefail
module load slurm mps
source env/marlowe.sh
source slurm/train_args.sh             # job_timer and stamp
job_timer
MODEL=Qwen/Qwen3-235B-A22B-Instruct-2507-FP8
REVISION=e156cb4efae43fbee1a1ab073f946a1377e6b969
SIF=$SHARE/containers/vllm-openai_v0.31.0.sif
PORT=$((8100 + SLURM_JOB_ID % 900))
mkdir -p logs && echo "$(hostname -s):$PORT" > "$WORK/qwen-235b.server"
echo "serving $MODEL at http://$(hostname -s):$PORT"
gpu_log "logs/gpu-$SLURM_JOB_ID.csv"
# Marlowe's Apptainer guide: bind the project's scratch into the container and keep every cache there, not in the
# 32 GB home. The container sees this job's environment, so HF_HOME (the shared model cache) and HF_HUB_OFFLINE=1
# from env/marlowe.sh apply inside it.
export VLLM_CACHE_ROOT=$XDG_CACHE_HOME/vllm FLASHINFER_WORKSPACE_DIR=$XDG_CACHE_HOME/flashinfer
apptainer exec --nv --bind /scratch/m000106 "$SIF" \
  vllm serve "$MODEL" --revision "$REVISION" --served-model-name qwen-235b \
    --tensor-parallel-size 8 --max-model-len 16384 --host 0.0.0.0 --port "$PORT" 2>&1 | stamp
