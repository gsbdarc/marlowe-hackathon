#!/bin/bash -l
#SBATCH -J ceo-finetune
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_MODEL:A40
#SBATCH -c 8
#SBATCH --mem=32G
#SBATCH -t 00:45:00
#SBATCH -o logs/%x-%j.out

# Beginner B2: continue training Kev-4B's adapter for about 10 minutes on one GPU (an A40), then score the result,
# first on the 2,000 validation filings (to choose the learning rate by) and then on the same 1,000 test filings B1
# used (to report). The one decision is the learning rate; with no setting the job uses the default, 2e-5.
#   sbatch --reservation=hackathon slurm/yens/beginner/finetune.slurm                  # the default, 2e-5
#   LR=2e-6 sbatch --reservation=hackathon slurm/yens/beginner/finetune.slurm          # ten times smaller
#   LR=2e-4 sbatch --reservation=hackathon slurm/yens/beginner/finetune.slurm          # ten times larger
#   FILINGS=1024 sbatch --reservation=hackathon slurm/yens/beginner/finetune.slurm     # B2's challenge: twice the training
# It reads the shared, read-only training, validation and test filings ($CLASS_DATA), so there is no data to build
# first. The trained adapter goes to $WORK/runs/b2/<jobid>, the scores to $WORK/results/b2/<jobid>-{valid,test}_scores.json.
set -euo pipefail
source scripts/beginner/yens.sh
mkdir -p logs "$WORK/runs/b2" "$WORK/results/b2"
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total --format=csv -l 5 > "logs/gpu-$SLURM_JOB_ID.csv" &
GPUMON=$!

# The beginner board in the room's W&B team. scripts/beginner/wandb_key.sh finds the team's key: the hackathon's shared
# wandb.env, or a line WANDB_API_KEY=... in .env at the top of the repo (git ignores it). Without a key the job still
# runs; it just does not reach the board.
export WANDB_PROJECT="${WANDB_PROJECT:-Beginner Exercise 2}" WANDB_ENTITY=${WANDB_ENTITY:-Marlowe-Hackathon}
export WANDB_DIR=$WORK WANDB_CACHE_DIR=$XDG_CACHE_HOME/wandb WANDB_CONFIG_DIR=$XDG_CACHE_HOME/wandb-config
source scripts/beginner/wandb_key.sh                 # the room's key: the shared wandb.env, or your .env
WB=
if [ -n "${WANDB_API_KEY:-}" ] || [ "${WANDB_MODE:-}" = offline ]; then WB=1; else echo "W&B off: no key in the shared wandb.env or in .env"; fi
GPU=$(nvidia-smi --query-gpu=name --format=csv,noheader -i 0 | awk '{print tolower($2)}')
# Filings to train on: about 10 minutes on an A40 (1.08 s each), the same budget as the intermediate track.
FILINGS=${FILINGS:-512}
LR=${LR:-2e-5}                                       # how far each update moves the trained numbers
RUN=$WORK/runs/b2/$SLURM_JOB_ID
NAME=$USER-$GPU-lr$LR-f$FILINGS                  # wandb_watch.py adds the job ID

# Continue Kev-4B's adapter: the Qwen 4B backbone stays frozen, and Kev-4B's LoRA adapter and answer head train on.
ARGS=(--data "$CLASS_DATA/train.jsonl" --init_from jaredpalmer/kev-4b@v1.0
      --base Qwen/Qwen3.5-4B-Base --base_revision 1001bb4d826a52d1f399e183466143f4da7b741b
      --device cuda --dtype bf16 --weights_dtype fp32 --checkpointing 1 --max_state 2048 --seed 0
      --lora 16 --lr "$LR" --batch 1 --accum 8 --max_steps $((FILINGS / 8)) --out "$RUN")
if [ -n "$WB" ]; then                                # one W&B run for the job: the training curve, then the scores
  export WANDB_RUN_ID=$(python3 -c 'import uuid; print(uuid.uuid4().hex[:12])') WANDB_JOB_TYPE=train
  $PY scripts/intermediate/wandb_watch.py --log "$PWD/logs/ceo-finetune-$SLURM_JOB_ID.out" --run-dir "$RUN" --name "$NAME" &
  WATCH=$!
fi
(cd "$KEV_HOME/kev" && $PY -m kev.train "${ARGS[@]}")
if [ -n "$WB" ]; then wait $WATCH || true; fi      # a W&B problem must not stop the scoring
$PY scripts/step_times.py "$RUN" --per-step 8

# Serve the adapter you just trained and score it on the 1,000 test filings.
START=$SECONDS
PORT=$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
(cd "$KEV_HOME/kev" && exec .venv/bin/python -m kev.serve --run "$RUN" --port "$PORT") > "logs/kev-server-$SLURM_JOB_ID.log" 2>&1 &
SERVER=$!; trap 'kill $SERVER $GPUMON 2>/dev/null || true' EXIT
for i in $(seq 1 120); do                            # wait up to 10 minutes for the model to load
  curl -sf "http://127.0.0.1:$PORT/v1/models" > /dev/null && break
  kill -0 $SERVER 2>/dev/null || { echo "Kev server stopped; see logs/kev-server-$SLURM_JOB_ID.log" >&2; exit 1; }
  sleep 5
done
curl -sf "http://127.0.0.1:$PORT/v1/models" > /dev/null || { echo "Kev server not ready after 10 minutes" >&2; exit 1; }
echo "$RUN loaded in $((SECONDS - START)) s on $(hostname)"
# Validation first: the 2,000 filings the room compares learning rates on. Then test: the same 1,000 filings B1 used,
# so the before/after is an exact comparison, and the number you report once the choice is made.
for E in valid test; do
  case $E in valid) IN=valid SAMPLE=valid ;; test) IN=test1000 SAMPLE=test1000 ;; esac
  echo; echo "== $E: scoring on $CLASS_DATA/$IN.jsonl"
  OUT=$WORK/results/b2/$SLURM_JOB_ID-$E.jsonl
  $PY scripts/intermediate/label.py --url "http://127.0.0.1:$PORT" --data "$CLASS_DATA/$IN.jsonl" --out "$OUT" --concurrency 16
  $PY scripts/intermediate/score.py "$OUT" --sample "$CLASS_DATA/$SAMPLE.parquet" ${WB:+--wandb --wandb-prefix $E/} \
    || $PY scripts/intermediate/score.py "$OUT" --sample "$CLASS_DATA/$SAMPLE.parquet"   # again without W&B
done
