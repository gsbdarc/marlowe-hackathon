# Shared settings for cyber-distill on Marlowe. Source, don't run:  source scripts/marlowe/env.sh
# Every Marlowe job sources this. Home on Marlowe is small (32 GB), so every tool that would write a
# cache or config under ~ is pointed at scratch here (the vLLM container does the same in vllm.sh).
# vLLM (teacher) runs in a container with its files under SCRATCH_BASE: see scripts/vllm/env.sh.
export CYBER_ROOT=/scratch/m000106/gsb_hackathon/cyber-distill     # data/, config/ (and code, if transferred here)
export MARLOWE_SHARE=/scratch/m000106/gsb_hackathon                # shared by the hackathon team
export HF_HOME=${HF_HOME:-$MARLOWE_SHARE/hf_cache}                 # student base model (Qwen3-1.7B) for training
export VENV=${VENV:-$MARLOWE_SHARE/envs/cyber}                     # client + training venv (requirements-marlowe.txt)
# Caches and configs out of home (scripts/cache_env.sh): per user, under $MARLOWE_SHARE/$USER
export USER_SCRATCH=$MARLOWE_SHARE/$USER
export UV_CACHE_DIR=$MARLOWE_SHARE/.cache/uv                       # shared: the venv is shared
export UV_PYTHON_INSTALL_DIR=$MARLOWE_SHARE/tools/python
source "$(dirname "${BASH_SOURCE[0]}")/../cache_env.sh" || return 1
export TEACHER_MODEL=Qwen/Qwen3-235B-A22B-Instruct-2507-FP8
export TEACHER_REVISION=${TEACHER_REVISION:-e156cb4efae43fbee1a1ab073f946a1377e6b969}  # from scripts/vllm/download_model.sh, 2026-10-16
