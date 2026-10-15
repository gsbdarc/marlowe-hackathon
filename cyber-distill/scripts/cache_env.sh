# Point every cache and config that would land under $HOME at scratch. Sourced by
# scripts/marlowe/env.sh and scripts/yens/env.sh, which set first:
#   USER_SCRATCH   per-user scratch dir (caches, configs)
#   HF_HOME        Hugging Face cache (student base model)
#   VENV           Python environment
# Returns 1 (and creates nothing) if any path is inside $HOME. Slurm jobs run `set -e` or
# `|| exit 1` after sourcing, so the job stops.
: "${USER_SCRATCH:?set USER_SCRATCH first}" "${HF_HOME:?set HF_HOME first}"
export XDG_CACHE_HOME=$USER_SCRATCH/.cache                         # default for pip, torch hub, etc. (~/.cache)
export XDG_CONFIG_HOME=$USER_SCRATCH/.config                       # uv receipt, matplotlib, etc. (~/.config)
export XDG_DATA_HOME=$USER_SCRATCH/.local/share                    # (~/.local/share)
export PIP_CACHE_DIR=$XDG_CACHE_HOME/pip
export UV_CACHE_DIR=${UV_CACHE_DIR:-$XDG_CACHE_HOME/uv}
export TORCH_HOME=$XDG_CACHE_HOME/torch
export TORCHINDUCTOR_CACHE_DIR=$XDG_CACHE_HOME/torchinductor
export TRITON_CACHE_DIR=$XDG_CACHE_HOME/triton                     # default ~/.triton
export CUDA_CACHE_PATH=$XDG_CACHE_HOME/nv                          # default ~/.nv
export MPLCONFIGDIR=$XDG_CACHE_HOME/matplotlib
export APPTAINER_CONFIGDIR=$USER_SCRATCH/.apptainer-config         # default ~/.apptainer (image cache: scripts/vllm/env.sh)
export PYTHONPYCACHEPREFIX=$XDG_CACHE_HOME/pycache
for v in USER_SCRATCH VENV HF_HOME XDG_CACHE_HOME XDG_CONFIG_HOME XDG_DATA_HOME PIP_CACHE_DIR UV_CACHE_DIR \
         TORCH_HOME TORCHINDUCTOR_CACHE_DIR TRITON_CACHE_DIR CUDA_CACHE_PATH MPLCONFIGDIR APPTAINER_CONFIGDIR \
         PYTHONPYCACHEPREFIX; do
  case "${!v:-}" in "$HOME"|"$HOME"/*) echo "scripts/cache_env.sh: $v=${!v} is in home; point it at scratch" >&2; return 1 ;; esac
done
mkdir -p "$XDG_CACHE_HOME" "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$APPTAINER_CONFIGDIR" "$HF_HOME"
