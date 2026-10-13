#!/bin/bash
# Wait until the vLLM server started by `vllm serve &` answers /v1/models (or give up).
#   bash scripts/vllm/wait_ready.sh [timeout_seconds, default 3600]
set -uo pipefail
: "${SCRATCH_BASE:?source scripts/vllm/env.sh first}"
T=${1:-3600}; S=$SCRATCH_BASE/vllm; start=$(date +%s)
while :; do
  if [ -f "$S/host.txt" ] && [ -f "$S/port.txt" ]; then
    url="http://$(<"$S/host.txt"):$(<"$S/port.txt")"
    if curl -sf "$url/v1/models" >/dev/null; then echo "vLLM ready at $url after $(( $(date +%s) - start ))s"; exit 0; fi
  fi
  if (( $(date +%s) - start > T )); then echo "vLLM not ready after ${T}s" >&2; exit 1; fi
  sleep 15
done
