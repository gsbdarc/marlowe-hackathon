# Settings for jobs on the Yens. Source it, don't run it:  source env/yens.sh
# Every cache and config goes to scratch, never home. Change DATA if your copy of the data is elsewhere.
export HACKATHON=/scratch/shared/marlowe_hackathon
export DATA=${DATA:-$HACKATHON/data/jev}                     # Jev-labeled Item 5.02 release (read only)
export WORK=${WORK:-/scratch/users/$USER/ceo-turnover}      # your training data, runs and results
export KEV_HOME=${KEV_HOME:-/scratch/users/$USER/kev}       # Kev code and its Python environment (setup_kev.sh)
export HF_HOME=${HF_HOME:-/scratch/users/$USER/hf}          # model weights
export UV_CACHE_DIR=$KEV_HOME/uv-cache UV_PYTHON_INSTALL_DIR=$KEV_HOME/uv-python
export XDG_CACHE_HOME=/scratch/users/$USER/.cache PIP_CACHE_DIR=/scratch/users/$USER/.cache/pip
export TRITON_CACHE_DIR=/scratch/users/$USER/.cache/triton TORCHINDUCTOR_CACHE_DIR=/scratch/users/$USER/.cache/inductor
export KEV_PREFIX_CACHE=0                                    # time every filing on its own
export HF_HUB_DISABLE_UPDATE_CHECK=1                         # Kev pins huggingface_hub below 2.0: skip the hf CLI's upgrade hint
export PY=$KEV_HOME/kev/.venv/bin/python
mkdir -p "$WORK" "$HF_HOME" "$XDG_CACHE_HOME"
