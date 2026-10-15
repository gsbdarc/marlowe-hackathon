# Shared settings for cyber-distill on Marlowe. Source, don't run:  source scripts/marlowe/env.sh
# Every Marlowe job sources this. Home on Marlowe is small (32 GB), so every tool that would write a
# cache or config under ~ is pointed at scratch here (the vLLM container does the same in vllm.sh).
# vLLM (teacher) runs in a container with its files under SCRATCH_BASE: see scripts/vllm/env.sh.
export CYBER_ROOT=/scratch/m000106/gsb_hackathon/cyber-distill     # data/, config/ (and code, if transferred here)
export MARLOWE_SHARE=/scratch/m000106/gsb_hackathon                # shared by the hackathon team
export HF_HOME=${HF_HOME:-$MARLOWE_SHARE/hf_cache}                 # student base model (Qwen3-1.7B) for training
export VENV=${VENV:-$MARLOWE_SHARE/envs/cyber}                     # client + training venv (requirements-marlowe.txt)
# Caches and configs out of home: per user, under $MARLOWE_SHARE/$USER (next to SCRATCH_BASE)
export USER_SCRATCH=$MARLOWE_SHARE/$USER
export XDG_CACHE_HOME=$USER_SCRATCH/.cache                         # default for pip, torch hub, etc.
export XDG_CONFIG_HOME=$USER_SCRATCH/.config                       # uv receipt, matplotlib, etc.
export XDG_DATA_HOME=$USER_SCRATCH/.local/share
export PIP_CACHE_DIR=$XDG_CACHE_HOME/pip
export UV_CACHE_DIR=$MARLOWE_SHARE/.cache/uv                       # shared: the venv is shared
export UV_PYTHON_INSTALL_DIR=$MARLOWE_SHARE/tools/python
export TORCH_HOME=$XDG_CACHE_HOME/torch
export TORCHINDUCTOR_CACHE_DIR=$XDG_CACHE_HOME/torchinductor
export TRITON_CACHE_DIR=$XDG_CACHE_HOME/triton                     # default ~/.triton
export CUDA_CACHE_PATH=$XDG_CACHE_HOME/nv                          # default ~/.nv
export MPLCONFIGDIR=$XDG_CACHE_HOME/matplotlib
export APPTAINER_CONFIGDIR=$USER_SCRATCH/.apptainer-config         # default ~/.apptainer (image cache: scripts/vllm/env.sh)
export PYTHONPYCACHEPREFIX=$XDG_CACHE_HOME/pycache
mkdir -p "$XDG_CACHE_HOME" "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$APPTAINER_CONFIGDIR" "$HF_HOME"
export TEACHER_MODEL=Qwen/Qwen3-235B-A22B-Instruct-2507-FP8
export TEACHER_REVISION=${TEACHER_REVISION:-}                      # FILL with the revision printed by scripts/vllm/download_model.sh
