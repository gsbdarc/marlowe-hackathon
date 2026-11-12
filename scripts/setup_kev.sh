#!/bin/bash
# Checks the shared Kev and the models, where you log in (an interactive Yen node, or the Marlowe login node):
#   source env/yens.sh      (or env/marlowe.sh)
#   bash scripts/setup_kev.sh
# It never changes Kev. KEV_HOME is one Kev for everyone, which setup/setup.sh builds with KEV_BUILD=1: Kev's code and
# Python environment, about 3 minutes and 8 GB. Safe to rerun: finished steps are skipped.
set -euo pipefail
: "${KEV_HOME:?source env/yens.sh or env/marlowe.sh first}"
KEV_COMMIT=53cb0b5                       # the Kev commit DARC tested
UV=$KEV_HOME/bin/uv
if [ "${KEV_BUILD:-0}" != 1 ]; then
  [ -x "$KEV_HOME/kev/.venv/bin/python" ] \
    || { echo "no Kev in $KEV_HOME: the instructors build it with setup/setup.sh" >&2; exit 1; }
  echo "using the shared Kev in $KEV_HOME"
  cd "$KEV_HOME/kev"
else
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
fi
# Models. DARC downloads them into the shared cache before the day. HF_HUB_OFFLINE=1 makes these lines only check
# they are there: setup never downloads a model. The Intermediate track needs only the 4B models, so a missing one fails
# setup; Kev-27B is for the Advanced track, so a missing Kev-27B only prints a note.
have() { HF_HUB_OFFLINE=1 .venv/bin/hf download "${1%@*}" --revision "${1#*@}" "${@:2}" > /dev/null 2>&1; }
CACHE=${HF_HUB_CACHE:-$HF_HOME/hub}
for m in jaredpalmer/kev-4b@v1.0 Qwen/Qwen3.5-4B-Base@main; do
  have "$m" || { echo "model missing from $CACHE: $m" >&2; exit 1; }
  echo "model ok: $m"
done
# Kev-27B ships full weights but loads its tokenizer and config from its base: only those files are needed
m=jaredpalmer/kev-27b@af0e6d551bdc2cc724f3e9d7a8bee1cd4fb8f7bf
t=Qwen/Qwen3.8-27B@1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0
if have "$m" && have "$t" --exclude "*.safetensors"; then
  echo "model ok: $m"
  echo "tokenizer ok: $t"
else
  echo "Kev-27B not in $CACHE: fine for the Beginner and Intermediate tracks; the Advanced track (A1 on) needs it"
fi
# the shared Kev belongs to another user, so git needs safe.directory to read its commit
echo "Kev ready: $KEV_HOME/kev at $(git -c safe.directory='*' rev-parse --short HEAD), $(.venv/bin/python --version)"
