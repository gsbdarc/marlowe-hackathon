#!/bin/bash
# Download every model the tasks use into this cluster's shared model cache. For organizers: participants never run
# it. It does not install Kev; participants do that with setup_kev.sh, which then checks these models are there.
# Run it from your clone, on an interactive Yen node or the Marlowe login node:
#   bash scripts/download_models.sh
# Safe to rerun: a model already in the cache is checked and skipped.
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
python3 -m pip install -q --target "$TOOLS" "huggingface_hub==1.32.0"
hf() { PYTHONPATH="$TOOLS" "$TOOLS/bin/hf" "$@"; }

# model@revision; on the Yens, Kev-27B needs only its base model's tokenizer and config (no *.safetensors)
MODELS=(jaredpalmer/kev-4b@v1.0 Qwen/Qwen3.5-4B-Base@main jaredpalmer/kev-27b@af0e6d551bdc2cc724f3e9d7a8bee1cd4fb8f7bf
        Qwen/Qwen3.8-27B@1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0)
get() {  # get MODEL@REVISION: download it, or with HF_HUB_OFFLINE=1 only check it is in the cache
  local args=(download "${1%@*}" --revision "${1#*@}")
  if [ "$CLUSTER" = yens ] && [ "${1%@*}" = Qwen/Qwen3.8-27B ]; then args+=(--exclude "*.safetensors"); fi
  hf "${args[@]}"
}

echo "== downloading into $CACHE"
for m in "${MODELS[@]}"; do
  HF_HUB_OFFLINE=0 get "$m" > /dev/null
  echo "downloaded: $m"
done
if [ "$CLUSTER" = marlowe ]; then
  # Marlowe only: A4 serves Qwen 235B with vLLM, from a container in the project's shared containers folder
  HF_HUB_OFFLINE=0 hf download Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 --revision e156cb4efae43fbee1a1ab073f946a1377e6b969 > /dev/null
  echo "downloaded: Qwen/Qwen3-235B-A22B-Instruct-2507-FP8@e156cb4efae43fbee1a1ab073f946a1377e6b969"
  SIF=$SHARE/containers/vllm-openai_v0.31.0.sif
  if [ ! -e "$SIF" ]; then mkdir -p "$(dirname "$SIF")" && apptainer pull "$SIF" docker://vllm/vllm-openai:v0.31.0; fi
  echo "container: $SIF"
fi
if [ "$CLUSTER" = yens ]; then chmod -R g-w "$CACHE"; fi   # Yens: read only for all but its owner; Marlowe's stays group-writable

echo "== checking, with downloads off"
for m in "${MODELS[@]}"; do
  HF_HUB_OFFLINE=1 get "$m" > /dev/null 2>&1 \
    || { echo "model missing from $CACHE: $m" >&2; exit 1; }
  echo "model ok: $m"
done
