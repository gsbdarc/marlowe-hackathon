#!/bin/bash
#SBATCH --job-name=cyber_vllm_setup
#SBATCH --partition=normal
#SBATCH --output=logs/cyber_vllm_setup_%j.out
#SBATCH --error=logs/cyber_vllm_setup_%j.err
#SBATCH --time=01:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=nrapstin@stanford.edu

# One-time: vllm_helper clone and vLLM container pull into /scratch/shared/$USER (scripts/vllm/setup.sh).
set -euo pipefail
cd /zfs/projects/darc/marlowe_hackathon/cyber-distill
module load apptainer
bash scripts/vllm/setup.sh
