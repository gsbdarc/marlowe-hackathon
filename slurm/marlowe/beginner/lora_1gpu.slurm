#!/bin/bash
#SBATCH -J lora-1gpu
#SBATCH --account=marlowe-m000106
#SBATCH --partition=preempt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:40:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu

# LoRA fine-tune of Kev-4B on one H100: the baseline the 4- and 8-GPU data-parallel runs are compared with. Same
# settings as every LoRA and full fine-tune run here (100 steps of 16 filings, lr 2e-5); see lora.sh.
#   sbatch slurm/marlowe/beginner/lora_1gpu.slurm
# The run is $WORK/runs/lora-ddp/<jobid>; score it with score_test.slurm.
GPUS=1
source slurm/marlowe/beginner/lora.sh
