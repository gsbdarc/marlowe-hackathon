#!/bin/bash -l
#SBATCH -J ceo-score
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_MODEL:A40
#SBATCH -c 8
#SBATCH --mem=32G
#SBATCH -t 00:30:00
#SBATCH -o logs/%x-%j.out

# Beginner exercise 1: serve Kev-4B as released on one GPU, send it the 1,000 test filings, score its answers against
# Jev's, and log the run to the room's Weights & Biases project. Change one setting at a time and compare:
#   sbatch slurm/yens/beginner/score_kev.slurm                     # an A40, 16 filings at a time, bf16, fused kernels
#   sbatch -C GPU_MODEL:H200 slurm/yens/beginner/score_kev.slurm   # an H200 instead of an A40
#   CONCURRENCY=64 sbatch slurm/yens/beginner/score_kev.slurm      # filings in flight, 1 to 64 (the server's largest batch)
#   DTYPE=fp32 sbatch slurm/yens/beginner/score_kev.slurm          # 32-bit numbers instead of 16-bit (bf16)
#   FUSED=0 sbatch slurm/yens/beginner/score_kev.slurm             # without Kev's fused kernels (transformers' own layer code)
# Every job labels all 1,000 filings afresh, into $WORK/results/b1/<jobid>.jsonl.
# Loading fp32 weights passes through host memory, hence 32 GB (the gpu partition allows 4,000 MB per CPU).
set -euo pipefail
source env/yens.sh
CONCURRENCY=${CONCURRENCY:-16}
export KEV_DTYPE=${DTYPE:-bf16} KEV_FUSED=${FUSED:-1}
OUT=$WORK/results/b1/$SLURM_JOB_ID.jsonl
mkdir -p logs "$WORK/results/b1"
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total --format=csv -l 5 > "logs/gpu-$SLURM_JOB_ID.csv" &

# This exercise's project in the room's W&B team. The team's key is a line WANDB_API_KEY=... in .env at the top of the
# repo, which git ignores.
export WANDB_PROJECT=${WANDB_PROJECT:-exercise-1-inference}
export WANDB_ENTITY=${WANDB_ENTITY:-Marlowe-Hackathon}
export WANDB_DIR=$WORK WANDB_CACHE_DIR=$XDG_CACHE_HOME/wandb WANDB_CONFIG_DIR=$XDG_CACHE_HOME/wandb-config
GPU=$(nvidia-smi --query-gpu=name --format=csv,noheader -i 0 | awk '{print tolower($2)}')
NAME=$USER-$GPU-c$CONCURRENCY-$KEV_DTYPE$([ "$KEV_FUSED" = 0 ] && echo -nofused || true)-$SLURM_JOB_ID
WB=()
if [ -r .env ]; then set -a; source ./.env; set +a; fi
if [ -n "${WANDB_API_KEY:-}" ] || [ "${WANDB_MODE:-}" = offline ]; then WB=(--wandb "$NAME"); else echo "W&B off: no WANDB_API_KEY in .env"; fi

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
$PY scripts/beginner/label.py --url "http://127.0.0.1:$PORT" --data "$WORK/data/test1000.jsonl" --out "$OUT" --concurrency "$CONCURRENCY" "${WB[@]}"
$PY scripts/beginner/score.py "$OUT" ${WB:+--wandb --wandb-prefix test/}
