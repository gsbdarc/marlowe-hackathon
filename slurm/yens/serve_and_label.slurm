#!/bin/bash -l
#SBATCH -J ceo-label
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -c 4
#SBATCH --mem=16G
#SBATCH -t 02:00:00
#SBATCH -o logs/%x-%j.out

# Serve a Kev model on this GPU and label filings with it, then score against Jev.
#   sbatch slurm/yens/serve_and_label.slurm                                  # zero-shot Kev-4B on the test sample
#   sbatch slurm/yens/serve_and_label.slurm $WORK/runs/cp2-2gpu my-model     # your fine-tuned run
#   sbatch -C GPU_MODEL:H200 slurm/yens/serve_and_label.slurm $WORK/runs/cp2-2gpu my-model $WORK/data/all.jsonl
# Arguments: model (Hub id or run directory), a name for the results, the filings to label.
# The gpu partition allows at most 4,000 MB of memory per CPU; Kev-4B needs a 24 GB GPU or larger.
set -euo pipefail
source env/yens.sh
RUN=${1:-jaredpalmer/kev-4b@v1.0}
NAME=${2:-kev-4b-zeroshot}
FILINGS=${3:-$WORK/data/test1000.jsonl}
mkdir -p logs "$WORK/results"
PORT=$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
(cd "$KEV_HOME/kev" && exec .venv/bin/python -m kev.serve --run "$RUN" --port "$PORT") > "logs/kev-server-$SLURM_JOB_ID.log" 2>&1 &
SERVER=$!; trap 'kill $SERVER 2>/dev/null || true' EXIT
for i in $(seq 1 360); do                            # wait up to 30 minutes for the model to load
  curl -sf "http://127.0.0.1:$PORT/v1/models" > /dev/null && break
  kill -0 $SERVER 2>/dev/null || { echo "Kev server stopped; see logs/kev-server-$SLURM_JOB_ID.log" >&2; exit 1; }
  sleep 5
done
curl -sf "http://127.0.0.1:$PORT/v1/models" > /dev/null || { echo "Kev server not ready after 30 minutes" >&2; exit 1; }
echo "serving $RUN on $(hostname): $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader -i 0)"
$PY scripts/label.py --url "http://127.0.0.1:$PORT" --data "$FILINGS" --out "$WORK/results/$NAME.jsonl"
[ "$FILINGS" = "$WORK/data/test1000.jsonl" ] && $PY scripts/score.py "$WORK/results/$NAME.jsonl"
