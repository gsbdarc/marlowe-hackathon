#!/bin/bash
#SBATCH -J ceo-cp5
#SBATCH --account=marlowe-m000106
#SBATCH --partition=preempt
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=8
#SBATCH --exclusive
#SBATCH --time=01:00:00
#SBATCH --output=logs/%x-%j.out

# Checkpoint 5 (advanced): two Marlowe nodes, 16 H100s, one torchrun per node, with resume points.
#   STOP_AFTER=100 sbatch slurm/marlowe/05_train_2node.slurm   # stops after step 100, as a preemption would
#   sbatch slurm/marlowe/05_train_2node.slurm                  # continues from $OUT/resume to step $STEPS
# Kev writes a resume point every SAVE_STEPS optimizer steps; --resume 1 continues from the last one. A resumed
# run must keep the same training arguments (STEPS included); only the save and stop settings may change.
set -euo pipefail
module load slurm mps
source env/marlowe.sh
STEPS=${STEPS:-300}
GPUS=16
source slurm/train_args.sh
OUT=$WORK/runs/cp5-2node
SAVE_STEPS=${SAVE_STEPS:-50}
STOP=${STOP_AFTER:+--stop_after $STOP_AFTER}
mkdir -p logs
export MASTER_ADDR=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1) MASTER_PORT=29500
wandb_watch cp5-2node
cd "$KEV_HOME/kev"
srun --kill-on-bad-exit=1 bash -c "nvidia-smi --query-gpu=timestamp,index,utilization.gpu,memory.used --format=csv -l 30 > $OLDPWD/logs/gpu-$SLURM_JOB_ID-\$(hostname -s).csv &
  exec $KEV_HOME/kev/.venv/bin/torchrun --nnodes $SLURM_NNODES --nproc_per_node 8 \
    --rdzv_id $SLURM_JOB_ID --rdzv_backend c10d --rdzv_endpoint $MASTER_ADDR:$MASTER_PORT \
    -m kev.train $TRAIN_ARGS --out $OUT --resume 1 --save_every_steps $SAVE_STEPS $STOP"
