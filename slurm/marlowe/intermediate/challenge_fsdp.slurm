#!/bin/bash
#SBATCH -J i4-challenge-fsdp
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
# This one: a full fine-tune, sharded with FSDP2, as full_ft_8gpu.slurm. Settings: LR, RECORDS_PER_STEP (see full_ft.sh).
#   sbatch slurm/marlowe/intermediate/challenge_fsdp.slurm
# The run is $WORK/runs/i4/<jobid>. Run I3's full_ft_1gpu.slurm first: it makes $WORK/kev-4b-full.
GPUS=8 EXERCISE=i4 WANDB_DEFAULT="Intermediate Exercise 4"
FILINGS=${FILINGS:-9600} EVAL=${EVAL-valid test}
export WANDB_RUN_GROUP=${WANDB_RUN_GROUP:-10-minute challenge}
source slurm/marlowe/intermediate/full_ft.sh
