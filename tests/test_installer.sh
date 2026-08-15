#!/bin/bash
# Tests for RAPP Brainstem installer and server
# Run: bash tests/test_installer.sh

set -e
PASS=0
FAIL=0
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

PYTHON_BIN=""
for candidate in "${PYTHON:-}" python3 python; do
    [ -n "$candidate" ] || continue
    if command -v "$candidate" >/dev/null 2>&1 \
       && "$candidate" -c 'import sys' >/dev/null 2>&1; then
        PYTHON_BIN="$candidate"
        break
    fi
done
[ -n "$PYTHON_BIN" ] || { echo "No runnable Python interpreter found" >&2; exit 1; }

pass() { PASS=$((PASS + 1)); echo "  ✓ $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  ✗ $1"; }

echo "=== RAPP Brainstem Tests ==="
echo ""

# ── install.sh tests ──────────────────────────────────────────────────────────

echo "--- install.sh ---"

if bash -n "$REPO_ROOT/install.sh" 2>/dev/null; then
    pass "install.sh is valid bash"
else
    fail "install.sh has syntax errors"
fi

if grep -q "RAPP Brainstem" "$REPO_ROOT/install.sh"; then
    pass "install.sh has brainstem branding"
else
    fail "install.sh missing brainstem branding"
fi

if grep -q '\.brainstem' "$REPO_ROOT/install.sh" && ! grep -q 'RAPP_HOME=.*\.rapp"' "$REPO_ROOT/install.sh"; then
    pass "install.sh targets ~/.brainstem"
else
    fail "install.sh should target ~/.brainstem"
fi

if grep -q 'BRAINSTEM_BIN.*local/bin' "$REPO_ROOT/install.sh" && grep -q 'brainstem.*WRAPPER' "$REPO_ROOT/install.sh"; then
    pass "install.sh creates brainstem CLI"
else
    fail "install.sh should create brainstem CLI wrapper"
fi

if grep -q 'microsoft/aibast-agents-library.git' "$REPO_ROOT/install.sh" && ! grep -q 'RAPPAI' "$REPO_ROOT/install.sh"; then
    pass "install.sh clones the public AIBAST repo"
else
    fail "install.sh should clone microsoft/aibast-agents-library"
fi

echo ""

# ── install.sh behaviour ─────────────────────────────────────────────────────
# These drive the REAL install.sh: its pure helpers are loaded by evaluating the
# script with its `main "$@"` invocation replaced by a no-op, and its argument
# parsing is exercised end to end (both cases exit before touching the disk).

echo "--- install.sh behaviour ---"

# Scratch space. Override with BRAINSTEM_TEST_TMP to keep temp files off /tmp.
SANDBOX_ROOT="${BRAINSTEM_TEST_TMP:-${TMPDIR:-/tmp}}"

load_installer() {
    # $1 = probe body, run in a throwaway shell with install.sh's functions loaded.
    bash -s "$REPO_ROOT/install.sh" "$1" <<'PROBE'
eval "$(grep -v '^main "\$@"$' "$1")"
set +e
eval "$2"
PROBE
}

