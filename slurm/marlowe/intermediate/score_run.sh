# After training, score the run as I2's job does: serve it with Kev on this job's GPU, label the 2,000 validation and
# the 1,000 test filings, and print agreement with Jev. With W&B on, the scores join the training run on the board as
# valid/... and test/... Sourced by finetune_kev.slurm and full_ft.sh once the run is trained; they set RUN, ID,
# EXERCISE, EVAL ("valid test" by default; empty skips scoring) and WB (1 when W&B is on).
# The filings come from the class data folder, read only: $CLASS_DATA/{valid,test1000}.{jsonl,parquet}.
if [ -n "$EVAL" ]; then
  START=$SECONDS
  PORT=$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
  (cd "$KEV_HOME/kev" && exec .venv/bin/python -m kev.serve --run "$RUN" --port "$PORT") > "logs/kev-server-$ID.log" 2>&1 &
  SERVER=$!; trap 'kill $SERVER $GPUMON 2>/dev/null || true' EXIT
  for i in $(seq 1 120); do                          # wait up to 10 minutes for the model to load
    curl -sf "http://127.0.0.1:$PORT/v1/models" > /dev/null && break
    kill -0 $SERVER 2>/dev/null || { echo "Kev server stopped; see logs/kev-server-$ID.log" >&2; exit 1; }
    sleep 5
  done
  curl -sf "http://127.0.0.1:$PORT/v1/models" > /dev/null || { echo "Kev server not ready after 10 minutes" >&2; exit 1; }
  echo "$RUN loaded in $((SECONDS - START)) s on $(hostname)"
  mkdir -p "$WORK/results/$EXERCISE"
  for E in $EVAL; do
    case $E in
      valid) DATA=$CLASS_DATA/valid.jsonl SAMPLE=$CLASS_DATA/valid.parquet ;;
      test) DATA=$CLASS_DATA/test1000.jsonl SAMPLE=$CLASS_DATA/test1000.parquet ;;
      *) echo "EVAL is valid, test or both (\"valid test\"): $E" >&2; exit 1 ;;
    esac
    echo "scoring the $E filings"
    OUT=$WORK/results/$EXERCISE/$ID-$E.jsonl
    $PY scripts/intermediate/label.py --url "http://127.0.0.1:$PORT" --data "$DATA" --out "$OUT" --concurrency 16
    $PY scripts/intermediate/score.py "$OUT" --sample "$SAMPLE" ${WB:+--wandb --wandb-prefix $E/}
  done
  kill $SERVER; wait $SERVER 2>/dev/null || true
fi
