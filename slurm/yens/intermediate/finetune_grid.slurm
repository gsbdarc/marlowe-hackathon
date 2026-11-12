#!/bin/bash -l
#SBATCH -J ceo-finetune-grid
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_MODEL:A40
#SBATCH -c 8
#SBATCH --mem=32G
#SBATCH -t 04:00:00
#SBATCH -o logs/%x-%j.out

# Every setting of exercise 2 in one job, one after another on one GPU, for the hackathon's reference dashboard. Each
# setting trains for about 10 minutes (finetune_kev.slurm's default for the GPU), then is scored on the validation and
# the test filings, all in its own W&B run. Participants run one setting at a time with finetune_kev.slurm.
#   sbatch -C GPU_MODEL:H200 slurm/yens/intermediate/finetune_grid.slurm    # about 2 hours on an H200
# Each setting's log is logs/ceo-finetune-<jobid>-<setting>.out, and its run is $WORK/runs/i2/<jobid>-<setting>.
set -uo pipefail
mkdir -p logs
while read -r name vars; do
  echo "$(date +%T) $name: $vars"
  env ID="$SLURM_JOB_ID-$name" EVAL="valid test" $vars bash slurm/yens/intermediate/finetune_kev.slurm < /dev/null \
    > "logs/ceo-finetune-$SLURM_JOB_ID-$name.out" 2>&1 || echo "  $name failed: see logs/ceo-finetune-$SLURM_JOB_ID-$name.out"
done <<'EOF'
default      INIT=kev
lr2e-6       LR=2e-6
lr2e-4       LR=2e-4
rps2         RECORDS_PER_STEP=2
rps32        RECORDS_PER_STEP=32
bf16         WEIGHTS=bf16
scratch-r4   INIT=scratch RANK=4
scratch-r16  INIT=scratch RANK=16
scratch-r64  INIT=scratch RANK=64
EOF
echo "$(date +%T) done"
