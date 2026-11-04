#!/bin/bash
#SBATCH -J b4-full-8gpu
#SBATCH --account=marlowe-m000106
#SBATCH --partition=preempt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=8
#SBATCH --exclusive
#SBATCH --mem=0
#SBATCH --time=00:20:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu

# Beginner B4: B3's full fine-tune on all 8 H100s of one node, sharded with FSDP2. --exclusive --mem=0: the whole node
# and all its memory. Run B3's full_ft_1gpu.slurm first: it makes $WORK/kev-4b-full, which this job starts from.
#   sbatch slurm/marlowe/beginner/full_ft_8gpu.slurm
#   LR=1e-5 sbatch slurm/marlowe/beginner/full_ft_8gpu.slurm     # settings: see full_ft.sh
# The run is $WORK/runs/b4/<jobid>.
GPUS=8 EXERCISE=b4 WANDB_DEFAULT=exercise-4-fsdp
source slurm/marlowe/beginner/full_ft.sh
