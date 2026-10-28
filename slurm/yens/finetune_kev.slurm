#!/bin/bash -l
#SBATCH -J ceo-finetune
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_MODEL:A40
#SBATCH -c 8
#SBATCH --mem=32G
#SBATCH -t 00:45:00
#SBATCH -o logs/%x-%j.out

# Beginner exercise 2: fine-tune Kev-4B's LoRA adapter for about 10 minutes on one GPU, score the result on the 2,000
# validation filings, and log the run to the room's Weights & Biases project. Change one setting at a time and compare:
#   sbatch slurm/yens/finetune_kev.slurm                       # continue Kev-4B's adapter: lr 2e-5, 8 filings a step, fp32
#   LR=2e-4 sbatch slurm/yens/finetune_kev.slurm               # the learning rate
#   RECORDS_PER_STEP=32 sbatch slurm/yens/finetune_kev.slurm   # filings per optimizer step (the same FILINGS in total)
#   WEIGHTS=bf16 sbatch slurm/yens/finetune_kev.slurm          # the frozen backbone in bf16 instead of fp32
#   INIT=scratch RANK=4 sbatch slurm/yens/finetune_kev.slurm   # a new adapter (rank 4, 16 or 64) on the base model
#   sbatch -C GPU_MODEL:H200 slurm/yens/finetune_kev.slurm     # an H200 instead of an A40
# Score without training: RUN=jaredpalmer/kev-4b@v1.0 is the baseline, RUN=$WORK/runs/b2/<jobid> a run you trained.
# Once you have chosen your settings on validation, score that one run on the test filings: EVAL=test RUN=...
set -euo pipefail
source env/yens.sh
INIT=${INIT:-kev} RANK=${RANK:-16} RECORDS_PER_STEP=${RECORDS_PER_STEP:-8} WEIGHTS=${WEIGHTS:-fp32}
LR=${LR:-$([ "$INIT" = scratch ] && echo 2e-4 || echo 2e-5)}
FILINGS=${FILINGS:-512}                              # filings to train on: about 10 minutes on an A40 (1.1 s each)
EVAL=${EVAL:-valid} RUN=${RUN:-}
case $EVAL in
  valid) DATA=$WORK/data/valid.jsonl SAMPLE=$WORK/data/valid.parquet ;;
  test) DATA=$WORK/data/test1000.jsonl SAMPLE=$WORK/data/test1000.parquet ;;
  *) echo "EVAL is valid or test" >&2; exit 1 ;;
esac
if [ "$INIT" = kev ] && [ "$RANK" != 16 ]; then echo "Kev-4B's adapter has rank 16; other ranks need INIT=scratch" >&2; exit 1; fi
case $RUN in /*) [ -f "$RUN/head.pt" ] || { echo "no trained run in $RUN" >&2; exit 1; } ;; esac   # kev.serve would fall back to a toy model
mkdir -p logs "$WORK/runs/b2" "$WORK/results/b2"
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total --format=csv -l 5 > "logs/gpu-$SLURM_JOB_ID.csv" &

# The room's W&B project. The shared key is a line WANDB_API_KEY=... in .env at the top of the repo, which git ignores.
export WANDB_PROJECT=${WANDB_PROJECT:-marlowe-hackathon-finetune} WANDB_ENTITY=${WANDB_ENTITY:-darc}
export WANDB_DIR=$WORK WANDB_CACHE_DIR=$XDG_CACHE_HOME/wandb WANDB_CONFIG_DIR=$XDG_CACHE_HOME/wandb-config
if [ -r .env ]; then set -a; source ./.env; set +a; fi
WB=
if [ -n "${WANDB_API_KEY:-}" ] || [ "${WANDB_MODE:-}" = offline ]; then WB=1; else echo "W&B off: no WANDB_API_KEY in .env"; fi
GPU=$(nvidia-smi --query-gpu=name --format=csv,noheader -i 0 | awk '{print tolower($2)}')

LABEL=()
if [ -z "$RUN" ]; then                               # train, then score the new adapter
  RUN=$WORK/runs/b2/$SLURM_JOB_ID
  NAME=$USER-$GPU-$([ "$INIT" = scratch ] && echo "scratch-r$RANK" || echo kev)-lr$LR-rps$RECORDS_PER_STEP-$WEIGHTS
  ARGS=(--data "$WORK/data/train.jsonl" --base Qwen/Qwen3.5-4B-Base --base_revision 1001bb4d826a52d1f399e183466143f4da7b741b
        --device cuda --dtype bf16 --weights_dtype "$WEIGHTS" --checkpointing 1 --max_state 2048 --seed 0
        --lora "$RANK" --lr "$LR" --batch 1 --accum "$RECORDS_PER_STEP" --max_steps $((FILINGS / RECORDS_PER_STEP)) --out "$RUN")
  if [ "$INIT" = kev ]; then ARGS+=(--init_from jaredpalmer/kev-4b@v1.0); fi
  if [ -n "$WB" ]; then                              # one W&B run for the job: the training curve, then the scores
    export WANDB_RUN_ID=$(python3 -c 'import uuid; print(uuid.uuid4().hex[:12])') WANDB_JOB_TYPE=train
    $PY scripts/wandb_watch.py --log "$PWD/logs/ceo-finetune-$SLURM_JOB_ID.out" --run-dir "$RUN" --name "$NAME" &
    WATCH=$!
  fi
  (cd "$KEV_HOME/kev" && $PY -m kev.train "${ARGS[@]}")
  if [ -n "$WB" ]; then wait $WATCH; fi
  $PY scripts/step_times.py "$RUN" --per-step "$RECORDS_PER_STEP"
else                                                 # score a released or trained run, as its own W&B run
  export WANDB_JOB_TYPE=$EVAL
  if [ -n "$WB" ]; then LABEL=(--wandb "$USER-$GPU-$(basename "$RUN")-$EVAL-$SLURM_JOB_ID"); fi
fi

START=$SECONDS
PORT=$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
(cd "$KEV_HOME/kev" && exec .venv/bin/python -m kev.serve --run "$RUN" --port "$PORT") > "logs/kev-server-$SLURM_JOB_ID.log" 2>&1 &
SERVER=$!; trap 'kill $SERVER 2>/dev/null || true' EXIT
for i in $(seq 1 120); do                            # wait up to 10 minutes for the model to load
  curl -sf "http://127.0.0.1:$PORT/v1/models" > /dev/null && break
  kill -0 $SERVER 2>/dev/null || { echo "Kev server stopped; see logs/kev-server-$SLURM_JOB_ID.log" >&2; exit 1; }
  sleep 5
done
curl -sf "http://127.0.0.1:$PORT/v1/models" > /dev/null || { echo "Kev server not ready after 10 minutes" >&2; exit 1; }
echo "$RUN loaded in $((SECONDS - START)) s on $(hostname); scoring the $EVAL filings"
OUT=$WORK/results/b2/$SLURM_JOB_ID-$EVAL.jsonl
$PY scripts/label.py --url "http://127.0.0.1:$PORT" --data "$DATA" --out "$OUT" --concurrency 16 "${LABEL[@]}"
$PY scripts/score.py "$OUT" --sample "$SAMPLE" ${WB:+--wandb}
