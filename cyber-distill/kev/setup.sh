#!/bin/bash
# One-time: uv, the kev source at KEV_REF, and a Python 3.13 venv with kev and the Gated DeltaNet kernels that the
# Qwen3.5 backbones need. Downloads only (a few GB), so a login node is fine.
#   bash kev/setup.sh            (from cyber-distill/)
set -euo pipefail
source "$(dirname "$0")/env.sh"
mkdir -p "$KEV_SCRATCH"
if [ ! -x "$UV" ]; then
  python3 -m venv "$(dirname "$(dirname "$UV")")"
  "$(dirname "$UV")/pip" install -q "uv==$UV_VERSION"
fi
"$UV" --version
if [ ! -d "$KEV_HOME/.git" ]; then
  git clone -q https://github.com/jaredpalmer/kev.git "$KEV_HOME"
fi
git -C "$KEV_HOME" fetch -q origin && git -C "$KEV_HOME" checkout -q "$KEV_REF"
echo "kev at $(git -C "$KEV_HOME" log --oneline -1)"
# kev's own lockfile, installed into KEV_VENV instead of $KEV_HOME/.venv
cd "$KEV_HOME"
UV_PROJECT_ENVIRONMENT=$KEV_VENV "$UV" sync -q --frozen --python 3.13 --extra serve
# Same kernels as kev's Modal image (skills/kev-finetune/scripts/kev_modal.py): torch 2.8 pins triton 3.4, but
# flash-linear-attention needs triton >= 3.7.1 on Hopper GPUs, so they go in after the lockfile. A later `uv sync`
# removes them; rerun this script instead.
"$UV" pip install -q --python "$KEV_VENV/bin/python" "flash-linear-attention==0.5.2" "triton>=3.7.1"
"$KEV_VENV/bin/python" -c "import kev, torch, transformers, peft, fla, triton; print('python', __import__('sys').version.split()[0], '| torch', torch.__version__, 'cuda', torch.version.cuda, '| transformers', transformers.__version__, '| peft', peft.__version__, '| fla', fla.__version__, '| triton', triton.__version__)"
