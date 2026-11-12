# Sourced by the beginner jobs: find the room's W&B key. First the hackathon's shared key file ($HACKATHON/wandb.env on
# the Yens, $SHARE/wandb.env on Marlowe), then a .env at the top of your clone, which wins if it holds a key of its own.
# Each file is read for its one line WANDB_API_KEY=..., not run as shell code, so a key typed with quotes, or the
# placeholder <the room's key> left in by mistake, turns W&B off with a message instead of stopping the job.
wandb_key_from() {                     # print the key in file $1, or nothing
  [ -r "$1" ] || return 0
  sed -n 's/^[[:space:]]*\(export[[:space:]]\{1,\}\)\{0,1\}WANDB_API_KEY=//p' "$1" | tail -1 | tr -d "\"' \r"
}
for f in "${HACKATHON:-${SHARE:-/nonexistent}}/wandb.env" .env; do
  KEY=$(wandb_key_from "$f")
  case $KEY in
    "") ;;
    *"<"*|*">"*) echo "W&B: ignoring $f, it still has the placeholder <the room's key>" ;;
    *) export WANDB_API_KEY=$KEY ;;
  esac
done
unset KEY f
unset -f wandb_key_from
