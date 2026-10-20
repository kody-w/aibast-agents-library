#!/bin/bash
# AIBAST RAPP one-liner:
#   curl -fsSL https://microsoft.github.io/aibast-agents-library/aibast-install.sh | bash
#
# AIBAST RAPP is the work twin of the Brainstem: it lives beside a personal Brainstem and never touches it.
# Its own folder (~/.aibast-rapp), its own sign-in, memory and agents, its own port (7272) and its own
# command (aibast-rapp). A personal Brainstem keeps ~/.brainstem, port 7071 and the brainstem command.
#
# 1. Runs this site's Brainstem installer (install.sh) unchanged, without launching, with HOME
#    pointed at ~/.aibast-rapp, so everything it writes lands there.
# 2. Adds the AIBAST Registry agent, checked byte for byte against this site's registry,
#    so AIBAST agents, offline mode and Send to Copilot Studio are one chat message away.
# 3. Installs the aibast-rapp command and launches the work twin on its own port.
# Arguments (such as --version or --no-launch) pass through to the installer.
# AIBAST_HOME and AIBAST_PORT change the folder and the port.
set -euo pipefail

SITE="https://microsoft.github.io/aibast-agents-library/"
RAW="https://raw.githubusercontent.com/microsoft/aibast-agents-library/main/"
REAL_HOME="$HOME"
AIBAST_HOME="${AIBAST_HOME:-$REAL_HOME/.aibast-rapp}"
AIBAST_PORT="${AIBAST_PORT:-7272}"
KERNEL="$AIBAST_HOME/.brainstem/src/rapp_brainstem"
VENV_PYTHON="$AIBAST_HOME/.brainstem/venv/bin/python"
CLI="$REAL_HOME/.local/bin/aibast-rapp"

installer="$(mktemp "${TMPDIR:-/tmp}/aibast-install-XXXXXX")"
trap 'rm -f "$installer"' EXIT
curl -fsSL "${SITE}install.sh" -o "$installer"

launch=true
for arg in "$@"; do [ "$arg" = "--no-launch" ] && launch=false; done

mkdir -p "$AIBAST_HOME"
chmod 700 "$AIBAST_HOME"
# The installer launches on 7071 itself, so it never launches here; the work twin starts below.
HOME="$AIBAST_HOME" bash "$installer" --no-launch "$@" </dev/null

echo "  Adding the AIBAST Registry agent..."
"$VENV_PYTHON" -I - "$SITE" "$RAW" "$KERNEL" "$AIBAST_PORT" <<'PY'
import hashlib, json, os, pathlib, sys, urllib.request
site, raw, kernel, port = sys.argv[1:5]
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
lines = text.splitlines()
if not any(l.startswith("AIBAST_REGISTRY_URL=") for l in lines):  # every AIBAST organ follows this one setting
    lines.append(f"AIBAST_REGISTRY_URL={site}registry.json")
# Never 7071, the personal Brainstem's port (the kernel's .env.example starts there); a port chosen
# by hand is kept.
lines = [l for l in lines if not (l.startswith("PORT=") and l[5:].strip() in ("", "7071"))]
if not any(l.startswith("PORT=") for l in lines):
    lines.append(f"PORT={port}")
if not any(l.startswith("OFFLINE_PORT=") for l in lines):  # offline mode beside it, never 7072
    lines.append(f"OFFLINE_PORT={int(port) + 1}")
new = "\n".join(lines) + "\n"
if new != text:
    part = env.with_name(".env.part")
    part.write_text(new, encoding="utf-8")
    os.chmod(part, 0o600)
    os.replace(part, env)
print("  ✓ AIBAST Registry agent added (checked against " + site + "registry.json)")
PY

# The aibast-rapp command runs the installer's own launcher with HOME set to the work twin's folder.
mkdir -p "$(dirname "$CLI")"
cat > "$CLI" <<EOF
#!/bin/bash
# AIBAST RAPP (work twin). Its folder: $AIBAST_HOME. Your personal Brainstem is untouched.
HOME="$AIBAST_HOME" exec "$AIBAST_HOME/.local/bin/brainstem" "\$@"
EOF
chmod +x "$CLI"
# The installer put ~/.local/bin on the PATH inside the work twin's folder only; someone with
# no personal Brainstem needs it in their own shell files too.
[ "$(uname -s)" = Darwin ] && [ ! -f "$REAL_HOME/.zshrc" ] && touch "$REAL_HOME/.zshrc"  # macOS starts zsh
for rc in "$REAL_HOME/.zshrc" "$REAL_HOME/.bashrc" "$REAL_HOME/.bash_profile"; do
    if [ -f "$rc" ] && ! grep -q '.local/bin' "$rc"; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$rc"
    fi
done
echo "  ✓ aibast-rapp command installed to $CLI"

if [ "$launch" = true ]; then
    port="$(sed -n 's/^PORT=//p' "$KERNEL/.env" | tail -1)"
    if lsof -ti:"$port" >/dev/null 2>&1; then
        echo "  Port $port is in use. If that is AIBAST RAPP it is already running: http://localhost:$port"
        echo "  Otherwise set AIBAST_PORT to a free port and run this again."
        exit 1
    fi
    if command -v open >/dev/null 2>&1 || command -v xdg-open >/dev/null 2>&1; then
        (
            for _ in $(seq 1 60); do
                curl -sf -o /dev/null --max-time 1 "http://localhost:$port/health" && break
                sleep 1
            done
            open "http://localhost:$port" 2>/dev/null || xdg-open "http://localhost:$port" 2>/dev/null || true
        ) &
    fi
    echo "  Starting AIBAST RAPP on http://localhost:$port ..."
    exec "$CLI" </dev/null
fi
