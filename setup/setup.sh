#!/bin/bash
# Instructor setup: everything the class needs on this cluster, in one run. Participants never run it. Run it once on
# each cluster, from your clone of this repository: on the Yens from an interactive node, on Marlowe from the login node.
#   bash setup/setup.sh
# On Marlowe it copies Jev's release from the Yens with rsync, so it asks you to log in to the Yens once (password, Duo).
# Safe to rerun: each step checks what is already there and skips it. See setup/README.md.
set -euo pipefail
cd "$(dirname "$0")/.."                       # the clone this script is in
case $(hostname) in
  yen*)    CLUSTER=yens ;;
  login-*) CLUSTER=marlowe ;;
  *) echo "run this on an interactive Yen node or the Marlowe login node, not $(hostname)" >&2; exit 2 ;;
esac
source "env/$CLUSTER.sh"
CACHE=${HF_HUB_CACHE:-$HF_HOME/hub}

# The hf command, at the huggingface_hub version Kev pins, in a temporary folder deleted when the script exits
TOOLS=$(mktemp -d)
trap 'rm -rf "$TOOLS"' EXIT
hf() {
  [ -x "$TOOLS/bin/hf" ] || python3 -m pip install -q --target "$TOOLS" "huggingface_hub==1.32.0"
  PYTHONPATH="$TOOLS" "$TOOLS/bin/hf" "$@"
}

echo "== 1. models, in $CACHE"
# model@revision; on the Yens, Kev-27B needs only its base model's tokenizer and config (no *.safetensors)
MODELS=(jaredpalmer/kev-4b@v1.0 Qwen/Qwen3.5-4B-Base@main jaredpalmer/kev-27b@af0e6d551bdc2cc724f3e9d7a8bee1cd4fb8f7bf
        Qwen/Qwen3.8-27B@1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0)
# Marlowe only: A4 serves Qwen 235B with vLLM
if [ "$CLUSTER" = marlowe ]; then MODELS+=(Qwen/Qwen3-235B-A22B-Instruct-2507-FP8@e156cb4efae43fbee1a1ab073f946a1377e6b969); fi
get() {  # get MODEL@REVISION [--offline]: download it, or with --offline only check it is in the cache
  local args=(download "${1%@*}" --revision "${1#*@}")
  if [ "$CLUSTER" = yens ] && [ "${1%@*}" = Qwen/Qwen3.8-27B ]; then args+=(--exclude "*.safetensors"); fi
  if [ "${2:-}" = --offline ]; then HF_HUB_OFFLINE=1 hf "${args[@]}" > /dev/null 2>&1; else HF_HUB_OFFLINE=0 hf "${args[@]}" > /dev/null; fi
}
changed=0
for m in "${MODELS[@]}"; do
  if get "$m" --offline; then echo "already there: $m"; else get "$m"; echo "downloaded: $m"; changed=1; fi
done
if [ "$CLUSTER" = marlowe ]; then
  SIF=$SHARE/containers/vllm-openai_v0.31.0.sif
  if [ -e "$SIF" ]; then echo "already there: $SIF"
  else mkdir -p "$(dirname "$SIF")" && apptainer pull "$SIF" docker://vllm/vllm-openai:v0.31.0; changed=1; fi
fi
if [ "$changed" = 1 ] && [ -O "$CACHE" ]; then chmod -R g-w "$CACHE"; fi     # read only for everyone but its owner
for m in "${MODELS[@]}"; do
  get "$m" --offline || { echo "model missing from $CACHE: $m" >&2; exit 1; }
  echo "model ok: $m"
done

echo "== 2. Kev, in $KEV_HOME"
bash scripts/setup_kev.sh                  # skips what is already installed; step 3 needs it
# Marlowe: everyone uses this prebuilt Kev, so make it read only for everyone but its owner
if [ "$CLUSTER" = marlowe ] && [ -O "$KEV_HOME" ]; then chmod -R g-w "$KEV_HOME"; fi

echo "== 3. data, in $(dirname "$DATA")"
OUT=$(dirname "$DATA")                     # train, valid and test1000 go next to the release
changed=0
YENS_JEV=/scratch/shared/marlowe_hackathon/data/jev   # Jev's release lives on the Yens: it is not on GitHub or Hugging Face
if [ ! -e "$DATA/MANIFEST.json" ]; then
  [ "$CLUSTER" = marlowe ] || { echo "Jev's release is not in $DATA" >&2; exit 1; }
  echo "copying Jev's release from the Yens: log in to the Yens when asked"
  mkdir -p "$DATA"
  rsync -a --info=progress2 "$USER@yen.stanford.edu:$YENS_JEV/" "$DATA/"
  changed=1
fi
python3 - "$DATA" <<'PY'
import hashlib, json, os, sys
d = sys.argv[1]
for name, f in json.load(open(os.path.join(d, "MANIFEST.json")))["files"].items():
    h = hashlib.sha256()
    with open(os.path.join(d, name), "rb") as fh:
        for block in iter(lambda: fh.read(1 << 24), b""):
            h.update(block)
    if h.hexdigest() != f["sha256"]:
        sys.exit(f"checksum does not match MANIFEST.json: {name}")
    print(f"release ok: {name}")
PY
if [ -e "$OUT/test1000.parquet" ] && [ -e "$OUT/train.jsonl" ] && [ -e "$OUT/valid.jsonl" ]; then
  echo "already there: train.jsonl, valid.jsonl, test1000.jsonl, test1000.parquet"
else
  $PY scripts/make_kev_data.py --out "$OUT"
  changed=1
fi
if [ "$changed" = 1 ] && [ -O "$OUT" ]; then chmod -R g-w "$OUT"; fi       # read only for everyone but its owner
# /scratch/c001/users: each participant makes a folder here. env/marlowe.sh may already have made it, for your own Kev
if [ "$CLUSTER" = marlowe ]; then
  mkdir -p "$(dirname "$ME")"
  if [ -O "$(dirname "$ME")" ]; then chmod g+w "$(dirname "$ME")"; fi
  echo "participants make their folders in $(dirname "$ME")"
fi
echo "== setup done on $CLUSTER"
