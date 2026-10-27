#!/bin/bash -l
#SBATCH -J ceo-merge-kev
#SBATCH -p normal
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 00:30:00
#SBATCH -o logs/%x-%j.out

# Once, before training: fold Kev-4B's LoRA adapter into its base so a full fine-tune can start from it.
# Kev-4B ships as an adapter (rank 16); --full_ft trains every weight and starts from full weights.
#   sbatch slurm/yens/00_merge_kev.slurm        # -> $WORK/kev-4b-full/checkpoint (about 8 GB)
set -euo pipefail
source env/yens.sh
mkdir -p logs
cd "$KEV_HOME/kev"
$PY scripts/merge_lora_checkpoint.py --lora jaredpalmer/kev-4b@v1.0 --out "$WORK/kev-4b-full" --weights_dtype bf16
du -sh "$WORK/kev-4b-full/checkpoint"
