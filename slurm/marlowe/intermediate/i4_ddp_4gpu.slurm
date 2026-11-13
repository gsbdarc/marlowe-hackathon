#!/bin/bash
#SBATCH -J i4-ddp-4gpu
#SBATCH --account=marlowe-c001
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=48
#SBATCH --mem=512G
#SBATCH --time=00:35:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu

# Intermediate I4: train on the same 4,800 filings as everyone else on 4 GPUs, on half a node: 4 H100s (about 10
# minutes; no --exclusive, so another 4-GPU job can use the other half),
# then score the model on the 2,000 validation and 1,000 test filings. The scores join the training run in W&B.
# This one: a LoRA fine-tune, data parallel (DDP), as lora_4gpu.slurm. Settings: LR, RECORDS_PER_STEP: 16, 40 or 80 (see lora.sh).
#   sbatch slurm/marlowe/intermediate/i4_ddp_4gpu.slurm
# The run is $WORK/runs/lora-ddp/<jobid>.
GPUS=4 EXERCISE=i4
FILINGS=${FILINGS:-4800} EVAL=${EVAL-valid test}
export WANDB_RUN_GROUP=${WANDB_RUN_GROUP:-4,800 filings}
source slurm/marlowe/intermediate/lora.sh
