#!/bin/bash
# One-time: Python venv on Marlowe for the Stage 7 client and Stage 10 training.
#   source scripts/marlowe/env.sh && bash scripts/marlowe/setup_venv.sh
# Marlowe's system Python is 3.10, too old for the pinned pandas 3 / numpy 2.4, so this installs
# uv (a single binary, pinned) into scratch and lets it provide Python 3.12. The uv binary, the
# Python it downloads and its cache all live in scratch (home is 32 GB).
set -euo pipefail
: "${VENV:?source scripts/marlowe/env.sh first}"
UV_VERSION=0.13.1
PY_VERSION=3.12
TOOLS=$MARLOWE_SHARE/tools
# UV_CACHE_DIR, UV_PYTHON_INSTALL_DIR and XDG_CONFIG_HOME (where the installer writes its receipt)
# come from scripts/marlowe/env.sh, so nothing lands in home.
if [ ! -x "$TOOLS/uv" ] || ! "$TOOLS/uv" --version | grep -q " $UV_VERSION"; then
    curl -LsSf "https://astral.sh/uv/$UV_VERSION/install.sh" | env UV_INSTALL_DIR="$TOOLS" UV_NO_MODIFY_PATH=1 sh
fi
"$TOOLS/uv" --version
"$TOOLS/uv" venv --python "$PY_VERSION" "$VENV"
"$TOOLS/uv" pip install --python "$VENV/bin/python" -r "$(dirname "$0")/../../requirements-marlowe.txt"
"$VENV/bin/python" --version
"$VENV/bin/python" -c "import torch, transformers, peft; print('torch', torch.__version__, 'cuda', torch.version.cuda, '| transformers', transformers.__version__, '| peft', peft.__version__)"
