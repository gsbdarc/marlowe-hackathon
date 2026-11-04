#!/bin/bash
#SBATCH -J b3-finetune-1gpu
#SBATCH --account=marlowe-m000106
#SBATCH --partition=preempt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu

# Beginner B3: the B2 fine-tune on one H100, to compare its speed with the Yens. It trains on the same 512 filings as
# a B2 run on an A40, with the settings you give it, then prints the time per step. It does not score the model. Use
# the settings of your B2 job:
#   sbatch slurm/marlowe/beginner/finetune_kev.slurm             # B2's defaults
#   LR=2e-4 sbatch slurm/marlowe/beginner/finetune_kev.slurm     # or whatever your B2 job set
# The run is $WORK/runs/b3/<jobid>.
set -euo pipefail
module load slurm mps                  # mps avoids CUDA_ERROR_MPS_CONNECTION_FAILED (Marlowe docs)
source env/marlowe.sh
INIT=${INIT:-kev} RANK=${RANK:-16} RECORDS_PER_STEP=${RECORDS_PER_STEP:-8} WEIGHTS=${WEIGHTS:-fp32}
LR=${LR:-$([ "$INIT" = scratch ] && echo 2e-4 || echo 2e-5)}
FILINGS=${FILINGS:-512}                # a B2 run's filings on an A40, so the two runs do the same work
if [ "$INIT" = kev ] && [ "$RANK" != 16 ]; then echo "Kev-4B's adapter has rank 16; other ranks need INIT=scratch" >&2; exit 1; fi
RUN=$WORK/runs/b3/$SLURM_JOB_ID
mkdir -p logs "$WORK/runs/b3"
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total --format=csv -l 5 > "logs/gpu-$SLURM_JOB_ID.csv" &
GPUMON=$!; trap 'kill $GPUMON 2>/dev/null || true' EXIT

# This exercise's project in the room's W&B team. The team's key is a line WANDB_API_KEY=... in .env at the top of the
# repo, which git ignores.
export WANDB_PROJECT=${WANDB_PROJECT:-exercise-3-marlowe} WANDB_ENTITY=${WANDB_ENTITY:-Marlowe-Hackathon}
export WANDB_DIR=$WORK WANDB_CACHE_DIR=$XDG_CACHE_HOME/wandb WANDB_CONFIG_DIR=$XDG_CACHE_HOME/wandb-config
if [ -r .env ]; then set -a; source ./.env; set +a; fi
GPU=$(nvidia-smi --query-gpu=name --format=csv,noheader -i 0 | awk '{print tolower($2)}')
NAME=$USER-$GPU-$([ "$INIT" = scratch ] && echo "scratch-r$RANK" || echo kev)-lr$LR-rps$RECORDS_PER_STEP-$WEIGHTS

ARGS=(--data "$WORK/data/train.jsonl" --base Qwen/Qwen3.5-4B-Base --base_revision 1001bb4d826a52d1f399e183466143f4da7b741b
      --device cuda --dtype bf16 --weights_dtype "$WEIGHTS" --checkpointing 1 --max_state 2048 --seed 0
      --lora "$RANK" --lr "$LR" --batch 1 --accum "$RECORDS_PER_STEP" --max_steps $((FILINGS / RECORDS_PER_STEP)) --out "$RUN")
if [ "$INIT" = kev ]; then ARGS+=(--init_from jaredpalmer/kev-4b@v1.0); fi
WATCH=
if [ -n "${WANDB_API_KEY:-}" ] || [ "${WANDB_MODE:-}" = offline ]; then
  $PY scripts/beginner/wandb_watch.py --log "$PWD/logs/b3-finetune-1gpu-$SLURM_JOB_ID.out" --run-dir "$RUN" --name "$NAME" &
  WATCH=$!
else
  echo "W&B off: no WANDB_API_KEY in .env"
fi
(cd "$KEV_HOME/kev" && $PY -m kev.train "${ARGS[@]}")
if [ -n "$WATCH" ]; then wait $WATCH; fi
$PY scripts/step_times.py "$RUN" --per-step "$RECORDS_PER_STEP"
