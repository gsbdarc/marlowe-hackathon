#!/bin/bash
# One-time: Python venv on Marlowe for the Stage 7 client and Stage 10 training.
#   source scripts/marlowe/env.sh && bash scripts/marlowe/setup_venv.sh
# Uses the Python on PATH; if Marlowe needs a module first, load it and note it in reports/environment.md.
set -euo pipefail
: "${VENV:?source scripts/marlowe/env.sh first}"
python3 --version
python3 -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r "$(dirname "$0")/../../requirements-marlowe.txt"
"$VENV/bin/python" -c "import torch, transformers, peft; print('torch', torch.__version__, 'cuda', torch.version.cuda, '| transformers', transformers.__version__, '| peft', peft.__version__)"
