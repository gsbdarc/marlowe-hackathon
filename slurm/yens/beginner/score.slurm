#!/bin/bash -l
#SBATCH -J ceo-score
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_MODEL:A40
#SBATCH -c 8
#SBATCH --mem=32G
#SBATCH -t 00:30:00
#SBATCH -o logs/%x-%j.out

# Beginner B1: serve Kev-4B as released on one GPU (an A40), send it the 1,000 test filings, score its answers
# against Jev's, and log the run to the room's Weights & Biases board. There is nothing to choose: submit it from the
# top of your clone and watch the log.
#   sbatch --reservation=hackathon slurm/yens/beginner/score.slurm
#   sbatch --reservation=hackathon -C GPU_MODEL:H200 slurm/yens/beginner/score.slurm     # B1's challenge: the same job on an H200
# (An option given to sbatch on the command line overrides the same #SBATCH line in this file.)
# It reads the shared, read-only test filings the instructors prepared ($CLASS_DATA), so there is no data to build
# first. The answers go to $WORK/results/b1/<jobid>.jsonl and the scores to <jobid>_scores.json next to them.
set -euo pipefail
source scripts/beginner/yens.sh
OUT=$WORK/results/b1/$SLURM_JOB_ID.jsonl
mkdir -p logs "$WORK/results/b1"
# Record the GPU's use and memory every 5 seconds, so you can see how busy it was.
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total --format=csv -l 5 > "logs/gpu-$SLURM_JOB_ID.csv" &

# The beginner board in the room's W&B team. scripts/beginner/wandb_key.sh finds the team's key: the hackathon's shared
# wandb.env, or a line WANDB_API_KEY=... in .env at the top of the repo (git ignores it). Without a key the job still
# runs; it just does not reach the board.
export WANDB_PROJECT="${WANDB_PROJECT:-Beginner Exercise 1}"
export WANDB_ENTITY=${WANDB_ENTITY:-Marlowe-Hackathon}
export WANDB_DIR=$WORK WANDB_CACHE_DIR=$XDG_CACHE_HOME/wandb WANDB_CONFIG_DIR=$XDG_CACHE_HOME/wandb-config
GPU=$(nvidia-smi --query-gpu=name --format=csv,noheader -i 0 | awk '{print tolower($2)}')
NAME=$USER-$GPU-$SLURM_JOB_ID
WB=()
source scripts/beginner/wandb_key.sh                 # the room's key: the shared wandb.env, or your .env
if [ -n "${WANDB_API_KEY:-}" ] || [ "${WANDB_MODE:-}" = offline ]; then WB=(--wandb "$NAME"); else echo "W&B off: no key in the shared wandb.env or in .env"; fi

START=$SECONDS
PORT=$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
(cd "$KEV_HOME/kev" && exec .venv/bin/python -m kev.serve --run jaredpalmer/kev-4b@v1.0 --port "$PORT") > "logs/kev-server-$SLURM_JOB_ID.log" 2>&1 &
SERVER=$!; trap 'kill $SERVER 2>/dev/null || true' EXIT
for i in $(seq 1 120); do                            # wait up to 10 minutes for the model to load
  curl -sf "http://127.0.0.1:$PORT/v1/models" > /dev/null && break
  kill -0 $SERVER 2>/dev/null || { echo "Kev server stopped; see logs/kev-server-$SLURM_JOB_ID.log" >&2; exit 1; }
  sleep 5
done
curl -sf "http://127.0.0.1:$PORT/v1/models" > /dev/null || { echo "Kev server not ready after 10 minutes" >&2; exit 1; }
echo "$NAME: Kev-4B loaded in $((SECONDS - START)) s on $(hostname), $(nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader -i 0)"
LABEL=($PY scripts/intermediate/label.py --url "http://127.0.0.1:$PORT" --data "$CLASS_DATA/test1000.jsonl" --out "$OUT" --concurrency 16)
# If W&B refuses the key, label again without it: label.py skips the filings it already answered, so nothing is lost.
"${LABEL[@]}" "${WB[@]}" || { [ ${#WB[@]} -gt 0 ] && echo "W&B failed (check the key in .env); labeling without it" && WB=() && "${LABEL[@]}"; }
$PY scripts/intermediate/score.py "$OUT" --sample "$CLASS_DATA/test1000.parquet" ${WB:+--wandb --wandb-prefix test/} \
  || $PY scripts/intermediate/score.py "$OUT" --sample "$CLASS_DATA/test1000.parquet"
