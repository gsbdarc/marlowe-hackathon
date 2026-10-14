# Settings for the Kev tutorial (kev/TUTORIAL.md) on the Yens. Source, don't run:  source kev/env.sh
# Kev (github.com/jaredpalmer/kev) needs Python 3.12-3.13 and torch < 2.9, so it gets its own venv instead of the
# shared ../.venv (Python 3.11, torch 2.14). Source code, venv, uv, caches and weights all live in scratch.
KEV_REF=0a6d3fafeee7f3f76a9a4a522bf8b9d5b50bd7e5      # jaredpalmer/kev main on 2026-10-13
UV_VERSION=0.12.24
export KEV_SCRATCH=${KEV_SCRATCH:-/scratch/users/$USER}
export KEV_HOME=$KEV_SCRATCH/kev                        # kev source at KEV_REF
export KEV_VENV=$KEV_SCRATCH/kev-venv                   # Python 3.13 venv with kev installed
export UV=$KEV_SCRATCH/uv-tool/bin/uv                   # uv in its own small venv
export UV_CACHE_DIR=$KEV_SCRATCH/uv_cache
export UV_PYTHON_INSTALL_DIR=$KEV_SCRATCH/uv_python
export HF_HOME=$KEV_SCRATCH/hf_cache                    # Kev adapters, Qwen3.5 bases, Kev-27B
# Inputs are read from the shared project copy and never written: frozen samples and, once Stage 7 is done,
# data/final/teacher_labels.parquet.
export CYBER_DATA=${CYBER_DATA:-/zfs/projects/darc/marlowe_hackathon/cyber-distill/data/final}
# Released checkpoints at the Kev 1.0 tag (README "Kev 1.0"): Hub repo@revision
export KEV_4B=jaredpalmer/kev-4b@v1.0
export KEV_9B=jaredpalmer/kev-9b@v1.0
export KEV_27B=jaredpalmer/kev-27b@v1.0
