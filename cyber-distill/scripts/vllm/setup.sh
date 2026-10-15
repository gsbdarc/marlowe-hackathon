#!/bin/bash
# One-time per cluster: clone vllm_helper at the pinned commit and pull the vLLM container image
# into SCRATCH_BASE. On the Yens run it as a CPU job (slurm/vllm_setup_yens.slurm): building the
# 12 GB image is too heavy for a login node.
set -euo pipefail
source "$(dirname "$0")/env.sh"
command -v apptainer >/dev/null || module load apptainer
source "$(dirname "$0")/../home_check.sh"; home_mark
mkdir -p "$SCRATCH_BASE/vllm" "$APPTAINER_CACHEDIR"
if [ ! -d "$VLLM_HELPER/.git" ]; then
  git clone -q https://github.com/gsbdarc/vllm_helper.git "$VLLM_HELPER"
fi
git -C "$VLLM_HELPER" fetch -q --all && git -C "$VLLM_HELPER" checkout -q "$VLLM_HELPER_COMMIT"
echo "vllm_helper at $(git -C "$VLLM_HELPER" log --oneline -1)"
if [ ! -f "$VLLM_SIF" ]; then
  apptainer pull "$VLLM_SIF" "docker://vllm/vllm-openai:${VLLM_IMAGE_TAG}"
fi
ls -lh "$VLLM_SIF"
apptainer exec --contain --cleanenv --home "$VLLM_CONTAINER_HOME:/root" "$VLLM_SIF" python3 -c "import vllm, torch; print('vllm', vllm.__version__, '| torch', torch.__version__)"
home_check
