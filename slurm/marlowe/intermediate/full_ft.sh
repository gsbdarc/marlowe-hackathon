# The full fine-tune of I3 and I4: every one of Qwen 4B's 4.2 billion weights is trained, starting from Kev-4B, instead
# of I2's LoRA adapter. Sourced by full_ft_1gpu.slurm (I3) and full_ft_8gpu.slurm (I4), which set GPUS first.
#   One GPU:  the bf16 weights and gradients sit on the H100; the fp32 master weights and the optimizer's moments
#             (about 50 GB) sit in the node's memory and stream to and from the GPU every step.
#   8 GPUs:   torchrun starts 8 copies of the trainer, one per GPU. FSDP2 gives each 1/8 of the weights, gradients,
#             master weights and moments, and each trains on 1/8 of every step's filings.
# Settings, set before sbatch:
#   LR=2e-5                learning rate
#   RECORDS_PER_STEP=16    filings per optimizer step, in total across the GPUs; a multiple of GPUS
#   FILINGS=1600           filings to train on: FILINGS / RECORDS_PER_STEP steps (100 by default)
#   STEPS=100              or set the optimizer steps directly (at least 20: the learning rate warms up over 10%)
#   EVAL="valid test"      what to score after training, on one GPU; EVAL= skips it (8 GPUs: off by default)
set -euo pipefail
module load slurm mps                  # mps avoids CUDA_ERROR_MPS_CONNECTION_FAILED (Marlowe docs)
source env/marlowe.sh
LR=${LR:-2e-5} RECORDS_PER_STEP=${RECORDS_PER_STEP:-16} FILINGS=${FILINGS:-1600}
STEPS=${STEPS:-$((FILINGS / RECORDS_PER_STEP))}
# One GPU (I3) scores the run on validation and test after training, as I2 did; I4 compares runs with score_test.slurm
EVAL=${EVAL-$([ "$GPUS" = 1 ] && echo "valid test")} ID=$SLURM_JOB_ID
if [ $((RECORDS_PER_STEP % GPUS)) != 0 ]; then echo "RECORDS_PER_STEP must be a multiple of $GPUS" >&2; exit 1; fi
if [ "$STEPS" -lt 20 ]; then echo "STEPS must be at least 20" >&2; exit 1; fi
INIT=$WORK/kev-4b-full                 # Kev-4B as full weights: its LoRA adapter merged into Qwen 4B
RUN=$WORK/runs/$EXERCISE/$SLURM_JOB_ID
mkdir -p logs "$WORK/runs/$EXERCISE"
nvidia-smi --query-gpu=timestamp,index,name,utilization.gpu,memory.used,memory.total --format=csv -l 5 > "logs/gpu-$SLURM_JOB_ID.csv" &
GPUMON=$!; trap 'kill $GPUMON 2>/dev/null || true' EXIT

if [ ! -f "$INIT/checkpoint/head.pt" ]; then
  if [ "$GPUS" != 1 ]; then echo "no $INIT yet: run I3's sbatch slurm/marlowe/intermediate/full_ft_1gpu.slurm first" >&2; exit 1; fi
  echo "merging Kev-4B's adapter into Qwen 4B, once: $INIT"
  rm -rf "$INIT"
  (cd "$KEV_HOME/kev" && $PY scripts/merge_lora_checkpoint.py --lora jaredpalmer/kev-4b@v1.0 --out "$INIT" --weights_dtype bf16)
fi

export WANDB_PROJECT=${WANDB_PROJECT:-$WANDB_DEFAULT} WANDB_ENTITY=${WANDB_ENTITY:-Marlowe-Hackathon}
export WANDB_DIR=$WORK WANDB_CACHE_DIR=$XDG_CACHE_HOME/wandb WANDB_CONFIG_DIR=$XDG_CACHE_HOME/wandb-config
for f in "$SHARE/wandb.env" .env; do if [ -r "$f" ]; then set -a; source "$f"; set +a; fi; done
NAME=$USER-h100x$GPUS-full-lr$LR-rps$RECORDS_PER_STEP

ARGS=(--data "$WORK/data/train.jsonl" --base Qwen/Qwen3.5-4B-Base --base_revision 1001bb4d826a52d1f399e183466143f4da7b741b
      --init_from "$INIT/checkpoint" --full_ft 1 --weights_dtype bf16 --dtype bf16 --checkpointing 1 --device cuda
      --max_state 2048 --seed 0 --lr "$LR" --batch 1 --accum $((RECORDS_PER_STEP / GPUS)) --max_steps "$STEPS" --out "$RUN")
WATCH=
WB=
if [ -n "${WANDB_API_KEY:-}" ] || [ "${WANDB_MODE:-}" = offline ]; then
  WB=1                                 # one W&B run for the job: the training curve, then the scores
  export WANDB_RUN_ID=$(python3 -c 'import uuid; print(uuid.uuid4().hex[:12])') WANDB_JOB_TYPE=train
  $PY scripts/intermediate/wandb_watch.py --log "$PWD/logs/$SLURM_JOB_NAME-$SLURM_JOB_ID.out" --run-dir "$RUN" --name "$NAME" --gpus "$GPUS" &
  WATCH=$!
else
  echo "W&B off: no WANDB_API_KEY in $SHARE/wandb.env or .env"
fi
if [ "$GPUS" = 1 ]; then
  (cd "$KEV_HOME/kev" && $PY -m kev.train "${ARGS[@]}")
else
  (cd "$KEV_HOME/kev" && "$KEV_HOME/kev/.venv/bin/torchrun" --standalone --nproc_per_node "$GPUS" -m kev.train "${ARGS[@]}")
fi
if [ -n "$WATCH" ]; then wait $WATCH; fi
$PY scripts/step_times.py "$RUN" --per-step "$RECORDS_PER_STEP"
source slurm/marlowe/intermediate/score_run.sh
