#!/bin/bash
# One-time setup on a login node: Kev's code and Python environment, plus the Kev-4B weights.
#   source env/yens.sh      (or env/marlowe.sh)
#   bash scripts/setup_kev.sh
# Takes about 10 minutes and about 25 GB of scratch. Safe to rerun: finished steps are skipped.
set -euo pipefail
: "${KEV_HOME:?source env/yens.sh or env/marlowe.sh first}"
KEV_COMMIT=53cb0b5                       # the Kev commit DARC tested
UV=$KEV_HOME/bin/uv
mkdir -p "$KEV_HOME"
if [ ! -x "$UV" ]; then                  # uv is not installed on the clusters; install it into KEV_HOME
  python3 -m venv "$KEV_HOME/uv-venv" && "$KEV_HOME/uv-venv/bin/pip" install -q "uv==0.13.1"
  mkdir -p "$KEV_HOME/bin" && ln -sf "$KEV_HOME/uv-venv/bin/uv" "$UV"
fi
[ -d "$KEV_HOME/kev/.git" ] || git clone -q https://github.com/jaredpalmer/kev.git "$KEV_HOME/kev"
cd "$KEV_HOME/kev" && git checkout -q "$KEV_COMMIT"
"$UV" sync --extra serve
"$UV" pip install --python .venv/bin/python -q flash-linear-attention==0.5.2 wandb
# Weights, fetched here so no GPU time is spent downloading
.venv/bin/hf download jaredpalmer/kev-4b --revision v1.0 > /dev/null
.venv/bin/hf download Qwen/Qwen3.5-4B-Base > /dev/null
echo "Kev ready: $KEV_HOME/kev at $(git rev-parse --short HEAD), $(.venv/bin/python --version)"
