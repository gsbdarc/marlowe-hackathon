#!/bin/bash
#SBATCH -J a2-27b-8gpu
#SBATCH --account=marlowe-c001
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=8
#SBATCH --exclusive
#SBATCH --cpus-per-task=96
#SBATCH --mem=1500G
#SBATCH --time=01:00:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu

# A2, part 2: the same fine-tune on all 8 H100s of one node, sharded with FSDP2: each GPU holds 1/8 of the weights,
# gradients and optimizer state. --exclusive: the whole node. batch sets the CPU count from the memory asked for:
# --mem=0 would ask for 115 CPUs on a 112-CPU node and be refused, so the job asks for 96 CPUs and 1,500 GB.
#   sbatch slurm/marlowe/advanced/a2_train_8gpu.slurm
#   RUN=a2-batch2 BATCH=2 ACCUM=1 sbatch slurm/marlowe/advanced/a2_train_8gpu.slurm   # a named run with other settings
set -euo pipefail
module load slurm mps
source env/marlowe.sh
GPUS=8
source slurm/marlowe/advanced/train_27b_args.sh
source slurm/marlowe/advanced/wandb.sh
job_timer
RUN=${RUN:-a2-8gpu}
OUT=$WORK/runs/$RUN
mkdir -p logs && rm -rf "$OUT"
gpu_log "logs/gpu-$SLURM_JOB_ID.csv"
wandb_room advanced-a2 "$RUN" "$OUT"
cd "$KEV_HOME/kev"
$KEV_HOME/kev/.venv/bin/torchrun --standalone --nproc_per_node 8 -m kev.train $TRAIN_ARGS --out "$OUT" 2>&1 | stamp
wandb_wait