VERSION_PROBE=$(load_installer '
    looks_like_version "0.7.12"          || { echo "rejected a real version"; exit 1; }
    looks_like_version "<!DOCTYPE html>" && { echo "accepted an HTML body"; exit 1; }
    looks_like_version ""                && { echo "accepted an empty version"; exit 1; }
    looks_like_version "0.7.12-rc1"      && { echo "accepted a non-numeric version"; exit 1; }
    version_gt "0.7.2" "0.7.1"           || { echo "0.7.2 should be newer"; exit 1; }
    version_gt "0.7.1" "0.7.2"           && { echo "0.7.1 is not newer"; exit 1; }
    noise=$(version_gt "<html>" "0.7.1" 2>&1)
    [ -z "$noise" ]                      || { echo "arithmetic noise: $noise"; exit 1; }
    echo ok
' 2>&1) || true
if [ "$(printf '%s' "$VERSION_PROBE" | tail -1)" = "ok" ]; then
    pass "remote version is validated before it is compared"
else
    fail "version guard: $VERSION_PROBE"
fi

ARG_RC=0
ARG_OUT=$(bash "$REPO_ROOT/install.sh" --verison --version 2>&1) || ARG_RC=$?
if [ "$ARG_RC" -eq 2 ] \
   && printf '%s' "$ARG_OUT" | grep -q -- '--version needs a value' \
   && printf '%s' "$ARG_OUT" | grep -q 'Ignoring unknown option'; then
    pass "bad arguments fail loudly instead of dying silently"
else
    fail "argument handling (rc=$ARG_RC): $ARG_OUT"
fi

HELP_RC=0
HELP_OUT=$(bash "$REPO_ROOT/install.sh" --help 2>&1) || HELP_RC=$?
if [ "$HELP_RC" -eq 0 ] && printf '%s' "$HELP_OUT" | grep -q 'Usage:'; then
    pass "--help prints usage and exits cleanly"
else
    fail "--help (rc=$HELP_RC): $HELP_OUT"
fi

# An aborted upgrade must put the user's files back. Build a throwaway repo,
# seed it like a real install (custom agent + edited soul + .env), then ask the
# installer for a version that does not exist and prove nothing was lost.
ROLLBACK=$(
    set +e
    SANDBOX=$(mktemp -d "$SANDBOX_ROOT/brainstem-rollback-XXXXXX") || { echo "no sandbox"; exit 1; }
    ORIGIN="$SANDBOX/origin"
    FAKE_HOME="$SANDBOX/home"
    SRC="$FAKE_HOME/.brainstem/src/rapp_brainstem"
    mkdir -p "$ORIGIN/rapp_brainstem/agents" "$FAKE_HOME"
    printf '0.1.0\n' > "$ORIGIN/rapp_brainstem/VERSION"
    printf 'default soul\n' > "$ORIGIN/rapp_brainstem/soul.md"
    printf 'class BasicAgent: pass\n' > "$ORIGIN/rapp_brainstem/agents/basic_agent.py"
    git -C "$ORIGIN" init -q
    git -C "$ORIGIN" symbolic-ref HEAD refs/heads/main
    git -C "$ORIGIN" config user.email t@localhost
    git -C "$ORIGIN" config user.name t
    git -C "$ORIGIN" add -A
    git -C "$ORIGIN" commit -qm init
    git clone -q "$ORIGIN" "$FAKE_HOME/.brainstem/src"
    git -C "$FAKE_HOME/.brainstem/src" config user.email t@localhost
    git -C "$FAKE_HOME/.brainstem/src" config user.name t
    printf 'MY CUSTOM SOUL\n' > "$SRC/soul.md"
    printf 'GITHUB_MODEL=my-model\n' > "$SRC/.env"
    printf '# mine\n' > "$SRC/agents/my_custom_agent.py"

    HOME="$FAKE_HOME" TMPDIR="$SANDBOX" TEST_REPO_URL="$ORIGIN" \
        bash -s "$REPO_ROOT/install.sh" >/dev/null 2>&1 <<'PROBE'
eval "$(grep -v '^main "\$@"$' "$1")"
REPO_URL="$TEST_REPO_URL"
PIN_VERSION="99.99.99"
install_brainstem
PROBE
    rc=$?
    problem=""
    [ "$rc" -ne 0 ] || problem="installer did not fail on a missing version"
    grep -q 'MY CUSTOM SOUL' "$SRC/soul.md" 2>/dev/null || problem="${problem:-soul.md lost}"
    grep -q 'my-model' "$SRC/.env" 2>/dev/null || problem="${problem:-.env lost}"
    [ -f "$SRC/agents/my_custom_agent.py" ] || problem="${problem:-custom agent lost}"
    if ls -d "$SANDBOX"/brainstem-upgrade-* >/dev/null 2>&1; then
        problem="${problem:-backup dir leaked}"
    fi
    rm -rf "$SANDBOX"
    if [ -n "$problem" ]; then echo "$problem"; else echo ok; fi
) || true
if [ "$(printf '%s' "$ROLLBACK" | tail -1)" = "ok" ]; then
    pass "aborted upgrade restores soul, .env, and custom agents"
else
    fail "upgrade rollback: $ROLLBACK"
fi

# Backups carry the user's .env (their GITHUB_TOKEN). A predictable /tmp path is
# pre-creatable by any other account on the machine.
if ! grep -q 'brainstem-upgrade-\$\$' "$REPO_ROOT/install.sh" \
   && grep -q 'new_backup_dir' "$REPO_ROOT/install.sh" \
   && grep -q 'chmod 700' "$REPO_ROOT/install.sh"; then
    pass "install.sh backups use private, unpredictable temp dirs"
else
    fail "install.sh should back up into a mktemp dir with 0700 permissions"
fi

# A pinned install must stay pinned — a pull at launch would move it to main.
if grep -qF 'if [ -z "$PIN_VERSION" ] && [ -d "$SRC_DIR/.git" ]; then' "$REPO_ROOT/install.sh" \
   && grep -qF '(-not $PIN_VERSION) -and (Test-Path' "$REPO_ROOT/install.ps1"; then
    pass "launch does not pull over a pinned version"
else
    fail "launch should skip the git pull when --version is pinned"
fi

# The installer must never take down an unrelated process holding port 7071.
if grep -q 'brainstem.py\*)' "$REPO_ROOT/install.sh" \
   && grep -q 'Not stopping it' "$REPO_ROOT/install.sh"; then
    pass "only a brainstem is killed to free port 7071"
else
    fail "install.sh should identify the port 7071 owner before killing it"
fi

# A PyPI outage must not leave the user without the `brainstem` command: the CLI
# wrapper and .env are written before dependencies on BOTH installers, in both
# the full-install and already-up-to-date paths.
if "$PYTHON_BIN" - "$REPO_ROOT" <<'PY'
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])


