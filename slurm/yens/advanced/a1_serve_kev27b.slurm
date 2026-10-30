#!/bin/bash -l
#SBATCH -J kev27b-server
#SBATCH -p gpu
#SBATCH -G 1
#SBATCH -C GPU_MODEL:H200
#SBATCH -c 4
#SBATCH --mem=16G
#SBATCH -t 02:00:00
#SBATCH -o logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=nrapstin@stanford.edu

# A1: serve Kev-27B on one H200 and leave it running. Query it from an interactive Yen node, then stop it with
# scancel. Kev-27B's weights are 51 GB, so it needs an H200 (141 GB); an A40 (48 GB) is too small.
#   sbatch slurm/yens/advanced/a1_serve_kev27b.slurm
# The server's address (node:port) is written to $WORK/kev-27b.server.
set -euo pipefail
source env/yens.sh
MODEL=jaredpalmer/kev-27b@af0e6d551bdc2cc724f3e9d7a8bee1cd4fb8f7bf   # pinned, so everyone serves the same weights
PORT=$((8100 + SLURM_JOB_ID % 900))                                  # a port of its own, so two servers on one node don't collide
echo "$(hostname):$PORT" > "$WORK/kev-27b.server"
echo "serving $MODEL at http://$(hostname):$PORT on $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader -i 0)"
cd "$KEV_HOME/kev"
exec .venv/bin/python -m kev.serve --run "$MODEL" --host 0.0.0.0 --port "$PORT"
