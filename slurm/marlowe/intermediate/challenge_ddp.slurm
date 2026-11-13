#!/bin/bash
#SBATCH -J i4-challenge-ddp
#SBATCH --account=marlowe-c001
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=8
#SBATCH --exclusive
#SBATCH --cpus-per-task=96
#SBATCH --mem=1500G
#SBATCH --time=00:35:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu

# Intermediate I4, the 10-minute challenge: train on the same 9,600 filings as everyone else, on one node's 8 H100s,
# then score the model on the 2,000 validation and 1,000 test filings. The scores join the training run in W&B.
# This one: a LoRA fine-tune, data parallel (DDP), as lora_8gpu.slurm. Settings: LR, RECORDS_PER_STEP (see lora.sh).
#   sbatch slurm/marlowe/intermediate/challenge_ddp.slurm
# The run is $WORK/runs/lora-ddp/<jobid>.
GPUS=8 EXERCISE=i4
FILINGS=${FILINGS:-9600} EVAL=${EVAL-valid test}
export WANDB_RUN_GROUP=${WANDB_RUN_GROUP:-10-minute challenge}
source slurm/marlowe/intermediate/lora.sh
