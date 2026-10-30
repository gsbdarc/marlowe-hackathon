# The Advanced fine-tune that A2 and A3 run, so their times compare. Sourced by the slurm/marlowe/advanced/ jobs.
# A full fine-tune of Qwen3.8-27B (every weight) on Jev's soft labels with Kev's trainer, from the base model and a new
# pointer head. bf16 weights and gradients plus fp32 master weights and AdamW moments: about 16 bytes per parameter.
# On one GPU the masters and moments go to host memory; under torchrun, FSDP2 splits all of it across the GPUs.
# Each step trains 16 records at every scale (BATCH x ACCUM x GPUS). Set GPUS before sourcing. EXTRA_ARGS adds
# kev.train options (for example EXTRA_ARGS="--length_sort 1").
source slurm/train_args.sh      # STEPS, BATCH, ACCUM, gpu_log, wandb_watch
BASE=Qwen/Qwen3.8-27B
BASE_REVISION=1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0
# Kev-27B's learning rates: 2e-6 for the backbone, 1e-4 for the new pointer head
TRAIN_ARGS="--data $WORK/data/train.jsonl --base $BASE --base_revision $BASE_REVISION \
  --full_ft 1 --weights_dtype bf16 --dtype bf16 --checkpointing 1 --device cuda \
  --lr 2e-6 --head_lr 1e-4 --batch $BATCH --accum $ACCUM --max_state 2048 --max_steps $STEPS --seed 0 ${EXTRA_ARGS:-}"
