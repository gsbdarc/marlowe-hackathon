#!/bin/bash
#SBATCH -J score-test
#SBATCH --account=marlowe-c001
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=128G
#SBATCH --time=01:30:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu

# Score several runs on the same 1,000 test filings (I1's test1000), one after another on one H100, and print them in
# one table: the way to compare training methods (LoRA on 1, 4 or 8 GPUs, full fine-tune on 1 or 8) on equal terms.
#   RUNS="kev-4b=jaredpalmer/kev-4b@v1.0 lora-1gpu=$WORK/runs/lora-ddp/<jobid> full-8gpu=$WORK/runs/i4/<jobid>" \
#     sbatch slurm/marlowe/intermediate/score_test.slurm
# Each entry is <name>=<run>: a released run, or a run folder with head.pt. EVAL=valid scores the 2,000 validation
# filings instead (EVAL="valid test" both). A run already labeled on a sample is not labeled again: delete
# $WORK/results/compare/<name>-<sample>.jsonl to redo it.
# First time on Marlowe: builds valid.jsonl and test1000.jsonl (+ .parquet) in $WORK/data with make_kev_data.py
# (seeded: the same filings as on the Yens), leaving train.jsonl as it is.
set -euo pipefail
module load slurm mps                  # mps avoids CUDA_ERROR_MPS_CONNECTION_FAILED (Marlowe docs)
source env/marlowe.sh
RUNS=${RUNS:?set RUNS=\"<name>=<run> ...\"} EVAL=${EVAL:-test}
OUT=$WORK/results/compare
mkdir -p logs "$OUT"
for E in $EVAL; do case $E in valid|test) ;; *) echo "EVAL is valid, test or both (\"valid test\")" >&2; exit 1 ;; esac; done
for R in $RUNS; do
  case $R in *=*) ;; *) echo "RUNS entries are <name>=<run>: $R" >&2; exit 1 ;; esac
  case ${R#*=} in /*) [ -f "${R#*=}/head.pt" ] || { echo "no trained run in ${R#*=}" >&2; exit 1; } ;; esac   # kev.serve would fall back to a toy model
done
if [ ! -f "$WORK/data/test1000.parquet" ] || [ ! -f "$WORK/data/valid.parquet" ]; then
  echo "building the validation and test samples in $WORK/data"
  TMP=$WORK/data/.build-$SLURM_JOB_ID
  $PY scripts/make_kev_data.py --out "$TMP"
  mv "$TMP"/valid.jsonl "$TMP"/valid.parquet "$TMP"/test1000.jsonl "$TMP"/test1000.parquet "$WORK/data/"
  rm -rf "$TMP"
fi
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total --format=csv -l 5 > "logs/gpu-$SLURM_JOB_ID.csv" &
GPUMON=$! SERVER=
trap 'kill $GPUMON $SERVER 2>/dev/null || true' EXIT

for R in $RUNS; do
  NAME=${R%%=*} RUN=${R#*=}
  TODO=
  for E in $EVAL; do [ -f "$OUT/$NAME-$E.jsonl" ] || TODO=1; done
  if [ -z "$TODO" ]; then echo "$NAME: already labeled"; continue; fi
  START=$SECONDS
  PORT=$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
  (cd "$KEV_HOME/kev" && exec .venv/bin/python -m kev.serve --run "$RUN" --port "$PORT") > "logs/kev-server-$SLURM_JOB_ID-$NAME.log" 2>&1 &
  SERVER=$!
  for i in $(seq 1 120); do            # wait up to 10 minutes for the model to load
    curl -sf "http://127.0.0.1:$PORT/v1/models" > /dev/null && break
    kill -0 $SERVER 2>/dev/null || { echo "Kev server stopped; see logs/kev-server-$SLURM_JOB_ID-$NAME.log" >&2; exit 1; }
    sleep 5
  done
  curl -sf "http://127.0.0.1:$PORT/v1/models" > /dev/null || { echo "Kev server not ready after 10 minutes" >&2; exit 1; }
  echo "$NAME: $RUN loaded in $((SECONDS - START)) s"
  for E in $EVAL; do
    case $E in valid) DATA=$WORK/data/valid.jsonl ;; test) DATA=$WORK/data/test1000.jsonl ;; esac
    [ -f "$OUT/$NAME-$E.jsonl" ] && continue
    $PY scripts/intermediate/label.py --url "http://127.0.0.1:$PORT" --data "$DATA" --out "$OUT/$NAME-$E.part.jsonl" --concurrency 16
    for f in "$OUT/$NAME-$E.part"*; do mv "$f" "${f/.part/}"; done   # the answers and their _summary.json, once complete
  done
  kill $SERVER; wait $SERVER 2>/dev/null || true; SERVER=
done

for E in $EVAL; do
  case $E in valid) SAMPLE=$WORK/data/valid.parquet ;; test) SAMPLE=$WORK/data/test1000.parquet ;; esac
  FILES=()
  for R in $RUNS; do FILES+=("$OUT/${R%%=*}-$E.jsonl"); done
  echo; echo "=== $E: $(basename "$SAMPLE") ==="
  $PY scripts/intermediate/score.py "${FILES[@]}" --sample "$SAMPLE"
done
