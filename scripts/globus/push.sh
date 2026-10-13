#!/bin/bash
# Copy a project-relative path from the Yens to the same path on Marlowe, with checksums.
#   bash scripts/globus/push.sh data/final [label]
# A directory is copied recursively and gets a MANIFEST.sha256 written first, so the
# copy can be checked on Marlowe with: cd <dir> && sha256sum -c MANIFEST.sha256
# Waits for the task and prints its final status; log the task ID in reports/run_log.md.
set -euo pipefail
source "$(dirname "$0")/env.sh"
REL=${1:?usage: push.sh <project-relative path> [label]}
LABEL=${2:-cyber-distill $REL}
SRC="$YEN_ROOT/$REL"
if [ -d "$SRC" ]; then
  (cd "$SRC" && find . -type f ! -name MANIFEST.sha256 -print0 | sort -z | xargs -0 sha256sum > MANIFEST.sha256)
  OPTS=(--recursive)
else
  OPTS=()
fi
TASK=$("$GLOBUS" transfer "$YEN:$SRC" "$MARLOWE:$MARLOWE_ROOT/$REL" "${OPTS[@]}" \
  --sync-level checksum --verify-checksum --label "${LABEL:0:128}" --jmespath task_id --format unix)
echo "task $TASK"
"$GLOBUS" task wait "$TASK" --polling-interval 10 || true
"$GLOBUS" task show "$TASK" --format unix --jmespath '[status,files_transferred,bytes_transferred,faults]'
