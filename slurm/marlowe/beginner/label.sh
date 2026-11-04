# B5: label filings on every GPU of the job at once. One Kev server per GPU, each a separate program with its own copy
# of the model; the filings are split into one shard per GPU, and one label.py per shard sends its filings to its own
# server. Nothing passes between the GPUs. Sourced by label_1gpu.slurm and label_8gpu.slurm.
# Settings, set before sbatch:
#   RUN=jaredpalmer/kev-4b@v1.0   the model: Kev-4B as released, or a run of yours, e.g. RUN=$WORK/runs/b3/<jobid>
#   FILINGS=0                     filings to label: 0 for all 296,477, or the first N, in filing order from 2004
#   SHARDS=<GPUs>                 split the filings into this many shards; this job labels the first <GPUs> of them
# More nodes: a job array, one node per task, each labeling the next <GPUs> shards. Two nodes, 16 GPUs:
#   SHARDS=16 sbatch --array=0-1 slurm/marlowe/beginner/label_8gpu.slurm
#   CONCURRENCY=64                filings each label.py keeps in flight (64 is the most a Kev server batches at once)
set -euo pipefail
module load slurm mps                  # mps avoids CUDA_ERROR_MPS_CONNECTION_FAILED (Marlowe docs)
source env/marlowe.sh
RUN=${RUN:-jaredpalmer/kev-4b@v1.0} FILINGS=${FILINGS:-0} CONCURRENCY=${CONCURRENCY:-64}
export KEV_TRUNCATE_STATES=1           # a filing longer than Kev's 2,048 tokens: read its start instead of refusing it
GPUS=$(nvidia-smi -L | wc -l)
SHARDS=${SHARDS:-$GPUS}
FIRST=$(( ${SLURM_ARRAY_TASK_ID:-0} * GPUS ))  # this task's first shard: 0, or 8 for the second node of a job array
if [ $((FIRST + GPUS)) -gt "$SHARDS" ]; then echo "shards $FIRST to $((FIRST + GPUS - 1)) are past SHARDS=$SHARDS" >&2; exit 1; fi
OUT=$WORK/results/b5/${SLURM_ARRAY_JOB_ID:-$SLURM_JOB_ID}   # one folder for every task of a job array
mkdir -p logs "$OUT"
nvidia-smi --query-gpu=timestamp,index,name,utilization.gpu,memory.used,memory.total --format=csv -l 5 > "logs/gpu-$SLURM_JOB_ID.csv" &
PIDS=($!); trap 'kill "${PIDS[@]}" 2>/dev/null || true' EXIT

START=$SECONDS
PORTS=()
for g in $(seq 0 $((GPUS - 1))); do    # one server per GPU: CUDA_VISIBLE_DEVICES shows each only its own GPU
  PORT=$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
  (cd "$KEV_HOME/kev" && CUDA_VISIBLE_DEVICES=$g exec .venv/bin/python -m kev.serve --run "$RUN" --port "$PORT") \
    > "logs/kev-server-$SLURM_JOB_ID-gpu$g.log" 2>&1 &
  PIDS+=($!) PORTS+=("$PORT")
done
for g in "${!PORTS[@]}"; do            # wait up to 10 minutes for every server to load
  for i in $(seq 1 120); do
    curl -sf "http://127.0.0.1:${PORTS[$g]}/v1/models" > /dev/null && break
    kill -0 "${PIDS[$((g + 1))]}" 2>/dev/null || { echo "server on GPU $g stopped; see logs/kev-server-$SLURM_JOB_ID-gpu$g.log" >&2; exit 1; }
    sleep 5
  done
  curl -sf "http://127.0.0.1:${PORTS[$g]}/v1/models" > /dev/null || { echo "server on GPU $g not ready after 10 minutes" >&2; exit 1; }
done
LOAD=$((SECONDS - START))
echo "$GPUS Kev servers ready in $LOAD s on $(hostname): $RUN"

LABEL=()
for g in "${!PORTS[@]}"; do
  CUDA_VISIBLE_DEVICES=$g $PY scripts/beginner/label.py --url "http://127.0.0.1:${PORTS[$g]}" --data "$DATA/item502_v1.parquet" \
    --limit "$FILINGS" --shard $((FIRST + g)) --shards "$SHARDS" --concurrency "$CONCURRENCY" --out "$OUT/shard-$((FIRST + g)).jsonl" \
    > "$OUT/shard-$((FIRST + g)).log" 2>&1 &
  LABEL+=($!)
done
tail -f "$OUT/shard-$FIRST.log" &      # GPU 0's progress, as a sample of all of them
PIDS+=($!)
for p in "${LABEL[@]}"; do wait "$p"; done
echo "{\"task\": ${SLURM_ARRAY_TASK_ID:-0}, \"gpus\": $GPUS, \"shards\": $SHARDS, \"run\": \"$RUN\", \"load_seconds\": $LOAD, \"job_seconds\": $((SECONDS - START)), \"concurrency\": $CONCURRENCY}" > "$OUT/job-${SLURM_ARRAY_TASK_ID:-0}.json"
$PY scripts/beginner/shards.py "$OUT"
