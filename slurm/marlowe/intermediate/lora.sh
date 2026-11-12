# LoRA fine-tune of Kev-4B on 1, 4 or 8 H100s, data parallel (like DDP): every GPU holds the whole model and its own
# copy of the adapter, trains on its share of each step's filings, and the GPUs add up their adapter gradients once per
# step. Sourced by lora_1gpu.slurm, lora_4gpu.slurm and lora_8gpu.slurm, which set GPUS first.
# The settings match I3 Part 2 and I4's full fine-tunes (100 steps of 16 filings, lr 2e-5), so every method trains on
# the same 1,600 filings, in the same order, 16 a step, and score_test.slurm compares them on the same test filings.
# Kev's own trainer runs LoRA on one GPU only. The data-parallel version is scripts/intermediate/kev-lora-ddp.patch,
# applied to a second checkout of Kev next to yours ($KEV_HOME/kev-lora-ddp, made here the first time; it uses Kev's
# own Python).
# Settings, set before sbatch:
#   LR=2e-5                learning rate
#   RECORDS_PER_STEP=16    filings per optimizer step, in total across the GPUs; a multiple of GPUS
#   STEPS=100              optimizer steps (at least 20: the learning rate warms up over the first 10%)
#   WEIGHTS=fp32           the frozen backbone's weights (fp32, as in I2 and I3 Part 1, or bf16)
set -euo pipefail
module load slurm mps                  # mps avoids CUDA_ERROR_MPS_CONNECTION_FAILED (Marlowe docs)
source env/marlowe.sh
LR=${LR:-2e-5} RECORDS_PER_STEP=${RECORDS_PER_STEP:-16} STEPS=${STEPS:-100} WEIGHTS=${WEIGHTS:-fp32}
KEV_DDP=${KEV_DDP:-$KEV_HOME/kev-lora-ddp}
if [ $((RECORDS_PER_STEP % GPUS)) != 0 ]; then echo "RECORDS_PER_STEP must be a multiple of $GPUS" >&2; exit 1; fi
if [ "$STEPS" -lt 20 ]; then echo "STEPS must be at least 20" >&2; exit 1; fi
if [ ! -d "$KEV_DDP" ]; then           # first time: a second checkout of Kev, with the data-parallel patch
  git -C "$KEV_HOME/kev" worktree add --detach "$KEV_DDP" HEAD
  git -C "$KEV_DDP" apply "$PWD/scripts/intermediate/kev-lora-ddp.patch"
fi
if ! grep -q "def sum_gradients" "$KEV_DDP/kev/full_ft.py"; then
  echo "$KEV_DDP has no data-parallel LoRA: git -C $KEV_DDP apply $PWD/scripts/intermediate/kev-lora-ddp.patch" >&2; exit 1
fi
RUN=$WORK/runs/lora-ddp/$SLURM_JOB_ID
mkdir -p logs "$WORK/runs/lora-ddp"
# Slurm can requeue a job under the same ID (a node fails, or someone requeues it). LoRA keeps no resume point, so an
# unfinished run starts again from step 0; a finished one (head.pt written) is not trained twice.
if [ -f "$RUN/head.pt" ]; then
  echo "$RUN is already trained"; $PY scripts/step_times.py "$RUN" --per-step "$RECORDS_PER_STEP"; exit 0
elif [ -d "$RUN" ]; then
  echo "an unfinished run in $RUN (the job was stopped and requeued): training again from step 0"; rm -rf "$RUN"
fi
nvidia-smi --query-gpu=timestamp,index,name,utilization.gpu,memory.used,memory.total --format=csv -l 5 > "logs/gpu-$SLURM_JOB_ID.csv" &
GPUMON=$!; trap 'kill $GPUMON 2>/dev/null || true' EXIT

export WANDB_PROJECT=${WANDB_PROJECT:-lora-ddp} WANDB_ENTITY=${WANDB_ENTITY:-Marlowe-Hackathon}
export WANDB_DIR=$WORK WANDB_CACHE_DIR=$XDG_CACHE_HOME/wandb WANDB_CONFIG_DIR=$XDG_CACHE_HOME/wandb-config
for f in "$SHARE/wandb.env" .env; do if [ -r "$f" ]; then set -a; source "$f"; set +a; fi; done
NAME=$USER-h100x$GPUS-lora-lr$LR-rps$RECORDS_PER_STEP-$WEIGHTS

ARGS=(--data "$WORK/data/train.jsonl" --base Qwen/Qwen3.5-4B-Base --base_revision 1001bb4d826a52d1f399e183466143f4da7b741b
      --init_from jaredpalmer/kev-4b@v1.0 --lora 16 --weights_dtype "$WEIGHTS" --dtype bf16 --checkpointing 1 --device cuda
      --max_state 2048 --seed 0 --lr "$LR" --batch 1 --accum $((RECORDS_PER_STEP / GPUS)) --max_steps "$STEPS" --out "$RUN")
WATCH=
if [ -n "${WANDB_API_KEY:-}" ] || [ "${WANDB_MODE:-}" = offline ]; then
  $PY scripts/intermediate/wandb_watch.py --log "$PWD/logs/$SLURM_JOB_NAME-$SLURM_JOB_ID.out" --run-dir "$RUN" --name "$NAME" --gpus "$GPUS" &
  WATCH=$!
else
  echo "W&B off: no WANDB_API_KEY in $SHARE/wandb.env or .env"
fi
echo "Kev from $KEV_DDP ($(git -C "$KEV_DDP" rev-parse --short HEAD)), $GPUS GPU(s), $RECORDS_PER_STEP filings a step, $STEPS steps"
if [ "$GPUS" = 1 ]; then
  (cd "$KEV_DDP" && $PY -m kev.train "${ARGS[@]}")
else
  (cd "$KEV_DDP" && "$KEV_HOME/kev/.venv/bin/torchrun" --standalone --nproc_per_node "$GPUS" -m kev.train "${ARGS[@]}")
fi
if [ -n "$WATCH" ]; then wait $WATCH; fi
$PY scripts/step_times.py "$RUN" --per-step "$RECORDS_PER_STEP"
echo "score it: RUNS=\"lora-${GPUS}gpu=$RUN\" sbatch slurm/marlowe/intermediate/score_test.slurm"
