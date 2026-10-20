#!/bin/bash
# AIBAST Brainstem one-liner:
#   curl -fsSL https://microsoft.github.io/aibast-agents-library/aibast-install.sh | bash
#
# 1. Runs this site's Brainstem installer (install.sh) unchanged, without launching.
# 2. Adds the AIBAST Registry agent, checked byte for byte against this site's registry,
#    so AIBAST agents, offline mode and Send to Copilot Studio are one chat message away.
# 3. Runs the installer again, which finds everything up to date and launches as usual.
# Arguments (such as --version or --no-launch) pass through to the installer.
set -euo pipefail

SITE="https://microsoft.github.io/aibast-agents-library/"
RAW="https://raw.githubusercontent.com/microsoft/aibast-agents-library/main/"
KERNEL="$HOME/.brainstem/src/rapp_brainstem"
VENV_PYTHON="$HOME/.brainstem/venv/bin/python"

installer="$(mktemp "${TMPDIR:-/tmp}/aibast-install-XXXXXX")"
trap 'rm -f "$installer"' EXIT
curl -fsSL "${SITE}install.sh" -o "$installer"

launch=true
for arg in "$@"; do [ "$arg" = "--no-launch" ] && launch=false; done

bash "$installer" --no-launch "$@" </dev/null

echo "  Adding the AIBAST Registry agent..."
"$VENV_PYTHON" -I - "$SITE" "$RAW" "$KERNEL" <<'PY'
import hashlib, json, os, pathlib, sys, urllib.request
site, raw, kernel = sys.argv[1:4]
with urllib.request.urlopen(site + "registry.json", timeout=60) as r:
    entry = next(a for a in json.load(r)["agents"] if a["name"] == "@aibast-agents-library/aibast-registry")
with urllib.request.urlopen(raw + entry["_file"], timeout=60) as r:
    body = r.read()
if hashlib.sha256(body).hexdigest() != entry["_sha256"]:
    sys.exit("  The AIBAST Registry agent did not match the registry, so it was not added.")
agents = pathlib.Path(kernel) / "agents"
part = agents / ".aibast_registry_agent.py.part"
part.write_bytes(body)
os.replace(part, agents / "aibast_registry_agent.py")
env = pathlib.Path(kernel) / ".env"
text = env.read_text(encoding="utf-8") if env.exists() else ""
if "AIBAST_REGISTRY_URL=" not in text:  # every AIBAST organ follows this one setting
    with env.open("a", encoding="utf-8") as f:
        f.write(("" if text.endswith("\n") or not text else "\n") + f"AIBAST_REGISTRY_URL={site}registry.json\n")
    os.chmod(env, 0o600)
print("  ✓ AIBAST Registry agent added (checked against " + site + "registry.json)")
PY

if [ "$launch" = true ]; then
    # Under curl | bash this script arrives on stdin; the installer must not read the rest of it.
    bash "$installer" "$@" </dev/null
fi
