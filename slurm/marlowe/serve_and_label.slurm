#!/bin/bash
#SBATCH -J ceo-label
#SBATCH --account=marlowe-m000106
#SBATCH --partition=preempt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=logs/%x-%j.out

# Serve a Kev model on one H100 and label the test sample with it, then score against Jev.
#   sbatch slurm/marlowe/serve_and_label.slurm $WORK/runs/cp4-8gpu cp4
set -euo pipefail
module load slurm mps
source env/marlowe.sh
RUN=${1:-jaredpalmer/kev-4b@v1.0}
NAME=${2:-kev-4b-zeroshot}
FILINGS=${3:-$WORK/data/test1000.jsonl}
mkdir -p logs "$WORK/results"
PORT=$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
(cd "$KEV_HOME/kev" && exec .venv/bin/python -m kev.serve --run "$RUN" --port "$PORT") > "logs/kev-server-$SLURM_JOB_ID.log" 2>&1 &
SERVER=$!; trap 'kill $SERVER 2>/dev/null || true' EXIT
for i in $(seq 1 360); do
  curl -sf "http://127.0.0.1:$PORT/v1/models" > /dev/null && break
  kill -0 $SERVER 2>/dev/null || { echo "Kev server stopped; see logs/kev-server-$SLURM_JOB_ID.log" >&2; exit 1; }
  sleep 5
done
curl -sf "http://127.0.0.1:$PORT/v1/models" > /dev/null || { echo "Kev server not ready after 30 minutes" >&2; exit 1; }
$PY scripts/label.py --url "http://127.0.0.1:$PORT" --data "$FILINGS" --out "$WORK/results/$NAME.jsonl"
if [ "$FILINGS" = "$WORK/data/test1000.jsonl" ]; then $PY scripts/score.py "$WORK/results/$NAME.jsonl"; fi
