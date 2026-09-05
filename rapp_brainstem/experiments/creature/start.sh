#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$ROOT/bootstrap-home/.brainstem/venv/bin/python" "$ROOT/payload/terrarium.py" "$@" --root "$ROOT"
