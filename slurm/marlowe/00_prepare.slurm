#!/bin/bash
#SBATCH -J ceo-prepare
#SBATCH --account=marlowe-m000106
#SBATCH --partition=preempt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --output=logs/%x-%j.out

# Once on Marlowe, before checkpoint 3: build the training files and Kev-4B as full weights, the same two steps
# slurm/yens/00_data.slurm and 00_merge_kev.slurm do on the Yens. Skip it if you copied $WORK from the Yens.
#   sbatch slurm/marlowe/00_prepare.slurm
set -euo pipefail
module load slurm mps
source env/marlowe.sh
mkdir -p logs
$PY scripts/make_kev_data.py
cd "$KEV_HOME/kev"
$PY scripts/merge_lora_checkpoint.py --lora jaredpalmer/kev-4b@v1.0 --out "$WORK/kev-4b-full" --weights_dtype bf16
