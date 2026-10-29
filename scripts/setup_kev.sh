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
"$UV" pip install --python .venv/bin/python -q flash-linear-attention==0.5.2 wandb
# Models. DARC downloads them into the shared cache before the day; with HF_HUB_OFFLINE=1 (the Yens), these lines
# only check they are there, and fail if one is missing.
for m in jaredpalmer/kev-4b@v1.0 Qwen/Qwen3.5-4B-Base@main jaredpalmer/kev-27b@af0e6d551bdc2cc724f3e9d7a8bee1cd4fb8f7bf; do
  .venv/bin/hf download "${m%@*}" --revision "${m#*@}" > /dev/null 2>&1 || { echo "model missing from ${HF_HUB_CACHE:-$HF_HOME/hub}: $m" >&2; exit 1; }
  echo "model ok: $m"
done
echo "Kev ready: $KEV_HOME/kev at $(git rev-parse --short HEAD), $(.venv/bin/python --version)"