def code(path, start):
    text = path.read_text(encoding="utf-8")
    body = text[text.index(start):]
    return "\n".join(
        line for line in body.splitlines() if not line.lstrip().startswith("#")
    )


for name, body, cli, deps in (
    ("install.sh", code(root / "install.sh", "\nmain() {"),
     r"install_cli", r"setup_deps|ensure_deps"),
    ("install.ps1", code(root / "install.ps1", "\nfunction Main {"),
     r"Install-CLI", r"Setup-Dependencies|Ensure-Dependencies"),
):
    cli_at = [m.start() for m in re.finditer(cli, body)]
    dep_at = [m.start() for m in re.finditer(deps, body)]
    assert len(cli_at) >= 2 and len(dep_at) >= 2, (name, cli_at, dep_at)
    assert min(cli_at) < min(dep_at), f"{name}: fast path installs deps before the CLI"
    assert max(cli_at) < max(dep_at), f"{name}: full path installs deps before the CLI"
print("ok")
PY
then
    pass "CLI wrapper and .env are installed before dependencies"
else
    fail "a dependency failure would leave the user without the brainstem command"
fi

# An interrupted fresh install must not be able to delete the only checkout.
if grep -q 'NEW_SRC="\$SRC_DIR.new' "$REPO_ROOT/install.sh" \
   && grep -q 'mv "\$NEW_SRC" "\$SRC_DIR"' "$REPO_ROOT/install.sh"; then
    pass "fresh install clones to staging before replacing src"
else
    fail "fresh install should not remove src before the clone succeeds"
fi

echo ""

# ── install.ps1 tests ────────────────────────────────────────────────────────

echo "--- install.ps1 ---"

