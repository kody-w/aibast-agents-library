#!/bin/bash
set -euo pipefail

# Experimental creature profile; the official aka.ms/rapp installer stays intact.
SOURCE_URL="${RAPP_TERRARIUM_SOURCE_URL:-https://raw.githubusercontent.com/kody-w/aibast-agents-library/astra/brainstem-creature}"
PYTHON=""
for candidate in python3.11 python3.12 python3.13 python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'; then
    PYTHON="$candidate"
    break
  fi
done
if [[ -z $PYTHON ]]; then
  printf 'Python 3.11+ is required. Install the standard Brainstem from https://aka.ms/rapp first.\n' >&2
  exit 1
fi

TEMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/brainstem-creature.XXXXXX")"
cleanup() {
  rm -f "$TEMP_DIR/setup.py"
  rmdir "$TEMP_DIR"
}
trap cleanup EXIT
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 \
  "$SOURCE_URL/rapp_brainstem/experiments/creature/setup.py" -o "$TEMP_DIR/setup.py"
"$PYTHON" "$TEMP_DIR/setup.py" --source-url "$SOURCE_URL" "$@"
