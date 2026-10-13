#!/bin/bash
# One-time Globus CLI setup on the Yens. Run in your own terminal (login is interactive).
#   bash scripts/globus/setup.sh
# Installs the CLI in its own venv (kept out of the shared hackathon .venv), logs in,
# and grants data_access consent for both collections. Each step prints a URL to open
# and asks for the code it gives you.
set -euo pipefail
source "$(dirname "$0")/env.sh"
if [ ! -x "$GLOBUS" ]; then
  python3 -m venv "$(dirname "$(dirname "$GLOBUS")")"
  "$(dirname "$GLOBUS")/pip" install -q globus-cli==3.43.0
fi
"$GLOBUS" whoami >/dev/null 2>&1 || "$GLOBUS" login --no-local-server
BASE='urn:globus:auth:scope:transfer.api.globus.org:all'
"$GLOBUS" session consent --no-local-server \
  "${BASE}[*https://auth.globus.org/scopes/${YEN}/data_access *https://auth.globus.org/scopes/${MARLOWE}/data_access]"
"$GLOBUS" ls "$MARLOWE:$MARLOWE_ROOT/" >/dev/null && echo "Globus ready: both collections reachable."
