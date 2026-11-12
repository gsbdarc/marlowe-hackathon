#!/bin/bash
#SBATCH -J i5-label-8gpu
#SBATCH --account=marlowe-c001
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=8
#SBATCH --exclusive
#SBATCH --cpus-per-task=96
#SBATCH --mem=1500G
#SBATCH --time=00:45:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu

# Intermediate I5: label every filing, all 296,477, on the 8 H100s of one node: one Kev server and one shard of the
# filings per GPU.
#   sbatch slurm/marlowe/intermediate/label_8gpu.slurm
#   FILINGS=16000 sbatch slurm/marlowe/intermediate/label_8gpu.slurm     # only the first 16,000; settings: see label.sh
# The answers are $WORK/results/i5/<jobid>/shard-<GPU>.jsonl.
source slurm/marlowe/intermediate/label.sh
