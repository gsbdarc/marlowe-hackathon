#!/bin/bash -l
#SBATCH -J adv-a1-kev27b
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_MODEL:H200
#SBATCH -c 4
#SBATCH --mem=16G
#SBATCH -t 01:00:00
#SBATCH -o logs/%x-%j.out

# A1: serve Kev-27B on one H200 and score it on the 1,000 test filings before any training. Its weights are 51 GB,
# so it needs an H200 (141 GB); an A40 (48 GB) is too small. Run from the repository root:
#   sbatch slurm/yens/advanced/a1_score_kev27b.slurm
# Results go to $WORK/results/kev-27b-zeroshot.jsonl; the scores print at the end of the log.
set -euo pipefail
source env/yens.sh
MODEL=jaredpalmer/kev-27b@af0e6d551bdc2cc724f3e9d7a8bee1cd4fb8f7bf   # pinned, so everyone scores the same weights
OUT=$WORK/results/kev-27b-zeroshot.jsonl
mkdir -p logs "$WORK/results"

# Start a Kev server on this GPU, on a free port, in the background
PORT=$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
(cd "$KEV_HOME/kev" && exec .venv/bin/python -m kev.serve --run "$MODEL" --port "$PORT") > "logs/kev-server-$SLURM_JOB_ID.log" 2>&1 &
SERVER=$!; trap 'kill $SERVER 2>/dev/null || true' EXIT

# Wait for the model to load (the first run also downloads the weights)
for i in $(seq 1 360); do
  curl -sf "http://127.0.0.1:$PORT/v1/models" > /dev/null && break
  kill -0 $SERVER 2>/dev/null || { echo "Kev server stopped; see logs/kev-server-$SLURM_JOB_ID.log" >&2; exit 1; }
  sleep 5
done
curl -sf "http://127.0.0.1:$PORT/v1/models" > /dev/null || { echo "Kev server not ready after 30 minutes" >&2; exit 1; }
echo "serving $MODEL on $(hostname): $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader -i 0)"

# Label the test filings, then score the answers against Jev's
$PY scripts/label.py --url "http://127.0.0.1:$PORT" --data "$WORK/data/test1000.jsonl" --out "$OUT"
$PY scripts/score.py "$OUT"
