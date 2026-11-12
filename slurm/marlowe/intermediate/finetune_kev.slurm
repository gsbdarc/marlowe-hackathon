#!/bin/bash
#SBATCH -J i3-finetune-1gpu
#SBATCH --account=marlowe-c001
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:40:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu

# Intermediate I3: the I2 fine-tune on one H100, to compare its speed with the Yens. Like I2, it trains for about 10
# minutes, with the settings you give it, then prints the time per step and, as I2 did, scores the new adapter on the
# 2,000 validation and 1,000 test filings (EVAL= skips that). Use the settings
# of your I2 job:
#   sbatch slurm/marlowe/intermediate/finetune_kev.slurm             # I2's defaults
#   LR=2e-4 sbatch slurm/marlowe/intermediate/finetune_kev.slurm     # or whatever your I2 job set
# The run is $WORK/runs/i3/<jobid>.
set -euo pipefail
module load slurm mps                  # mps avoids CUDA_ERROR_MPS_CONNECTION_FAILED (Marlowe docs)
source env/marlowe.sh
INIT=${INIT:-kev} RANK=${RANK:-16} RECORDS_PER_STEP=${RECORDS_PER_STEP:-8} WEIGHTS=${WEIGHTS:-fp32}
LR=${LR:-$([ "$INIT" = scratch ] && echo 2e-4 || echo 2e-5)}
EVAL=${EVAL-valid test} ID=$SLURM_JOB_ID EXERCISE=i3   # EVAL= (empty) skips scoring
if [ "$INIT" = kev ] && [ "$RANK" != 16 ]; then echo "Kev-4B's adapter has rank 16; other ranks need INIT=scratch" >&2; exit 1; fi
RUN=$WORK/runs/i3/$SLURM_JOB_ID
mkdir -p logs "$WORK/runs/i3"
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total --format=csv -l 5 > "logs/gpu-$SLURM_JOB_ID.csv" &
GPUMON=$!; trap 'kill $GPUMON 2>/dev/null || true' EXIT

# This exercise's project in the room's W&B team. The team's key is in $SHARE/wandb.env. A .env at the top of your
# clone (git ignores it) overrides it, for a key of your own.
export WANDB_PROJECT=${WANDB_PROJECT:-exercise-3-marlowe} WANDB_ENTITY=${WANDB_ENTITY:-Marlowe-Hackathon}
export WANDB_DIR=$WORK WANDB_CACHE_DIR=$XDG_CACHE_HOME/wandb WANDB_CONFIG_DIR=$XDG_CACHE_HOME/wandb-config
for f in "$SHARE/wandb.env" .env; do if [ -r "$f" ]; then set -a; source "$f"; set +a; fi; done
GPU=$(nvidia-smi --query-gpu=name --format=csv,noheader -i 0 | awk '{print tolower($2)}')
# Filings to train on: about 10 minutes, as in I2 (1.08 s each on an A40, 0.31 s on an H200, 0.49 s on an H100). On
# your first Marlowe run; later runs reuse the GPU kernels it compiled ($XDG_CACHE_HOME/triton) and train for about
# 7.5 minutes.
FILINGS=${FILINGS:-1216}
NAME=$USER-$GPU-$([ "$INIT" = scratch ] && echo "scratch-r$RANK" || echo kev)-lr$LR-rps$RECORDS_PER_STEP-$WEIGHTS

ARGS=(--data "$WORK/data/train.jsonl" --base Qwen/Qwen3.5-4B-Base --base_revision 1001bb4d826a52d1f399e183466143f4da7b741b
      --device cuda --dtype bf16 --weights_dtype "$WEIGHTS" --checkpointing 1 --max_state 2048 --seed 0
      --lora "$RANK" --lr "$LR" --batch 1 --accum "$RECORDS_PER_STEP" --max_steps $((FILINGS / RECORDS_PER_STEP)) --out "$RUN")
if [ "$INIT" = kev ]; then ARGS+=(--init_from jaredpalmer/kev-4b@v1.0); fi
WATCH=
WB=
if [ -n "${WANDB_API_KEY:-}" ] || [ "${WANDB_MODE:-}" = offline ]; then
  WB=1                                 # one W&B run for the job: the training curve, then the scores
  export WANDB_RUN_ID=$(python3 -c 'import uuid; print(uuid.uuid4().hex[:12])') WANDB_JOB_TYPE=train
  $PY scripts/intermediate/wandb_watch.py --log "$PWD/logs/i3-finetune-1gpu-$SLURM_JOB_ID.out" --run-dir "$RUN" --name "$NAME" &
  WATCH=$!
else
  echo "W&B off: no WANDB_API_KEY in $SHARE/wandb.env or .env"
fi
(cd "$KEV_HOME/kev" && $PY -m kev.train "${ARGS[@]}")
if [ -n "$WATCH" ]; then wait $WATCH; fi
$PY scripts/step_times.py "$RUN" --per-step "$RECORDS_PER_STEP"
source slurm/marlowe/intermediate/score_run.sh
