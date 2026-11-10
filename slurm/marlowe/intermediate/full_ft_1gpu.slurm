#!/bin/bash
#SBATCH -J i3-full-1gpu
#SBATCH --account=marlowe-c001
#SBATCH --partition=preempt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=00:30:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu

# Intermediate I3, part 2: a full fine-tune of Kev-4B on one H100, every weight trained instead of a LoRA adapter.
# 128 GB of node memory: the fp32 master weights and the optimizer's moments live there. The first run also merges
# Kev-4B's adapter into full weights, once, in $WORK/kev-4b-full.
#   sbatch slurm/marlowe/intermediate/full_ft_1gpu.slurm
#   LR=1e-5 sbatch slurm/marlowe/intermediate/full_ft_1gpu.slurm     # settings: see full_ft.sh
# The run is $WORK/runs/i3-full/<jobid>.
GPUS=1 EXERCISE=i3-full WANDB_DEFAULT=exercise-3-marlowe
source slurm/marlowe/intermediate/full_ft.sh
