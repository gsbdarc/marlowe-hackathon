#!/bin/bash
#SBATCH -J a5-student
#SBATCH --account=marlowe-c001
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=00:30:00
#SBATCH --output=logs/%x-%j.out
# Email when the job starts, ends or fails: replace <sunet> with your SUNet ID
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=<sunet>@stanford.edu

# A5: distill a student. Train Qwen3.5-4B-Base as a LoRA, with Kev's trainer, on a teacher's labels from
# scripts/advanced/make_teacher_data.py. The argument names the teacher: its labels are $WORK/data/teacher-<name>.jsonl, and the
# student is saved in $WORK/runs/a5-<name>.
#   sbatch slurm/marlowe/advanced/a5_train_student.slurm qwen-235b         # the student of Qwen 235B
set -euo pipefail
module load slurm mps                  # mps avoids CUDA_ERROR_MPS_CONNECTION_FAILED (Marlowe docs)
source env/marlowe.sh
source slurm/train_args.sh             # job_timer, stamp, gpu_log
TEACHER=${1:?name the teacher, for example qwen-235b}
DATA=$WORK/data/teacher-$TEACHER.jsonl
OUT=$WORK/runs/a5-$TEACHER
[ -f "$DATA" ] || { echo "no $DATA: run scripts/advanced/make_teacher_data.py first" >&2; exit 1; }
job_timer
mkdir -p logs && rm -rf "$OUT"
gpu_log "logs/gpu-$SLURM_JOB_ID.csv"
cd "$KEV_HOME/kev"
# A rank-16 LoRA at learning rate 5e-5, as in Kev's recipe for its 4B model, stopped after 100 steps of 16 filings
# (1,600 filings, about 10 minutes) so the job fits the session. Remove --max_steps 100 and set --epochs 2 for the full recipe.
$PY -m kev.train --data "$DATA" --base Qwen/Qwen3.5-4B-Base \
  --full_ft 0 --lora 16 --lr 5e-5 --epochs 1 --max_steps 100 \
  --weights_dtype bf16 --dtype bf16 --checkpointing 1 --device cuda \
  --batch 1 --accum 16 --max_state 2048 --seed 0 --out "$OUT" 2>&1 | stamp
