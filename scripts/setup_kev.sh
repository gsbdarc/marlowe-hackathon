#!/bin/bash
# One-time setup, run where you log in (an interactive Yen node, or the Marlowe login node), not in a job: Kev's code
# and Python environment, and a check that the models are in the shared cache.
#   source env/yens.sh      (or env/marlowe.sh)
#   bash scripts/setup_kev.sh
# Takes about 3 minutes and about 8 GB of scratch. Safe to rerun: finished steps are skipped.
set -euo pipefail
: "${KEV_HOME:?source env/yens.sh or env/marlowe.sh first}"
KEV_COMMIT=53cb0b5                       # the Kev commit DARC tested
UV=$KEV_HOME/bin/uv
mkdir -p "$KEV_HOME"
if [ ! -x "$UV" ]; then                  # uv is not installed on the clusters; install it into KEV_HOME
  # pip --target, not a venv: Marlowe's system Python has no ensurepip, so python3 -m venv fails there
  python3 -m pip install -q --target "$KEV_HOME/uv-pkg" "uv==0.13.1"
  mkdir -p "$KEV_HOME/bin" && ln -sf "$KEV_HOME/uv-pkg/bin/uv" "$UV"
fi
[ -d "$KEV_HOME/kev/.git" ] || git clone -q https://github.com/jaredpalmer/kev.git "$KEV_HOME/kev"
cd "$KEV_HOME/kev" && git checkout -q "$KEV_COMMIT"
"$UV" sync --extra serve
# The same kernels as Kev's own training image (modal_app.py at this commit). The Gated DeltaNet kernels need Triton
# 3.7.1: with the Triton 3.4 torch 2.8 pins, fla refuses its gated chunk backward on Hopper GPUs (H100, H200), and
# Triton 3.9 breaks fla 0.5.2's import.
"$UV" pip install --python .venv/bin/python -q flash-linear-attention==0.5.2 triton==3.7.1 wandb
# the DeltaNet short convolution's CUDA kernel (transformers falls back to a slow PyTorch conv without it). The wheel
# matches torch 2.8 / CUDA 12 / Python 3.13; --no-deps, or resolving its torch requirement puts back Triton 3.4
"$UV" pip install --python .venv/bin/python -q --no-deps \
  "https://github.com/Dao-AILab/causal-conv1d/releases/download/v1.7.0/causal_conv1d-1.7.0%2Bcu12torch2.8cxx11abiTRUE-cp313-cp313-linux_x86_64.whl"
# Models. DARC downloads them into the shared cache before the day. HF_HUB_OFFLINE=1 makes these lines only check
# they are there, and fail if one is missing: setup never downloads a model.
for m in jaredpalmer/kev-4b@v1.0 Qwen/Qwen3.5-4B-Base@main jaredpalmer/kev-27b@af0e6d551bdc2cc724f3e9d7a8bee1cd4fb8f7bf; do
  HF_HUB_OFFLINE=1 .venv/bin/hf download "${m%@*}" --revision "${m#*@}" > /dev/null 2>&1 || { echo "model missing from ${HF_HUB_CACHE:-$HF_HOME/hub}: $m" >&2; exit 1; }
  echo "model ok: $m"
done
# Kev-27B ships full weights but loads its tokenizer and config from its base: only those files are needed
m=Qwen/Qwen3.8-27B@1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0
HF_HUB_OFFLINE=1 .venv/bin/hf download "${m%@*}" --revision "${m#*@}" --exclude "*.safetensors" > /dev/null 2>&1 || { echo "tokenizer missing from ${HF_HUB_CACHE:-$HF_HOME/hub}: $m" >&2; exit 1; }
echo "tokenizer ok: $m"
echo "Kev ready: $KEV_HOME/kev at $(git rev-parse --short HEAD), $(.venv/bin/python --version)"
