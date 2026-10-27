# The training job every checkpoint runs, so their times compare. Sourced by the train_*.slurm scripts.
# Kev's full fine-tune (every weight; bf16 weights, fp32 master weights), starting from the released Kev-4B,
# on Jev's soft labels. Under torchrun it shards across the GPUs with FSDP2; on one GPU the master weights
# sit in host memory. A fixed number of optimizer steps (STEPS) gives a time per step you can compare
# across GPU counts. Each step trains on BATCH x ACCUM x GPUS records, so ACCUM shrinks as GPUS grows and
# every scale takes 16 records per step: the same training, split more ways. Set GPUS before sourcing.
BASE=Qwen/Qwen3.5-4B-Base
INIT=${INIT:-$WORK/kev-4b-full/checkpoint}   # Kev-4B as full weights, from slurm/yens/00_merge_kev.slurm
STEPS=${STEPS:-100}      # at least 20: the learning rate warms up over the first 10% of steps
BATCH=${BATCH:-1}
GPUS=${GPUS:-1}
ACCUM=${ACCUM:-$((16 / GPUS))}
# One line with no newlines (each \ joins the next line), so it also survives the bash -c "..." in 05_train_2node.slurm.
TRAIN_ARGS="--data $WORK/data/train.jsonl --base $BASE --init_from $INIT \
  --full_ft 1 --weights_dtype bf16 --dtype bf16 --checkpointing 1 --device cuda \
  --lr 2e-5 --batch $BATCH --accum $ACCUM --max_state 2048 --max_steps $STEPS --seed 0"
# Log GPU memory and utilization every 15 seconds, next to the job's log.
gpu_log() { nvidia-smi --query-gpu=timestamp,index,name,utilization.gpu,memory.used,memory.total --format=csv -l 15 > "$1" & }
# With WANDB=1, follow this job's log and send its progress to Weights & Biases (scripts/wandb_watch.py).
wandb_watch() {
  [ "${WANDB:-0}" = 1 ] || return 0
  $PY scripts/wandb_watch.py --log "$PWD/logs/$SLURM_JOB_NAME-$SLURM_JOB_ID.out" --name "$1" --gpus "$GPUS" &
}
