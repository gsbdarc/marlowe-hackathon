#!/bin/bash
#SBATCH -J b3-finetune-1gpu
#SBATCH --account=marlowe-c001
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:20:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu
#
# NOTE FOR INSTRUCTORS: the class account's medium QOS runs on the batch partition, where the hackathon reservation
# (GSB_Hackathon, Nov 13 12:00-17:00, 4 nodes) lives. Batch jobs are not preempted.

# Beginner B3: run your B2 fine-tune again on one H100 on Marlowe and see how much faster it trains than the Yens A40.
# Submit it from the top of your Marlowe clone and watch the log. By default it spends the H100's speed on data: 1,216
# filings in about 10 minutes. FILINGS=512 spends it on time instead (B2's filings, done sooner); LR= carries over the
# learning rate the room chose in B2.
#   sbatch --reservation=GSB_Hackathon slurm/marlowe/beginner/finetune.slurm
#   FILINGS=512 sbatch --reservation=GSB_Hackathon slurm/marlowe/beginner/finetune.slurm
# B3's challenge: submit it a second time. The first run on Marlowe compiles its GPU kernels into your cache
# ($XDG_CACHE_HOME/triton); the second reuses them, so compare the two runs' Elapsed time in sacct.
# It reads the shared, read-only training filings ($CLASS_DATA) and does not score the model: the training is the same
# as B2, so only the speed changes. The run is $WORK/runs/b3/<jobid>.
set -euo pipefail
module load slurm mps                  # mps avoids CUDA_ERROR_MPS_CONNECTION_FAILED (Marlowe docs)
source env/marlowe.sh
mkdir -p logs "$WORK/runs/b3"
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total --format=csv -l 5 > "logs/gpu-$SLURM_JOB_ID.csv" &
GPUMON=$!; trap 'kill $GPUMON 2>/dev/null || true' EXIT

# The beginner board in the room's W&B team. scripts/beginner/wandb_key.sh finds the team's key: the hackathon's shared
# wandb.env, or a line WANDB_API_KEY=... in .env at the top of the repo (git ignores it). Without a key the job still
# runs; it just does not reach the board.
export WANDB_PROJECT="${WANDB_PROJECT:-Beginner Exercise 3}" WANDB_ENTITY=${WANDB_ENTITY:-Marlowe-Hackathon}
export WANDB_DIR=$WORK WANDB_CACHE_DIR=$XDG_CACHE_HOME/wandb WANDB_CONFIG_DIR=$XDG_CACHE_HOME/wandb-config
source scripts/beginner/wandb_key.sh                 # the room's key: the shared wandb.env, or your .env
GPU=$(nvidia-smi --query-gpu=name --format=csv,noheader -i 0 | awk '{print tolower($2)}')
# Filings to train on: about 10 minutes, as on the Yens (0.49 s each on an H100, against 1.08 s on an A40). Later runs
# reuse the kernels this one compiled and train faster.
FILINGS=${FILINGS:-1216}
LR=${LR:-2e-5}
RUN=$WORK/runs/b3/$SLURM_JOB_ID
NAME=$USER-$GPU-lr$LR-f$FILINGS                  # wandb_watch.py adds the job ID

ARGS=(--data "$CLASS_DATA/train.jsonl" --init_from jaredpalmer/kev-4b@v1.0
      --base Qwen/Qwen3.5-4B-Base --base_revision 1001bb4d826a52d1f399e183466143f4da7b741b
      --device cuda --dtype bf16 --weights_dtype fp32 --checkpointing 1 --max_state 2048 --seed 0
      --lora 16 --lr "$LR" --batch 1 --accum 8 --max_steps $((FILINGS / 8)) --out "$RUN")
WATCH=
if [ -n "${WANDB_API_KEY:-}" ] || [ "${WANDB_MODE:-}" = offline ]; then
  $PY scripts/intermediate/wandb_watch.py --log "$PWD/logs/b3-finetune-1gpu-$SLURM_JOB_ID.out" --run-dir "$RUN" --name "$NAME" &
  WATCH=$!
else
  echo "W&B off: no key in the shared wandb.env or in .env"
fi
(cd "$KEV_HOME/kev" && $PY -m kev.train "${ARGS[@]}")
if [ -n "$WATCH" ]; then wait $WATCH || true; fi  # a W&B problem must not stop the timing table
$PY scripts/step_times.py "$RUN" --per-step 8
