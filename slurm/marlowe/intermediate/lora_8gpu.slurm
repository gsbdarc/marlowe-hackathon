#!/bin/bash
#SBATCH -J lora-8gpu
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

# LoRA fine-tune of Kev-4B on all 8 H100s of one node, data parallel: each GPU a whole copy of the model, trained on 2
# of each step's 16 filings, the adapter gradients summed every step. Same settings as lora_1gpu.slurm; see lora.sh.
#   sbatch slurm/marlowe/intermediate/lora_8gpu.slurm
# The run is $WORK/runs/lora-ddp/<jobid>; score it with score_test.slurm.
GPUS=8
source slurm/marlowe/intermediate/lora.sh
