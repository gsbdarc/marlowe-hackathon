#!/bin/bash
#SBATCH -J i4-full-8gpu
#SBATCH --account=marlowe-c001
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=8
#SBATCH --exclusive
#SBATCH --cpus-per-task=96
#SBATCH --mem=1500G
#SBATCH --time=00:20:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu

# Intermediate I4: I3's full fine-tune on all 8 H100s of one node, sharded with FSDP2. --exclusive: the whole node.
# batch sets the CPU count from the memory asked for: --mem=0 would ask for 115 CPUs on a 112-CPU node and be refused,
# so the job asks for 96 CPUs and 1,500 GB. Run I3's full_ft_1gpu.slurm first: it makes $WORK/kev-4b-full.
#   sbatch slurm/marlowe/intermediate/full_ft_8gpu.slurm
#   LR=1e-5 sbatch slurm/marlowe/intermediate/full_ft_8gpu.slurm     # settings: see full_ft.sh
# The run is $WORK/runs/i4/<jobid>.
GPUS=8 EXERCISE=i4 WANDB_DEFAULT=exercise-4-fsdp
source slurm/marlowe/intermediate/full_ft.sh
