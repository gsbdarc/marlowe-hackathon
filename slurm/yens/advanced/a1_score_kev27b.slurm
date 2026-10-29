#!/bin/bash -l
#SBATCH -J adv-a1-kev27b
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_MODEL:H200
#SBATCH -c 4
#SBATCH --mem=16G
#SBATCH -t 01:00:00
#SBATCH -o logs/%x-%j.out

# A1: serve Kev-27B on one H200 and score it on the 1,000 test filings before any training. Its weights are 51 GB,
# so it needs an H200 (141 GB); an A40 (48 GB) is too small. Run from the repository root:
#   sbatch slurm/yens/advanced/a1_score_kev27b.slurm
# Results go to $WORK/results/kev-27b-zeroshot.jsonl; the scores print at the end of the log.
exec bash slurm/yens/serve_and_label.slurm jaredpalmer/kev-27b@af0e6d551bdc2cc724f3e9d7a8bee1cd4fb8f7bf kev-27b-zeroshot
