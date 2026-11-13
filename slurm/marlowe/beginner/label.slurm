#!/bin/bash
#SBATCH -J b4-label
#SBATCH --account=marlowe-c001
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-gpu=8
#SBATCH --mem-per-gpu=64G
#SBATCH --time=00:45:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu
#
# NOTE FOR INSTRUCTORS: see the partition/reservation note in slurm/marlowe/beginner/finetune.slurm. CPUs and memory
# are per GPU, so --gpus-per-node on the command line scales them too. Batch's submit plugin sets the CPU count from
# the memory asked for (about 16 GB a CPU); do not use --mem=0, which asks for more CPUs than a node has.

# Beginner B4: label Kev-4B's answers for every Item 5.02 filing since 2004, dealt into 8 piles (shards) of 37,060.
# Each GPU starts its own copy of the model and labels one pile, so a job with N GPUs labels the first N piles. First
# the 1-GPU job, then the same file with the number of GPUs you chose (2, 4 or 8):
#   sbatch --reservation=GSB_Hackathon slurm/marlowe/beginner/label.slurm
#   sbatch --reservation=GSB_Hackathon --gpus-per-node=4 slurm/marlowe/beginner/label.slurm
# The answers are $WORK/results/b4/<jobid>/shard-<n>.jsonl. It runs the Intermediate track's I5 job unchanged.
# B5's challenge labels with your own trained model instead, and keeps its answers apart:
#   RUN=$WORK/runs/b3/<jobid> RESULTS_NAME=b5 sbatch --reservation=GSB_Hackathon slurm/marlowe/beginner/label.slurm
RESULTS_NAME=${RESULTS_NAME:-b4} SHARDS=8
# The job's speed goes to the room's W&B board as one run, in the Beginner Exercise 4 project, not I5's
export WANDB_PROJECT="${WANDB_PROJECT:-Beginner Exercise 4}"
source slurm/marlowe/intermediate/label.sh
