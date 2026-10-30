#!/bin/bash
# Download every model the tasks use into this cluster's shared model cache. For organizers: participants never run it.
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

# Install Kev for its hf command. Its model check at the end fails while models are missing, which is expected here.
bash scripts/setup_kev.sh || true
HF=$KEV_HOME/kev/.venv/bin/hf
[ -x "$HF" ] || { echo "setup_kev.sh did not install Kev: $HF is missing" >&2; exit 1; }

echo "== downloading into $CACHE"
export HF_HUB_OFFLINE=0                        # env/$CLUSTER.sh turns downloads off; on for this script only
"$HF" download jaredpalmer/kev-4b --revision v1.0
"$HF" download Qwen/Qwen3.5-4B-Base --revision main
"$HF" download jaredpalmer/kev-27b --revision af0e6d551bdc2cc724f3e9d7a8bee1cd4fb8f7bf
if [ "$CLUSTER" = yens ]; then
  # Kev-27B needs only its base model's tokenizer and config on the Yens
  "$HF" download Qwen/Qwen3.8-27B --revision 1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0 --exclude "*.safetensors"
  chmod -R g-w "$CACHE"                        # read only for everyone but its owner
else
  # full weights on Marlowe, for the Advanced fine-tunes; the cache stays writable by the project group
  "$HF" download Qwen/Qwen3.8-27B --revision 1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0
fi

echo "== checking, with downloads off"
export HF_HUB_OFFLINE=1
bash scripts/setup_kev.sh
