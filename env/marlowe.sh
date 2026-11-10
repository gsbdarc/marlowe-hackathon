# Settings for jobs on Marlowe. Source it, don't run it:  source env/marlowe.sh
# Marlowe home is 32 GB, so code, weights, caches and runs all go to the class's scratch space, /scratch/c001.
export SHARE=${SHARE:-/scratch/c001/marlowe-hackathon}      # shared and read only: data, models, container
export ME=${ME:-/scratch/c001/users/$USER}                   # yours: your clone, Kev, runs and caches
export DATA=${DATA:-$SHARE/data/jev}                         # Jev-labeled Item 5.02 release (read only)
export WORK=${WORK:-$ME/ceo-turnover}                        # your training data, runs and results
export KEV_HOME=${KEV_HOME:-$ME/kev}                         # Kev code and its Python environment (setup_kev.sh)
export HF_HOME=${HF_HOME:-$SHARE/hf_cache}                   # shared model weights
export HF_HUB_OFFLINE=1                                      # every model is pre-downloaded by DARC: never download
export UV_CACHE_DIR=$KEV_HOME/uv-cache UV_PYTHON_INSTALL_DIR=$KEV_HOME/uv-python
export XDG_CACHE_HOME=$ME/.cache PIP_CACHE_DIR=$ME/.cache/pip
export TRITON_CACHE_DIR=$ME/.cache/triton TORCHINDUCTOR_CACHE_DIR=$ME/.cache/inductor
export APPTAINER_CACHEDIR=$ME/.apptainer_cache   # Marlowe's Apptainer guide: not the 32 GB home
export KEV_PREFIX_CACHE=0
export HF_HUB_DISABLE_UPDATE_CHECK=1                         # Kev pins huggingface_hub below 2.0: skip the hf CLI's upgrade hint
export PY=$KEV_HOME/kev/.venv/bin/python
export MARLOWE_ACCOUNT=${MARLOWE_ACCOUNT:-marlowe-c001}
mkdir -p "$WORK" "$HF_HOME" "$XDG_CACHE_HOME"
