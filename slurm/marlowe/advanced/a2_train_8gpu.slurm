#!/bin/bash
#SBATCH -J a2-27b-8gpu
#SBATCH --account=marlowe-m000106
#SBATCH --partition=preempt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=8
#SBATCH --exclusive
#SBATCH --mem=0
#SBATCH --time=01:00:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu

# A2, part 2: the same fine-tune on all 8 H100s of one node, sharded with FSDP2: each GPU holds 1/8 of the weights,
# gradients and optimizer state. --exclusive --mem=0: the whole node and all its memory.
#   sbatch slurm/marlowe/advanced/a2_train_8gpu.slurm
#   RUN=a2-batch2 BATCH=2 ACCUM=1 sbatch slurm/marlowe/advanced/a2_train_8gpu.slurm   # a named run with other settings
set -euo pipefail
module load slurm mps
source env/marlowe.sh
GPUS=8
source slurm/train_27b_args.sh
job_timer
RUN=${RUN:-a2-8gpu}
OUT=$WORK/runs/$RUN
mkdir -p logs && rm -rf "$OUT"
gpu_log "logs/gpu-$SLURM_JOB_ID.csv"
wandb_watch "$RUN"
cd "$KEV_HOME/kev"
$KEV_HOME/kev/.venv/bin/torchrun --standalone --nproc_per_node 8 -m kev.train $TRAIN_ARGS --out "$OUT" 2>&1 | stamp
