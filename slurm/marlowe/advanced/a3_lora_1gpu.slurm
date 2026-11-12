#!/bin/bash
#SBATCH -J a3-27b-lora
#SBATCH --account=marlowe-c001
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=240G
#SBATCH --time=01:00:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu

# A3 bonus: a LoRA of Qwen3.8-27B on one H100, the same 100 steps and 16 filings per step as the A2 full fine-tune.
# The base weights stay frozen in bf16; only a rank-16 adapter and the pointer head train, so it fits on one GPU.
#   sbatch slurm/marlowe/advanced/a3_lora_1gpu.slurm
set -euo pipefail
module load slurm mps                  # mps avoids CUDA_ERROR_MPS_CONNECTION_FAILED (Marlowe docs)
source env/marlowe.sh
GPUS=1
source slurm/marlowe/advanced/train_27b_args.sh
source slurm/marlowe/advanced/wandb.sh
# The LoRA settings come after TRAIN_ARGS, so they replace its --full_ft 1 and --lr 2e-6
LORA_ARGS="--full_ft 0 --lora 16 --lr 2e-4"
job_timer
OUT=$WORK/runs/a3-lora
mkdir -p logs && rm -rf "$OUT"
gpu_log "logs/gpu-$SLURM_JOB_ID.csv"
wandb_room advanced-a3 a3-lora
cd "$KEV_HOME/kev"
$PY -m kev.train $TRAIN_ARGS $LORA_ARGS --out "$OUT" 2>&1 | stamp
