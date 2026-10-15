# Shared settings for cyber-distill on the Yens. Source, don't run:  source scripts/yens/env.sh
# Every Yen job sources this (after cd to the project). Caches and configs go to the per-user
# scratch /scratch/users/$USER, never home; see scripts/cache_env.sh. The vLLM image and models are
# under the same directory (SCRATCH_BASE in scripts/vllm/env.sh).
export CYBER_ROOT=/zfs/projects/darc/marlowe_hackathon/cyber-distill
export VENV=${VENV:-/zfs/projects/darc/marlowe_hackathon/.venv}    # shared hackathon venv (requirements.txt)
export USER_SCRATCH=/scratch/users/$USER
export HF_HOME=${HF_HOME:-$USER_SCRATCH/hf_cache}                  # student base model (Qwen3-1.7B)
source "$(dirname "${BASH_SOURCE[0]}")/../cache_env.sh" || return 1
