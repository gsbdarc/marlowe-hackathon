# Report an Advanced training job to the room's Weights & Biases team, as the Beginner and Intermediate jobs do.
# Sourced by the slurm/marlowe/advanced/ training jobs. The team's key is in $SHARE/wandb.env, which every job reads;
# a line WANDB_API_KEY=... in .env at the top of your clone (git ignores it) wins if it holds a key of its own.
# Without a key the job trains as usual and its log says "W&B off". To keep a run off W&B: WANDB_MODE=disabled sbatch ...
#   wandb_room advanced-a2 a2-8gpu "$OUT"   # project, the run's name (your SUNet ID and the job ID are added), its --out
wandb_room() {
  export WANDB_ENTITY=${WANDB_ENTITY:-Marlowe-Hackathon} WANDB_PROJECT=${WANDB_PROJECT:-$1} WANDB_DIR=$WORK
  local f
  for f in "$SHARE/wandb.env" .env; do if [ -r "$f" ]; then set -a; source "$f"; set +a; fi; done
  if [ -n "${WANDB_API_KEY:-}" ] || [ "${WANDB_MODE:-}" = offline ]; then
    $PY scripts/wandb_watch.py --log "$PWD/logs/$SLURM_JOB_NAME-$SLURM_JOB_ID.out" --name "$USER-$2" --gpus "${GPUS:-1}" \
      ${3:+--run-dir "$3"} &
  else
    echo "W&B off: no WANDB_API_KEY in $SHARE/wandb.env or .env"
  fi
}