if grep -q "RAPP Brainstem" "$REPO_ROOT/install.ps1"; then
    pass "install.ps1 has brainstem branding"
else
    fail "install.ps1 missing brainstem branding"
fi

if grep -q '\.brainstem' "$REPO_ROOT/install.ps1"; then
    pass "install.ps1 targets ~/.brainstem"
else
    fail "install.ps1 should target ~/.brainstem"
fi

BOOTSTRAP_BOMS=$("$PYTHON_BIN" - "$REPO_ROOT" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
files = (
    "install.ps1",
    "deploy.ps1",
    "community_rapp/install.ps1",
    "rapp_ai/install.ps1",
)
print(" ".join(name for name in files if (root / name).read_bytes().startswith(b"\xef\xbb\xbf")))
PY
)
if [ -z "$BOOTSTRAP_BOMS" ]; then
    pass "PowerShell bootstrap scripts omit UTF-8 BOMs"
else
    fail "PowerShell 5.1 irm | iex rejects BOMs in: $BOOTSTRAP_BOMS"
fi

if grep -q 'read -r PROJECT_NAME </dev/tty' "$REPO_ROOT/community_rapp/install.sh"; then
    pass "piped CommunityRAPP installer reads prompts from the terminal"
else
    fail "community_rapp/install.sh should not consume its piped script as prompt input"
fi

if grep -q 'FRESH_SHIPPED' "$REPO_ROOT/install.sh" \
   && grep -q 'FreshShipped' "$REPO_ROOT/install.ps1"; then
    pass "repair installs preserve fresh bundled agents"
else
    fail "repair installs should restore only custom agents"
fi

echo ""

# ── install.cmd tests ────────────────────────────────────────────────────────

echo "--- install.cmd ---"

if grep -qi "brainstem" "$REPO_ROOT/install.cmd"; then
    pass "install.cmd references brainstem"
else
    fail "install.cmd should reference brainstem"
fi

echo ""

# ── skill.md tests ────────────────────────────────────────────────────────────

echo "--- skill.md ---"

if head -1 "$REPO_ROOT/skill.md" | grep -q '^---'; then
    pass "skill.md has YAML frontmatter"
else
    fail "skill.md missing YAML frontmatter"
fi

TIER_COUNT=$(grep -cE "^## Tier [0-9]" "$REPO_ROOT/skill.md" || true)
if [ "$TIER_COUNT" -ge 3 ]; then
    pass "skill.md has all 3 tiers"
else
    fail "skill.md missing tier content (found $TIER_COUNT)"
fi

# Pause points are the per-tier gates that stop autonomous execution and hand back
# to the user ("Do not proceed…", "Wait for…", "Only pause and ask…").
PAUSE_COUNT=$(grep -cE "Do not proceed|Wait for|Only pause" "$REPO_ROOT/skill.md" || true)
if [ "$PAUSE_COUNT" -ge 3 ]; then
    pass "skill.md has $PAUSE_COUNT pause points"
else
    fail "skill.md needs at least 3 pause points (found $PAUSE_COUNT)"
fi

if grep -q 'state.json' "$REPO_ROOT/skill.md"; then
    pass "skill.md saves state to disk"
else
    fail "skill.md should save state like Moltbook pattern"
fi

if grep -q "Do not proceed" "$REPO_ROOT/skill.md"; then
    pass "skill.md gates tier progression"
else
    fail "skill.md should gate tier progression"
fi

echo ""

# ── index.html tests ─────────────────────────────────────────────────────────

echo "--- index.html ---"

# The landing page names Tier 2 by its installer path ("Hippocampus") or its tier
# metaphor ("Spinal Cord") — accept either so a vocabulary choice doesn't fail the test.
if grep -q "Brainstem" "$REPO_ROOT/index.html" \
   && { grep -q "Spinal Cord" "$REPO_ROOT/index.html" || grep -q "Hippocampus" "$REPO_ROOT/index.html"; } \
   && grep -q "Nervous System" "$REPO_ROOT/index.html"; then
    pass "index.html has all 3 tiers"
