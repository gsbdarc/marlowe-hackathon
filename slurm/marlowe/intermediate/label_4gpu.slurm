#!/bin/bash
#SBATCH -J i5-label-4gpu
#SBATCH --account=marlowe-c001
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=32
#SBATCH --mem=256G
#SBATCH --time=00:25:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu

# Intermediate I5: label the first 32,000 filings on 4 H100s, one Kev server and one shard per GPU, 8,000 filings
# each. label_2gpu.slurm labels the same 32,000 on 2: compare the two to see how labeling scales.
#   sbatch slurm/marlowe/intermediate/label_4gpu.slurm
#   FILINGS=0 sbatch slurm/marlowe/intermediate/label_4gpu.slurm      # all 296,477 (needs a longer --time)
# The answers are $WORK/results/i5/<jobid>/shard-<n>.jsonl. Settings: see label.sh.
FILINGS=${FILINGS:-32000}
source slurm/marlowe/intermediate/label.sh
