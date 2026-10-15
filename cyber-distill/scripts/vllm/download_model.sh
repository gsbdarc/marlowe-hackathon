#!/bin/bash
# Download a model into the folder the container serves from ($SCRATCH_BASE/vllm/models, seen as
# /models), using the container's own huggingface_hub, and print the revision to record.
# Run where outbound internet works (login or data-transfer node), in tmux for the ~240 GB teacher.
#   source scripts/vllm/env.sh && bash scripts/vllm/download_model.sh Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 [revision]
set -euo pipefail
: "${SCRATCH_BASE:?source scripts/vllm/env.sh first}"
command -v apptainer >/dev/null || module load apptainer
source "$(dirname "$0")/../home_check.sh"; home_mark
MODEL=${1:?model id}; REV=${2:-}
mkdir -p "$SCRATCH_BASE/vllm/models"
df -h "$SCRATCH_BASE" | tail -1
# --contain --cleanenv + a scratch home (as in vllm.sh): huggingface_hub's cache, token and lock files stay out of the real home.
apptainer exec --contain --cleanenv --home "$VLLM_CONTAINER_HOME:/root" --bind "$SCRATCH_BASE/vllm/models:/models" \
  --env HF_HOME=/root/.cache/huggingface "$VLLM_SIF" python3 - "$MODEL" "$REV" <<'PY'
import sys
from huggingface_hub import HfApi, snapshot_download
model, rev = sys.argv[1], sys.argv[2] or None
path = snapshot_download(model, revision=rev, cache_dir="/models")
print("downloaded to", path)
print("REVISION =", HfApi().model_info(model, revision=rev).sha, " <- record this (TEACHER_REVISION, README data card)")
PY
du -sh "$SCRATCH_BASE/vllm/models"
home_check