else
    fail "index.html missing tier content"
fi

if grep -q "curl -fsSL" "$REPO_ROOT/index.html"; then
    pass "index.html has one-liner install command"
else
    fail "index.html missing one-liner"
fi

if grep -q "localhost:7071" "$REPO_ROOT/index.html"; then
    pass "index.html has health check"
else
    fail "index.html missing health check"
fi

echo ""

# ── README.md tests ───────────────────────────────────────────────────────────

echo "--- README.md ---"

if head -8 "$REPO_ROOT/README.md" | grep -q "AIBAST Agents Library" \
   && grep -q "Brainstem" "$REPO_ROOT/README.md"; then
    pass "README.md leads with AIBAST and documents Brainstem"
else
    fail "README.md should preserve AIBAST library identity and Brainstem guidance"
fi

if grep -q "curl -fsSL" "$REPO_ROOT/README.md"; then
    pass "README.md has one-liner"
else
    fail "README.md missing one-liner"
fi

if grep -q "Tier 1" "$REPO_ROOT/README.md" && grep -q "Tier 2" "$REPO_ROOT/README.md" && grep -q "Tier 3" "$REPO_ROOT/README.md"; then
    pass "README.md has all 3 tiers"
else
    fail "README.md missing tier content"
fi

echo ""

# ── copilot-instructions.md tests ────────────────────────────────────────────

echo "--- .github/copilot-instructions.md ---"

if grep -q "Brainstem" "$REPO_ROOT/.github/copilot-instructions.md" && grep -q "Spinal Cord" "$REPO_ROOT/.github/copilot-instructions.md"; then
    pass "copilot-instructions.md has progressive architecture"
else
    fail "copilot-instructions.md missing progressive architecture"
fi

if grep -q "pytest" "$REPO_ROOT/.github/copilot-instructions.md"; then
    pass "copilot-instructions.md has test commands"
else
    fail "copilot-instructions.md missing test commands"
fi

echo ""

# ── brainstem server tests ────────────────────────────────────────────────────

echo "--- brainstem server ---"

if [ -f "$REPO_ROOT/rapp_brainstem/requirements.txt" ]; then
    pass "requirements.txt exists"
else
    fail "requirements.txt missing"
fi

for endpoint in "/chat" "/health" "/login" "/models" "/agents" "/version"; do
    if grep -q "\"$endpoint\"" "$REPO_ROOT/rapp_brainstem/brainstem.py"; then
        pass "brainstem.py has $endpoint endpoint"
    else
        fail "brainstem.py missing $endpoint endpoint"
    fi
done

# BasicAgent lives in agents/ (also mirrored to the repo copy the shim loads).
if grep -q "def perform" "$REPO_ROOT/rapp_brainstem/agents/basic_agent.py" && grep -q "def to_tool" "$REPO_ROOT/rapp_brainstem/agents/basic_agent.py"; then
    pass "basic_agent.py has perform() and to_tool()"
else
    fail "basic_agent.py missing required methods"
fi

echo ""

# ── bundled agents ────────────────────────────────────────────────────────────

echo "--- bundled agents ---"

# Each bundled agent file must define a class that loads and exposes a valid tool
# schema. This is the contract every *_agent.py must satisfy to be discoverable.
for agent_file in manage_memory_agent context_memory_agent hacker_news_agent; do
    if [ -f "$REPO_ROOT/rapp_brainstem/agents/${agent_file}.py" ]; then
        pass "bundled agent present: ${agent_file}.py"
    else
        fail "bundled agent missing: ${agent_file}.py"
    fi
done

