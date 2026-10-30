#!/bin/bash
#SBATCH -J a3-27b-2node
#SBATCH --account=marlowe-m000106
#SBATCH --partition=preempt
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=8
#SBATCH --exclusive
#SBATCH --mem=0
#SBATCH --time=01:00:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu

# A3: the A2 fine-tune on two Marlowe nodes, 16 H100s, sharded with FSDP2 across both. One torchrun per node; the 16
# processes find each other through the first node (MASTER_ADDR). Same training as A2: 100 steps of 16 records.
#   sbatch slurm/marlowe/advanced/a3_train_2node.slurm
set -euo pipefail
module load slurm mps
source env/marlowe.sh
GPUS=16
source slurm/train_27b_args.sh
job_timer
OUT=$WORK/runs/a3-2node
mkdir -p logs && rm -rf "$OUT"
export MASTER_ADDR=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1) MASTER_PORT=29500
wandb_watch a3-2node
cd "$KEV_HOME/kev"
# On each node: log its GPUs to logs/gpu-<jobid>-<node>.csv, then start its 8 trainer processes
srun --kill-on-bad-exit=1 bash -c "nvidia-smi --query-gpu=timestamp,index,name,utilization.gpu,memory.used,memory.total --format=csv -l 15 > $OLDPWD/logs/gpu-$SLURM_JOB_ID-\$(hostname -s).csv &
  exec $KEV_HOME/kev/.venv/bin/torchrun --nnodes $SLURM_NNODES --nproc_per_node 8 \
    --rdzv_id $SLURM_JOB_ID --rdzv_backend c10d --rdzv_endpoint $MASTER_ADDR:$MASTER_PORT \
    -m kev.train $TRAIN_ARGS --out $OUT" 2>&1 | stamp
