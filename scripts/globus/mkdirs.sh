#!/bin/bash
# Create the project layout on Marlowe (/scratch/m000106/gsb_hackathon/cyber-distill). Safe to rerun.
set -uo pipefail
source "$(dirname "$0")/env.sh"
for d in "" /data /data/final /data/interim /data/teacher /models /config; do
  path="$MARLOWE:$MARLOWE_ROOT$d/"
  "$GLOBUS" ls "$path" >/dev/null 2>&1 || "$GLOBUS" mkdir "$path"
done
"$GLOBUS" ls "$MARLOWE:$MARLOWE_ROOT/"