# Drive the REAL loader (which registers the utils/basic_agent shims the memory
# agents import) so this exercises the same path a live /chat request would — but
# against a temp dir holding only the GIT-TRACKED agents, so a local drop-in can't
# fail (or pip-install mid-run during) a check of the BUNDLED set. The `|| true`
# keeps a failure reportable instead of aborting the whole suite under set -e.
TMP_AGENTS=$(mktemp -d "${TMPDIR:-/tmp}/brainstem-agents-XXXXXX")
for f in "$REPO_ROOT"/rapp_brainstem/agents/*.py; do
    base=$(basename "$f")
    if (cd "$REPO_ROOT" && git ls-files --error-unmatch "rapp_brainstem/agents/$base" >/dev/null 2>&1); then
        cp "$f" "$TMP_AGENTS/"
    fi
done
# Not a git checkout (tarball)? Fall back to everything rather than testing nothing.
if ! ls "$TMP_AGENTS"/*_agent.py >/dev/null 2>&1; then
    cp "$REPO_ROOT"/rapp_brainstem/agents/*.py "$TMP_AGENTS/" 2>/dev/null || true
fi
AGENT_TEST=$(cd "$REPO_ROOT/rapp_brainstem" && AGENTS_PATH="$TMP_AGENTS" "$PYTHON_BIN" -c "
import sys
sys.path.insert(0, '.')
import brainstem
agents = brainstem.load_agents()
names = set(agents)
assert 'ManageMemory' in names and 'ContextMemory' in names, names
for a in agents.values():
    t = a.to_tool()
    assert t['type'] == 'function' and t['function']['name'], t
print('ok')
" 2>&1) || true
rm -rf "$TMP_AGENTS"
if [ "$(printf '%s' "$AGENT_TEST" | tail -1)" = "ok" ]; then
    pass "bundled agents load and expose valid tool schemas"
else
    fail "bundled agent runtime test failed: $AGENT_TEST"
fi

echo ""

# ── docs/ & tracking tests ───────────────────────────────────────────────────

echo "--- docs & tracking ---"

if [ -f "$REPO_ROOT/docs/index.html" ] && grep -q "Brainstem" "$REPO_ROOT/docs/index.html"; then
    pass "docs/index.html has brainstem content"
else
    fail "docs/index.html missing or stale"
fi

if [ -f "$REPO_ROOT/docs/install.sh" ] && grep -q "brainstem" "$REPO_ROOT/docs/install.sh" -i; then
    pass "docs/install.sh exists for GitHub Pages curl"
else
    fail "docs/install.sh missing (needed for curl one-liner via GitHub Pages)"
fi

if [ ! -f "$REPO_ROOT/docs/copilot-install.html" ]; then
    pass "stale docs/copilot-install.html removed"
else
    fail "docs/copilot-install.html should be removed (stale)"
fi

if grep -q ".brainstem_data" "$REPO_ROOT/.gitignore" && grep -q ".remote_agents" "$REPO_ROOT/.gitignore"; then
    pass ".gitignore excludes runtime artifacts"
else
    fail ".gitignore should exclude .brainstem_data/ and .remote_agents/"
fi

echo ""

# ── unit tests ────────────────────────────────────────────────────────────────

echo "--- unit tests (tests/) ---"
cd "$REPO_ROOT/rapp_brainstem"
if "$PYTHON_BIN" -m pytest tests/ -x --tb=short -q 2>&1; then
    pass "unit tests passed"
else
    fail "unit tests failed"
fi

if "$PYTHON_BIN" tests/test_model_selection.py >/dev/null 2>&1 \
   && "$PYTHON_BIN" tests/test_streaming.py >/dev/null 2>&1; then
    pass "documented standalone test runners work"
else
    fail "standalone model-selection or streaming test runner failed"
fi

echo ""

# ── Summary ───────────────────────────────────────────────────────────────────

TOTAL=$((PASS + FAIL))
echo "=== Results: $PASS/$TOTAL passed ==="
if [ "$FAIL" -gt 0 ]; then
    echo "  $FAIL test(s) failed"
    exit 1
else
    echo "  All tests passed! ✓"
    exit 0
fi
