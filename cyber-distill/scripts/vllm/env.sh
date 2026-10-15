# vLLM in a container, following gsbdarc/vllm_helper (https://github.com/gsbdarc/vllm_helper) and the
# RCpedia post "Fine-Tuning Open Source Models with Together + vLLM". Source, don't run.
# Large files (container image, model weights, caches) live under SCRATCH_BASE, never in home or
# project space. Set SCRATCH_BASE before sourcing to override the per-cluster default.
VLLM_IMAGE_TAG=v0.31.0                                # docker://vllm/vllm-openai:<tag>; "latest" on 2026-10-13
VLLM_HELPER_COMMIT=db1c923                            # gsbdarc/vllm_helper commit used
if [ -z "${SCRATCH_BASE:-}" ]; then
  case "$(hostname -f)" in
    *yen*) export SCRATCH_BASE=/scratch/shared/$USER ;;                 # Yens (as in the guide)
    *)     export SCRATCH_BASE=/scratch/m000106/gsb_hackathon/$USER ;;  # Marlowe
  esac
fi
export SCRATCH_BASE
export APPTAINER_CACHEDIR=$SCRATCH_BASE/.apptainer                  # image layers (default ~/.apptainer/cache)
export APPTAINER_CONFIGDIR=${APPTAINER_CONFIGDIR:-$SCRATCH_BASE/.apptainer-config}  # default ~/.apptainer
# Writable home for the container (what vllm.sh uses), so `apptainer exec` never writes to the real ~.
export VLLM_CONTAINER_HOME=$SCRATCH_BASE/vllm/home
for v in SCRATCH_BASE APPTAINER_CACHEDIR APPTAINER_CONFIGDIR VLLM_CONTAINER_HOME; do
  case "${!v}" in "$HOME"|"$HOME"/*) echo "scripts/vllm/env.sh: $v=${!v} is in home; point it at scratch" >&2; return 1 ;; esac
done
mkdir -p "$APPTAINER_CACHEDIR" "$APPTAINER_CONFIGDIR" "$VLLM_CONTAINER_HOME"
export VLLM_HELPER=$SCRATCH_BASE/vllm_helper
export VLLM_SIF=$SCRATCH_BASE/vllm/vllm-openai_${VLLM_IMAGE_TAG}.sif
