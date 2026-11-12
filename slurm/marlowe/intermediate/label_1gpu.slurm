#!/bin/bash
#SBATCH -J i5-label-1gpu
#SBATCH --account=marlowe-c001
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:45:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu

# Intermediate I5: one H100's share of label_8gpu.slurm, to compare with: the filings split 8 ways, and this job labels
# the first shard, 37,060 filings, the same as GPU 0 does in the 8-GPU job.
#   sbatch slurm/marlowe/intermediate/label_1gpu.slurm
# The answers are $WORK/results/i5/<jobid>/shard-0.jsonl.
SHARDS=${SHARDS:-8}
source slurm/marlowe/intermediate/label.sh
