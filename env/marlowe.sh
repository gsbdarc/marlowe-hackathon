# Settings for jobs on Marlowe. Source it, don't run it:  source env/marlowe.sh
# Marlowe home is 32 GB, so code, weights, caches and runs all go to project scratch.
export SHARE=${SHARE:-/scratch/m000106/gsb_hackathon}
export DATA=${DATA:-$SHARE/ceo-turnover/data/jev}           # Jev-labeled Item 5.02 release (read only)
export WORK=${WORK:-$SHARE/$USER/ceo-turnover}               # your training data, runs and results
export KEV_HOME=${KEV_HOME:-$SHARE/$USER/kev}                # Kev code and its Python environment (setup_kev.sh)
export HF_HOME=${HF_HOME:-$SHARE/hf_cache}                   # shared model weights
export HF_HUB_OFFLINE=1                                      # every model is pre-downloaded by DARC: never download
export UV_CACHE_DIR=$KEV_HOME/uv-cache UV_PYTHON_INSTALL_DIR=$KEV_HOME/uv-python
export XDG_CACHE_HOME=$SHARE/$USER/.cache PIP_CACHE_DIR=$SHARE/$USER/.cache/pip
export TRITON_CACHE_DIR=$SHARE/$USER/.cache/triton TORCHINDUCTOR_CACHE_DIR=$SHARE/$USER/.cache/inductor
export KEV_PREFIX_CACHE=0
export HF_HUB_DISABLE_UPDATE_CHECK=1                         # Kev pins huggingface_hub below 2.0: skip the hf CLI's upgrade hint
export PY=$KEV_HOME/kev/.venv/bin/python
export MARLOWE_ACCOUNT=${MARLOWE_ACCOUNT:-marlowe-m000106}
mkdir -p "$WORK" "$HF_HOME" "$XDG_CACHE_HOME"
