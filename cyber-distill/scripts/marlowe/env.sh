# Shared settings for cyber-distill on Marlowe. Source, don't run:  source scripts/marlowe/env.sh
# The Slurm account and partition are FILL placeholders in slurm/marlowe/*.slurm.
# vLLM (teacher) runs in a container with its files under SCRATCH_BASE: see scripts/vllm/env.sh.
export CYBER_ROOT=/scratch/m000106/gsb_hackathon/cyber-distill     # data/, config/ (and code, if transferred here)
export MARLOWE_SHARE=/scratch/m000106/gsb_hackathon                # shared by the hackathon team
export HF_HOME=${HF_HOME:-$MARLOWE_SHARE/hf_cache}                 # student base model (Qwen3-1.7B) for training
export VENV=${VENV:-$MARLOWE_SHARE/envs/cyber}                     # client + training venv (requirements-marlowe.txt)
export TEACHER_MODEL=Qwen/Qwen3-235B-A22B-Instruct-2507-FP8
export TEACHER_REVISION=${TEACHER_REVISION:-}                      # FILL with the revision printed by scripts/vllm/download_model.sh
