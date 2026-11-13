#!/bin/bash
#SBATCH -J i4-fsdp-4gpu
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
# This one: a full fine-tune, sharded with FSDP2, as full_ft_8gpu.slurm, on 4 GPUs: 1/4 each. Settings: LR, RECORDS_PER_STEP: 16, 40 or 80 (see full_ft.sh).
#   sbatch slurm/marlowe/intermediate/i4_fsdp_4gpu.slurm
# The run is $WORK/runs/i4/<jobid>. Run I3's full_ft_1gpu.slurm first: it makes $WORK/kev-4b-full.
GPUS=4 EXERCISE=i4 WANDB_DEFAULT="Intermediate Exercise 4"
FILINGS=${FILINGS:-4800} EVAL=${EVAL-valid test}
export WANDB_RUN_GROUP=${WANDB_RUN_GROUP:-4,800 filings}
source slurm/marlowe/intermediate/full_ft.sh
