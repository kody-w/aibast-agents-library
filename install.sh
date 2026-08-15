#!/bin/bash
set -e

# RAPP Brainstem Installer
# Usage: curl -fsSL https://microsoft.github.io/aibast-agents-library/install.sh | bash
# Pin a version: curl ... install.sh | bash -s -- --version v0.6.0

BRAINSTEM_HOME="$HOME/.brainstem"
BRAINSTEM_BIN="$HOME/.local/bin"
VENV_DIR="$BRAINSTEM_HOME/venv"
REPO_URL="https://github.com/microsoft/aibast-agents-library.git"
REMOTE_VERSION_URL="https://raw.githubusercontent.com/microsoft/aibast-agents-library/main/rapp_brainstem/VERSION"
PIN_VERSION=""

# The user's files live inside the checkout but are NOT in git. Every path the
# backup/restore logic touches is defined once, here, so the exit trap can put
# them back without depending on any function's locals.
SRC_DIR="$BRAINSTEM_HOME/src"
BRAINSTEM_SRC="$SRC_DIR/rapp_brainstem"
AGENTS_DIR="$BRAINSTEM_SRC/agents"
SOUL_FILE="$BRAINSTEM_SRC/soul.md"
ENV_FILE="$BRAINSTEM_SRC/.env"
DATA_DIR="$BRAINSTEM_SRC/.brainstem_data"
LOCAL_VERSION_FILE="$BRAINSTEM_SRC/VERSION"
# Outstanding backup directories — non-empty only while an install is mid-flight.
UPGRADE_BACKUP=""
FRESH_BACKUP=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

read_input() {
    local prompt="$1" default="$2" result
    if [ -t 0 ]; then
        read -p "$prompt" result
    else
        read -p "$prompt" result < /dev/tty
    fi
    echo "${result:-$default}"
}

usage() {
    cat <<'USAGE'
  RAPP Brainstem installer

  Usage:
    curl -fsSL https://microsoft.github.io/aibast-agents-library/install.sh | bash
    curl -fsSL https://microsoft.github.io/aibast-agents-library/install.sh | bash -s -- --version v0.6.0

  Options:
    --version <vX.Y.Z>   Install/pin a specific release instead of the latest
    -h, --help           Show this help and exit

  The installer preserves your soul.md, .env, custom agents, and memories.
USAGE
}

# ── temp-file safety ──────────────────────────────────────────────────────────
# Backups hold the user's .env — which carries their GITHUB_TOKEN — so they must
# never land on a predictable, world-readable path (the old /tmp/...-$$ form was
# guessable and pre-creatable by any other user on the box). mktemp gives us an
# unguessable name we know we created; 700 keeps the contents ours.
new_backup_dir() {
    local d
    d=$(mktemp -d "${TMPDIR:-/tmp}/brainstem-$1-XXXXXX") || return 1
    chmod 700 "$d" 2>/dev/null || true
    printf '%s' "$d"
}

# Put the user's files back from a backup, then delete it. Used both by the happy
# path's caller (after which the global is cleared) and by the exit trap, so an
# install that dies mid-upgrade can never leave the user without their soul,
# config, or custom agents — and never leaves their token sitting in /tmp.
restore_backup() {
    local backup="$1"
    [ -n "$backup" ] && [ -d "$backup" ] || return 0
    if [ ! -d "$BRAINSTEM_SRC" ]; then
        # There is no checkout to restore into (the install died between removing
        # the old tree and moving the new one in). This backup is the only copy of
        # the user's work — park it somewhere they can find, never delete it.
        local rescue="$BRAINSTEM_HOME/rescued-$(basename "$backup")"
        if mkdir -p "$BRAINSTEM_HOME" 2>/dev/null && mv "$backup" "$rescue" 2>/dev/null; then
            echo -e "  ${YELLOW}⚠${NC} Saved your soul, config, and agents to ${rescue}"
        else
            echo -e "  ${YELLOW}⚠${NC} Your soul, config, and agents are still at ${backup}"
        fi
        return 0
    fi
    [ -f "$backup/soul.md" ] && cp "$backup/soul.md" "$SOUL_FILE" 2>/dev/null || true
    [ -f "$backup/.env" ] && cp "$backup/.env" "$ENV_FILE" 2>/dev/null || true
    if [ -d "$backup/agents" ] && [ -d "$AGENTS_DIR" ]; then
        local af fn
        for af in "$backup/agents"/*.py; do
            [ -f "$af" ] || continue
            fn=$(basename "$af")
            # Never clobber a file the checkout ships — only fill in what is gone.
            [ -e "$AGENTS_DIR/$fn" ] || cp "$af" "$AGENTS_DIR/$fn" 2>/dev/null || true
        done
    fi
    [ -d "$backup/.brainstem_data" ] && [ ! -d "$DATA_DIR" ] && \
        cp -R "$backup/.brainstem_data" "$DATA_DIR" 2>/dev/null || true
    rm -rf "$backup" 2>/dev/null || true
}

# Runs on every exit path (including a `set -e` abort). No-op once the install
# has cleared its backups; bash restores the original exit status afterwards.
installer_exit_trap() {
    local rc=$?
    if [ -n "$UPGRADE_BACKUP" ] || [ -n "$FRESH_BACKUP" ]; then
        echo ""
        echo -e "  ${YELLOW}⚠${NC} Install interrupted — restoring your soul, config, and custom agents..."
        restore_backup "$UPGRADE_BACKUP"
        restore_backup "$FRESH_BACKUP"
        UPGRADE_BACKUP=""
        FRESH_BACKUP=""
    fi
    return $rc
}
trap installer_exit_trap EXIT

# A version string we can actually compare: digits and dots, nothing else. A
# captive portal, a proxy error page, or a 404 body all return HTTP 200 with
# HTML — feeding that to the comparison prints bash arithmetic errors and
# "upgrades" the user to garbage. Anything unparseable is treated as unknown.
looks_like_version() {
    local v="$1"
    [ -n "$v" ] && [ "${#v}" -le 32 ] || return 1
    case "$v" in
        *[!0-9.]*|.*|*.) return 1 ;;
    esac
    return 0
}

# Echo the released version, or nothing (and return 1) when it can't be
# determined. --max-time is mandatory: a black-holed DNS or a captive portal
# that swallows packets would otherwise hang the installer indefinitely.
fetch_remote_version() {
    local v
    v=$(curl -fsSL --max-time 15 "$REMOTE_VERSION_URL" 2>/dev/null | head -1 | tr -d '[:space:]') || true
    looks_like_version "$v" || return 1
    printf '%s' "$v"
}

print_banner() {
    echo ""
    echo -e "${CYAN}"
    echo "  🧠 RAPP Brainstem"
    echo -e "${NC}"
    echo "  Local-first AI agent server"
    echo "  Powered by GitHub Copilot — no API keys needed"
    echo ""
}

detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then echo "linux"
    else echo "unknown"
    fi
}

# Ensure Homebrew is on PATH — curl|bash sessions don't source shell profiles
ensure_brew_on_path() {
    if command -v brew &> /dev/null; then return 0; fi
    if [[ -x "/opt/homebrew/bin/brew" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [[ -x "/usr/local/bin/brew" ]]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
}

find_python() {
    for cmd in python3.11 python3.12 python3.13 python3; do
        if command -v "$cmd" &> /dev/null; then
            version=$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null) || continue
            major=$(echo "$version" | cut -d. -f1)
            minor=$(echo "$version" | cut -d. -f2)
            if [[ -n "$major" && -n "$minor" ]] && [ "$major" -ge 3 ] 2>/dev/null && [ "$minor" -ge 11 ] 2>/dev/null; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    if [[ "$(detect_os)" == "macos" ]]; then
        for p in /opt/homebrew/bin/python3.11 /usr/local/bin/python3.11 /opt/homebrew/bin/python3.12 /usr/local/bin/python3.12; do
            if [[ -x "$p" ]]; then echo "$p"; return 0; fi
        done
    fi
    return 1
}

install_python() {
    local os_type=$(detect_os)
    echo -e "  ${YELLOW}Installing Python 3.11...${NC}"
    if [[ "$os_type" == "macos" ]]; then
        if ! command -v brew &> /dev/null; then
            echo -e "  ${YELLOW}Installing Homebrew first...${NC}"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            if [[ -f "/opt/homebrew/bin/brew" ]]; then eval "$(/opt/homebrew/bin/brew shellenv)"; fi
        fi
        brew install python@3.11
        export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
    elif [[ "$os_type" == "linux" ]]; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y python3.11 python3.11-venv python3-pip
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y python3.11 python3-pip
        else
            echo -e "  ${RED}✗${NC} Cannot auto-install Python 3.11 on this system"
            echo "    Install manually from https://python.org"
            exit 1
        fi
    fi
}

# Compare two semver strings. Returns 0 if $1 > $2, 1 otherwise.
version_gt() {
    looks_like_version "$1" && looks_like_version "$2" || return 1
    local IFS=.
    local i a=($1) b=($2)
    for ((i=0; i<${#a[@]}; i++)); do
        local va=${a[i]:-0}
        local vb=${b[i]:-0}
        if (( va > vb )); then return 0; fi
        if (( va < vb )); then return 1; fi
    done
    return 1  # equal
}

check_for_upgrade() {
    local version_file="$LOCAL_VERSION_FILE"

    # No existing install — always proceed
    if [ ! -f "$version_file" ]; then
        return 0
    fi

    local local_version
    local_version=$(cat "$version_file" 2>/dev/null | tr -d '[:space:]')

    # A missing or corrupt VERSION means we cannot reason about the install —
    # take the full path and let it repair itself rather than claiming "up to date".
    if ! looks_like_version "$local_version"; then
        echo -e "  ${YELLOW}⚠${NC} Local version unreadable — reinstalling"
        return 0
    fi

    # Fetch remote version
    local remote_version
    remote_version=$(fetch_remote_version) || true

    if [[ -z "$remote_version" ]]; then
        echo -e "  ${YELLOW}⚠${NC} Could not check remote version — upgrading anyway"
        return 0
    fi

    echo -e "  Local version:  ${CYAN}${local_version}${NC}"
    echo -e "  Remote version: ${CYAN}${remote_version}${NC}"

    if [[ "$local_version" == "$remote_version" ]]; then
        echo ""
        echo -e "  ${GREEN}✓ Already up to date (v${local_version})${NC}"
        echo ""
        return 1  # no upgrade needed
    fi

    if version_gt "$remote_version" "$local_version"; then
        echo -e "  ${YELLOW}⬆${NC} Upgrade available: ${local_version} → ${remote_version}"
        return 0
    fi

    echo -e "  ${GREEN}✓ Already up to date (v${local_version})${NC}"
    echo ""
    return 1
}

check_prereqs() {
    echo "Checking prerequisites..."

    # On macOS, ensure Homebrew is on PATH (curl|bash doesn't source shell profiles)
    if [[ "$(detect_os)" == "macos" ]]; then
        ensure_brew_on_path
    fi

    # Python 3.11+
    PYTHON_CMD=$(find_python) || true
    if [[ -n "$PYTHON_CMD" ]]; then
        version=$("$PYTHON_CMD" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        echo -e "  ${GREEN}✓${NC} Python $version ($PYTHON_CMD)"
    else
        echo -e "  ${YELLOW}⚠${NC} Python 3.11+ not found"
        install_python
        PYTHON_CMD=$(find_python) || true
        if [[ -z "$PYTHON_CMD" ]]; then
            echo -e "  ${RED}✗${NC} Failed to install Python 3.11"
            exit 1
        fi
        version=$("$PYTHON_CMD" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        echo -e "  ${GREEN}✓${NC} Python $version installed"
    fi
    export PYTHON_CMD

    # Git
    if command -v git &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} Git $(git --version | cut -d' ' -f3)"
    else
        echo -e "  ${YELLOW}⚠${NC} Git not found, installing..."
        if [[ "$(detect_os)" == "macos" ]]; then
            xcode-select --install 2>/dev/null || brew install git
        elif command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y git
        else
            echo -e "  ${RED}✗${NC} Git required — install from https://git-scm.com"
            exit 1
        fi
    fi

    # GitHub CLI (required for Copilot token auth)
    if command -v gh &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} GitHub CLI $(gh --version | head -1 | awk '{print $3}')"
    else
        echo -e "  ${YELLOW}⚠${NC} GitHub CLI not found, installing..."
        local os_type=$(detect_os)
        if [[ "$os_type" == "macos" ]]; then
            if command -v brew &> /dev/null; then
                brew install gh
            else
                echo -e "  ${YELLOW}⚠${NC} Installing Homebrew first..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
                ensure_brew_on_path
                brew install gh
            fi
        elif [[ "$os_type" == "linux" ]]; then
            if command -v apt-get &> /dev/null; then
                (type -p wget >/dev/null || sudo apt-get install -y wget) \
                    && sudo mkdir -p -m 755 /etc/apt/keyrings \
                    && out=$(mktemp) && wget -nv -O"$out" https://cli.github.com/packages/githubcli-archive-keyring.gpg \
                    && cat "$out" | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
                    && sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
                    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
                    && sudo apt-get update && sudo apt-get install -y gh
            elif command -v dnf &> /dev/null; then
                sudo dnf install -y 'dnf-command(config-manager)' \
                    && sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo \
                    && sudo dnf install -y gh
            else
                echo -e "  ${YELLOW}⚠${NC} Cannot auto-install GitHub CLI — install from https://cli.github.com"
            fi
        fi
        if command -v gh &> /dev/null; then
            echo -e "  ${GREEN}✓${NC} GitHub CLI installed"
        else
            echo -e "  ${YELLOW}!${NC} GitHub CLI not installed — install later from https://cli.github.com"
        fi
    fi
}

# On upgrade, decide what to do with the user's existing soul.md (issue #40).
# Args: <old_soul> <new_default_soul>. The new checkout's default is already at
# <new_default_soul>; <old_soul> is the pre-upgrade file we backed up.
#   return 0 → refreshed: keep the new default in place, save the old one to
#              soul.md.bak-<date>, and print one line saying so.
#   return 1 → preserve : caller restores <old_soul> byte-for-byte (today's behavior).
# It only returns 0 when the old soul is an UNMODIFIED historical default — its
# normalized hash (rapp_brainstem/tests/soul_hash.py) is listed in the manifest —
# AND the new default differs. Any customization, or any uncertainty (no python, no
# manifest, unreadable/undecodable file), fails safe to preserve. It never clobbers.
maybe_refresh_soul() {
    local old="$1" newdef="$2"
    local src_dir="$BRAINSTEM_HOME/src/rapp_brainstem"
    local hasher="$src_dir/tests/soul_hash.py"
    local manifest="$src_dir/tests/soul_defaults.sha256"

    [ -n "${PYTHON_CMD:-}" ] && [ -f "$hasher" ] && [ -f "$manifest" ] || return 1

    local oldhash newhash
    oldhash=$("$PYTHON_CMD" "$hasher" "$old" 2>/dev/null) || return 1
    [ -n "$oldhash" ] || return 1
    # Not an unmodified default (customized or unrecognizable) → preserve.
    awk -v h="$oldhash" '/^[[:space:]]*#/{next} $1==h{f=1; exit} END{exit !f}' "$manifest" || return 1
    # A known default — only refresh if the new default actually differs.
    newhash=$("$PYTHON_CMD" "$hasher" "$newdef" 2>/dev/null) || return 1
    [ -n "$newhash" ] && [ "$oldhash" != "$newhash" ] || return 1

    local bak="$src_dir/soul.md.bak-$(date +%Y%m%d)"
    # Don't clobber an earlier same-day backup (a second refresh on the same date).
    if [ -e "$bak" ]; then
        local n=1
        while [ -e "${bak}-${n}" ]; do n=$((n+1)); done
        bak="${bak}-${n}"
    fi
    cp "$old" "$bak" 2>/dev/null || return 1
    echo -e "  ${GREEN}✓${NC} Refreshed default soul (yours was an unmodified default); backup at ${bak}"
    return 0
}

install_brainstem() {
    echo ""
    echo "Installing RAPP Brainstem..."
    mkdir -p "$BRAINSTEM_HOME"

    if [ -d "$SRC_DIR/.git" ]; then
        # ── SMART UPDATE: preserve local files, upgrade framework ──
        local LOCAL_VER="0.0.0"
        [ -f "$LOCAL_VERSION_FILE" ] && LOCAL_VER=$(tr -d '[:space:]' < "$LOCAL_VERSION_FILE" 2>/dev/null || echo "0.0.0")
        [ -n "$LOCAL_VER" ] || LOCAL_VER="0.0.0"

        # Empty means "couldn't be determined" (offline, captive portal, blocked
        # DNS). We still refresh from origin — the git remote may be reachable
        # even when raw.githubusercontent.com is not — but we never print a
        # version we did not verify.
        local TARGET_VER=""
        if [ -n "$PIN_VERSION" ]; then
            # Strip leading 'v' for comparison (v0.6.0 → 0.6.0)
            TARGET_VER="${PIN_VERSION#v}"
        else
            TARGET_VER=$(fetch_remote_version) || true
        fi

        echo "  Local:  v${LOCAL_VER}"
        if [ -n "$TARGET_VER" ]; then
            echo "  Target: v${TARGET_VER}${PIN_VERSION:+ (pinned)}"
        else
            echo "  Target: unknown (could not reach github.com) — refreshing from origin"
        fi

        if [ -n "$TARGET_VER" ] && [ "$LOCAL_VER" = "$TARGET_VER" ]; then
            echo -e "  ${GREEN}✓${NC} Already on v${LOCAL_VER}"
        else
            if [ -n "$TARGET_VER" ]; then
                echo "  Switching v${LOCAL_VER} → v${TARGET_VER}..."
            fi

            # 1. Backup user's local files (soul, custom agents, .env)
            UPGRADE_BACKUP=$(new_backup_dir upgrade) || {
                echo -e "  ${RED}✗${NC} Could not create a temporary backup directory"
                exit 1
            }
            local BACKUP="$UPGRADE_BACKUP"
            [ -f "$SOUL_FILE" ] && cp "$SOUL_FILE" "$BACKUP/soul.md"
            [ -f "$ENV_FILE" ] && cp "$ENV_FILE" "$BACKUP/.env"
            if [ -d "$AGENTS_DIR" ]; then
                mkdir -p "$BACKUP/agents"
                # Backup ALL agents — user-created ones will be restored
                cp "$AGENTS_DIR"/*.py "$BACKUP/agents/" 2>/dev/null || true
            fi
            echo -e "  ${GREEN}✓${NC} Backed up soul, agents, config"

            # 2. Fetch and checkout target version.
            # Guard every git call: offline (or a black-holed github) must not abort
            # the whole script under `set -e` — we fall back to whatever is already
            # local and say so, instead of claiming an upgrade that never happened.
            cd "$SRC_DIR"
            # An install cloned from an older origin (a fork, or this project's
            # pre-Microsoft home) would otherwise keep pulling the wrong repository
            # forever. Point it at the repo this installer belongs to.
            git remote set-url origin "$REPO_URL" 2>/dev/null || true
            git stash --quiet 2>/dev/null || true
            git fetch origin --tags --quiet 2>/dev/null || true
            local UPDATE_OK=false
            if [ -n "$PIN_VERSION" ]; then
                # Resolve the pin against every tag form we ship: the documented
                # v0.6.0 UX, a bare 0.6.0, and the actual release tag brainstem-v0.6.0.
                TAG_REF=""
                for cand in "$PIN_VERSION" "v${PIN_VERSION#v}" "brainstem-${PIN_VERSION#v}" "brainstem-v${PIN_VERSION#v}"; do
                    if git rev-parse "$cand" >/dev/null 2>&1; then TAG_REF="$cand"; break; fi
                done
                if [ -z "$TAG_REF" ]; then
                    echo -e "  ${RED}✗${NC} Version ${PIN_VERSION} not found. Available versions:"
                    git tag -l 'brainstem-v*' 'v*' | sort -V | sed 's/^/    /'
                    # The exit trap restores the backup taken above, so a bad pin
                    # never costs the user their soul, config, or agents.
                    exit 1
                fi
                if git checkout "$TAG_REF" --quiet 2>/dev/null; then
                    UPDATE_OK=true
                    echo -e "  ${GREEN}✓${NC} Checked out ${TAG_REF}"
                else
                    echo -e "  ${YELLOW}⚠${NC} Could not check out ${TAG_REF} — keeping v${LOCAL_VER}"
                fi
            else
                # fetch + reset, not pull: it survives a detached HEAD (left by an
                # earlier --version pin) and an unrelated history (an old fork).
                if git fetch origin main --quiet 2>/dev/null && \
                   git reset --hard FETCH_HEAD --quiet 2>/dev/null; then
                    UPDATE_OK=true
                    echo -e "  ${GREEN}✓${NC} Framework updated"
                elif git pull --quiet 2>/dev/null; then
                    UPDATE_OK=true
                    echo -e "  ${GREEN}✓${NC} Framework updated"
                else
                    echo -e "  ${YELLOW}⚠${NC} Could not download the update — keeping v${LOCAL_VER}"
                fi
            fi

            # 3. Restore user's local files (merge, don't overwrite)
            # soul.md: refresh it only when the pre-upgrade file was an unmodified
            # historical default (issue #40); any customization is preserved as-is.
            if [ -f "$BACKUP/soul.md" ]; then
                if ! { [ "$UPDATE_OK" = true ] && maybe_refresh_soul "$BACKUP/soul.md" "$SOUL_FILE"; }; then
                    cp "$BACKUP/soul.md" "$SOUL_FILE"
                fi
            fi
            [ -f "$BACKUP/.env" ] && cp "$BACKUP/.env" "$ENV_FILE"
            if [ -d "$BACKUP/agents" ]; then
                # Only restore genuinely user-added agents. Compute the set the repo
                # now ships from the fresh checkout and skip-restore anything in it —
                # otherwise bundled agents (context_memory, manage_memory, hacker_news)
                # get reverted to the backed-up copies on every upgrade (issue #2), so
                # bundled-agent fixes never reach existing users.
                local SHIPPED=""
                for shipped_file in "$AGENTS_DIR"/*.py; do
                    [ -f "$shipped_file" ] || continue
                    SHIPPED="$SHIPPED $(basename "$shipped_file")"
                done
                for agent_file in "$BACKUP/agents"/*.py; do
                    [ -f "$agent_file" ] || continue
                    local fname=$(basename "$agent_file")
                    # Skip core agents that the repo manages
                    case "$fname" in
                        basic_agent.py|__init__.py) continue ;;
                    esac
                    # Skip anything shipped in the fresh checkout (bundled agents)
                    case " $SHIPPED " in *" $fname "*) continue ;; esac
                    # Genuinely user-added agent — keep it
                    cp "$agent_file" "$AGENTS_DIR/$fname"
                done
                echo -e "  ${GREEN}✓${NC} Restored custom agents + soul + config"
            fi

            # 4. Clean up backup — the user's files are back in place, so the exit
            # trap has nothing left to restore.
            rm -rf "$BACKUP"
            UPGRADE_BACKUP=""

            # 5. Report the version that is actually on disk. Announcing the target
            # would claim a successful upgrade even when the download failed.
            local NEW_VER="$LOCAL_VER"
            [ -f "$LOCAL_VERSION_FILE" ] && NEW_VER=$(tr -d '[:space:]' < "$LOCAL_VERSION_FILE" 2>/dev/null || echo "$LOCAL_VER")
            if [ "$UPDATE_OK" = true ] && [ -n "$PIN_VERSION" ]; then
                echo -e "  ${GREEN}✓${NC} Pinned to v${NEW_VER}"
            elif [ "$UPDATE_OK" = true ] && [ "$NEW_VER" != "$LOCAL_VER" ]; then
                echo -e "  ${GREEN}✓${NC} Upgrade complete: v${LOCAL_VER} → v${NEW_VER}"
            elif [ "$UPDATE_OK" = true ]; then
                echo -e "  ${GREEN}✓${NC} Already at the latest framework (v${NEW_VER})"
            else
                echo -e "  ${YELLOW}⚠${NC} Still on v${NEW_VER} — re-run the installer when you're back online"
            fi
        fi
    else
        echo "  Fresh install — cloning repository..."
        # A broken prior install (src present but .git gone) may still hold the user's
        # soul, .env, and custom agents — none of which are in git. Preserve them
        # before wiping so a re-run can't silently destroy the user's work. The common
        # case (no existing src) leaves FRESH_BACKUP empty and skips all of this.
        FRESH_BACKUP=""
        if [ -d "$BRAINSTEM_SRC" ]; then
            FRESH_BACKUP=$(new_backup_dir fresh) || {
                echo -e "  ${RED}✗${NC} Could not create a temporary backup directory"
                exit 1
            }
            mkdir -p "$FRESH_BACKUP/agents"
            [ -f "$SOUL_FILE" ] && cp "$SOUL_FILE" "$FRESH_BACKUP/soul.md" 2>/dev/null || true
            [ -f "$ENV_FILE" ] && cp "$ENV_FILE" "$FRESH_BACKUP/.env" 2>/dev/null || true
            [ -d "$AGENTS_DIR" ] && cp "$AGENTS_DIR"/*.py "$FRESH_BACKUP/agents/" 2>/dev/null || true
            [ -d "$DATA_DIR" ] && cp -R "$DATA_DIR" "$FRESH_BACKUP/.brainstem_data" 2>/dev/null || true
        fi

        # Clone into a staging directory and only swap it in once it is complete.
        # Deleting src first would mean a failed download (offline, proxy, disk
        # full) leaves the user with no install at all — and nothing to re-run.
        local NEW_SRC="$SRC_DIR.new.$$"
        rm -rf "$NEW_SRC" 2>/dev/null || true
        if ! git clone --quiet "$REPO_URL" "$NEW_SRC"; then
            rm -rf "$NEW_SRC" 2>/dev/null || true
            echo -e "  ${RED}✗${NC} Could not download RAPP Brainstem from GitHub."
            echo "    Check your network/proxy and re-run the installer."
            echo "    Your existing files were left untouched."
            exit 1
        fi
        # If pinning, checkout the specific tag after clone (accepts every tag form).
        if [ -n "$PIN_VERSION" ]; then
            cd "$NEW_SRC"
            git fetch origin --tags --quiet 2>/dev/null || true
            TAG_REF=""
            for cand in "$PIN_VERSION" "v${PIN_VERSION#v}" "brainstem-${PIN_VERSION#v}" "brainstem-v${PIN_VERSION#v}"; do
                if git rev-parse "$cand" >/dev/null 2>&1; then TAG_REF="$cand"; break; fi
            done
            if [ -n "$TAG_REF" ] && git checkout "$TAG_REF" --quiet 2>/dev/null; then
                echo -e "  ${GREEN}✓${NC} Checked out ${TAG_REF}"
            else
                echo -e "  ${RED}✗${NC} Version ${PIN_VERSION} not found. Available versions:"
                git tag -l 'brainstem-v*' 'v*' | sort -V | sed 's/^/    /'
                cd "$BRAINSTEM_HOME"
                rm -rf "$NEW_SRC" 2>/dev/null || true
                exit 1
            fi
            cd "$BRAINSTEM_HOME"
        fi
        rm -rf "$SRC_DIR" 2>/dev/null || true
        mv "$NEW_SRC" "$SRC_DIR"

        # Restore any preserved user files over the fresh checkout.
        if [ -n "$FRESH_BACKUP" ]; then
            local FRESH_SHIPPED=""
            for shipped_file in "$AGENTS_DIR"/*.py; do
                [ -f "$shipped_file" ] || continue
                FRESH_SHIPPED="$FRESH_SHIPPED $(basename "$shipped_file")"
            done
            [ -f "$FRESH_BACKUP/soul.md" ] && cp "$FRESH_BACKUP/soul.md" "$SOUL_FILE" 2>/dev/null || true
            [ -f "$FRESH_BACKUP/.env" ] && cp "$FRESH_BACKUP/.env" "$ENV_FILE" 2>/dev/null || true
            for af in "$FRESH_BACKUP/agents"/*.py; do
                [ -f "$af" ] || continue
                fn=$(basename "$af")
                case "$fn" in basic_agent.py|__init__.py) continue ;; esac
                case " $FRESH_SHIPPED " in *" $fn "*) continue ;; esac
                cp "$af" "$AGENTS_DIR/$fn" 2>/dev/null || true
            done
            [ -d "$FRESH_BACKUP/.brainstem_data" ] && cp -R "$FRESH_BACKUP/.brainstem_data" "$DATA_DIR" 2>/dev/null || true
            rm -rf "$FRESH_BACKUP"
            FRESH_BACKUP=""
            echo -e "  ${GREEN}✓${NC} Preserved your soul, agents, memories, and config"
        fi
    fi
    echo -e "  ${GREEN}✓${NC} Source code ready"
}

setup_venv() {
    local venv_python="$VENV_DIR/bin/python"

    # Check if venv exists and is healthy
    if [ -x "$venv_python" ]; then
        if "$venv_python" -c "import sys; sys.exit(0)" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} Virtual environment OK"
            return 0
        fi
        echo -e "  ${YELLOW}⚠${NC} Virtual environment broken — recreating..."
        rm -rf "$VENV_DIR"
    fi

    echo "  Creating virtual environment..."
    "$PYTHON_CMD" -m venv "$VENV_DIR" 2>/dev/null || {
        # Some systems need ensurepip first
        "$PYTHON_CMD" -m ensurepip 2>/dev/null || true
        "$PYTHON_CMD" -m venv "$VENV_DIR" || {
            echo -e "  ${RED}✗${NC} Failed to create virtual environment"
            echo "    Try: $PYTHON_CMD -m pip install virtualenv"
            exit 1
        }
    }
    # Ensure pip is up to date inside the venv
    "$VENV_DIR/bin/python" -m pip install --upgrade pip --quiet 2>/dev/null || true
    echo -e "  ${GREEN}✓${NC} Virtual environment ready"
}

setup_deps() {
    echo ""
    echo "Installing dependencies..."
    local req_file="$BRAINSTEM_HOME/src/rapp_brainstem/requirements.txt"
    "$VENV_DIR/bin/pip" install -r "$req_file" --quiet 2>/dev/null || \
        "$VENV_DIR/bin/pip" install -r "$req_file"

    # Verify the critical imports actually work
    if ! "$VENV_DIR/bin/python" -c "import flask, flask_cors, requests, dotenv" 2>/dev/null; then
        echo -e "  ${RED}✗${NC} Dependencies failed to install"
        echo "    Try: $VENV_DIR/bin/pip install -r $req_file"
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} Dependencies installed"
}

ensure_deps() {
    # Quick import check — only install if something is missing
    if "$VENV_DIR/bin/python" -c "import flask, flask_cors, requests, dotenv" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} Dependencies verified"
        return 0
    fi

    echo -e "  ${YELLOW}⚠${NC} Missing dependencies — installing..."
    local req_file="$BRAINSTEM_HOME/src/rapp_brainstem/requirements.txt"
    "$VENV_DIR/bin/pip" install -r "$req_file" --quiet 2>/dev/null || \
        "$VENV_DIR/bin/pip" install -r "$req_file"

    if ! "$VENV_DIR/bin/python" -c "import flask, flask_cors, requests, dotenv" 2>/dev/null; then
        echo -e "  ${RED}✗${NC} Dependencies failed — try: $VENV_DIR/bin/pip install -r $req_file"
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} Dependencies installed"
}

install_cli() {
    echo ""
    echo "Installing CLI..."
    mkdir -p "$BRAINSTEM_BIN"

    cat > "$BRAINSTEM_BIN/brainstem" << 'WRAPPER'
#!/bin/bash
BRAINSTEM_HOME="$HOME/.brainstem"
VENV_PYTHON="$BRAINSTEM_HOME/venv/bin/python"
# Never fall through to the caller's directory: `python brainstem.py` there fails
# with a bare "can't open file" instead of telling the user what is wrong.
cd "$BRAINSTEM_HOME/src/rapp_brainstem" 2>/dev/null || {
    echo "brainstem: no install found at $BRAINSTEM_HOME/src/rapp_brainstem" >&2
    echo "  Reinstall: curl -fsSL https://microsoft.github.io/aibast-agents-library/install.sh | bash" >&2
    exit 1
}

# Use venv Python; fall back to creating venv if missing
if [ ! -x "$VENV_PYTHON" ]; then
    echo "  Setting up environment..."
    PYTHON_CMD=$(command -v python3.11 || command -v python3.12 || command -v python3.13 || command -v python3)
    if [ -z "$PYTHON_CMD" ]; then
        echo "brainstem: no Python 3.11+ found on PATH" >&2
        exit 1
    fi
    "$PYTHON_CMD" -m venv "$BRAINSTEM_HOME/venv" 2>/dev/null
    "$BRAINSTEM_HOME/venv/bin/pip" install -r requirements.txt --quiet 2>/dev/null || \
        "$BRAINSTEM_HOME/venv/bin/pip" install -r requirements.txt
    VENV_PYTHON="$BRAINSTEM_HOME/venv/bin/python"
fi

# Verify deps on every launch (fast no-op if already installed)
if ! "$VENV_PYTHON" -c "import flask, flask_cors, requests, dotenv" 2>/dev/null; then
    "$BRAINSTEM_HOME/venv/bin/pip" install -r requirements.txt --quiet 2>/dev/null || true
fi

exec "$VENV_PYTHON" brainstem.py "$@"
WRAPPER

    chmod +x "$BRAINSTEM_BIN/brainstem"

    add_to_path() {
        local file="$1"
        # Create shell config if it doesn't exist (common on fresh macOS)
        touch "$file"
        if ! grep -q '\.local/bin' "$file" 2>/dev/null; then
            echo '' >> "$file"
            echo '# RAPP Brainstem' >> "$file"
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$file"
        fi
    }
    add_to_path "$HOME/.bashrc"
    add_to_path "$HOME/.zshrc"
    add_to_path "$HOME/.bash_profile"

    echo -e "  ${GREEN}✓${NC} CLI installed to $BRAINSTEM_BIN/brainstem"
}

create_env() {
    local env_file="$BRAINSTEM_HOME/src/rapp_brainstem/.env"
    if [ ! -f "$env_file" ]; then
        cp "$BRAINSTEM_HOME/src/rapp_brainstem/.env.example" "$env_file" 2>/dev/null || true
    fi
}

launch_brainstem() {
    export PATH="$BRAINSTEM_BIN:/opt/homebrew/bin:/usr/local/bin:$PATH"

    # Always pull latest code before launching — but never when a version is
    # pinned, or the pull would silently drag the user off the tag they asked for.
    if [ -z "$PIN_VERSION" ] && [ -d "$SRC_DIR/.git" ]; then
        cd "$SRC_DIR"
        git pull --quiet 2>/dev/null || true
    fi

    local venv_python="$VENV_DIR/bin/python"

    # Ensure venv exists (handles edge case where only launch is called)
    if [ ! -x "$venv_python" ]; then
        if [[ -z "$PYTHON_CMD" ]]; then
            PYTHON_CMD=$(find_python) || true
        fi
        if [[ "$(detect_os)" == "macos" ]]; then
            ensure_brew_on_path
        fi
        setup_venv
        ensure_deps
    fi

    local token_file="$BRAINSTEM_HOME/src/rapp_brainstem/.copilot_token"
    local client_id="Iv1.b507a08c87ecfe98"

    # Step 1: Copilot authentication (device code flow)
    local needs_auth=true
    if [ -f "$token_file" ]; then
        # Validate existing token against Copilot API
        local saved_token
        saved_token=$("$venv_python" -c "
import json, sys
try:
    with open('$token_file') as f:
        raw = f.read().strip()
    if raw.startswith('{'):
        print(json.loads(raw).get('access_token',''))
    else:
        print(raw)
except: pass
" 2>/dev/null)
        if [[ -n "$saved_token" ]]; then
            local auth_prefix="token"
            if [[ "$saved_token" != ghu_* ]]; then auth_prefix="Bearer"; fi
            local check_status
            check_status=$(curl -s --max-time 15 -o /dev/null -w "%{http_code}" \
                -H "Authorization: $auth_prefix $saved_token" \
                -H "Accept: application/json" \
                -H "Editor-Version: vscode/1.95.0" \
                -H "Editor-Plugin-Version: copilot/1.0.0" \
                "https://api.github.com/copilot_internal/v2/token" 2>/dev/null) || true
            if [[ "$check_status" == "200" ]]; then
                echo -e "  ${GREEN}✓${NC} Already authenticated with GitHub Copilot"
                needs_auth=false
            elif [[ -z "$check_status" || "$check_status" == "000" ]]; then
                # curl never reached GitHub (offline, captive portal, timeout) — that
                # says nothing about the token. Keep it; the server retries live.
                echo -e "  ${YELLOW}⚠${NC} Couldn't verify the saved token (no network) — keeping it"
                needs_auth=false
            else
                echo -e "  ${YELLOW}⚠${NC} Saved token expired — re-authenticating..."
                rm -f "$token_file"
            fi
        else
            rm -f "$token_file"
        fi
    fi

    if [[ "$needs_auth" == true ]]; then
        echo ""
        echo -e "  ${CYAN}Authenticating with GitHub Copilot...${NC}"
        echo ""

        # Best-effort auth: disable `set -e` for the whole block. Every curl and JSON
        # parse below tolerates failure (empty response when offline), and the code
        # already handles those cases gracefully — but under `set -e` the very first
        # failed command substitution would abort the installer before the server can
        # start. The user can always finish signing in later at /login.
        set +e

        # Request device code
        local device_resp
        device_resp=$(curl -fsSL --max-time 15 -X POST "https://github.com/login/device/code" \
            -H "Accept: application/json" \
            -H "Content-Type: application/x-www-form-urlencoded" \
            -d "client_id=${client_id}" 2>/dev/null)

        local user_code device_code interval verify_uri
        user_code=$(echo "$device_resp" | "$venv_python" -c "import sys,json; print(json.load(sys.stdin)['user_code'])" 2>/dev/null)
        device_code=$(echo "$device_resp" | "$venv_python" -c "import sys,json; print(json.load(sys.stdin)['device_code'])" 2>/dev/null)
        interval=$(echo "$device_resp" | "$venv_python" -c "import sys,json; print(json.load(sys.stdin).get('interval',5))" 2>/dev/null)
        verify_uri=$(echo "$device_resp" | "$venv_python" -c "import sys,json; print(json.load(sys.stdin)['verification_uri'])" 2>/dev/null)

        if [[ -z "$user_code" || -z "$device_code" ]]; then
            echo -e "  ${YELLOW}!${NC} Could not start auth — you can sign in at http://localhost:7071/login"
        else
            echo "  ┌─────────────────────────────────────────┐"
            echo -e "  │  Your code: ${CYAN}${user_code}${NC}                  │"
            echo "  └─────────────────────────────────────────┘"
            echo ""
            echo "  Opening browser to authorize..."

            # Open browser
            open "$verify_uri" 2>/dev/null || xdg-open "$verify_uri" 2>/dev/null || true

            echo "  Waiting for authorization..."
            echo ""

            local token_json=""
            for i in $(seq 1 60); do
                sleep "${interval:-5}"
                local poll_resp
                poll_resp=$(curl -fsSL --max-time 15 -X POST "https://github.com/login/oauth/access_token" \
                    -H "Accept: application/json" \
                    -H "Content-Type: application/x-www-form-urlencoded" \
                    -d "client_id=${client_id}&device_code=${device_code}&grant_type=urn:ietf:params:oauth:grant-type:device_code" 2>/dev/null) || true

                local access_token error
                access_token=$(echo "$poll_resp" | "$venv_python" -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token',''))" 2>/dev/null)
                error=$(echo "$poll_resp" | "$venv_python" -c "import sys,json; d=json.load(sys.stdin); print(d.get('error',''))" 2>/dev/null)

                if [[ -n "$access_token" ]]; then
                    # Save token file (same format brainstem.py expects)
                    "$venv_python" -c "
import sys, json
d = json.loads(sys.argv[1])
out = {'access_token': d['access_token']}
if d.get('refresh_token'): out['refresh_token'] = d['refresh_token']
with open(sys.argv[2], 'w') as f: json.dump(out, f)
" "$poll_resp" "$token_file"

                    # Validate Copilot access immediately
                    local copilot_check copilot_status
                    copilot_check=$(curl -s --max-time 15 -w "\n%{http_code}" \
                        -H "Authorization: token $access_token" \
                        -H "Accept: application/json" \
                        -H "Editor-Version: vscode/1.95.0" \
                        -H "Editor-Plugin-Version: copilot/1.0.0" \
                        "https://api.github.com/copilot_internal/v2/token" 2>/dev/null) || true
                    copilot_status=$(echo "$copilot_check" | tail -1)

                    if [[ "$copilot_status" == "200" ]]; then
                        echo -e "  ${GREEN}✓${NC} Authenticated — Copilot access confirmed"
                    elif [[ "$copilot_status" == "403" ]]; then
                        echo ""
                        echo -e "  ${RED}✗${NC} This GitHub account does NOT have Copilot access."
                        echo ""
                        echo -e "  Either:"
                        echo -e "    1. Sign up for Copilot: ${CYAN}https://github.com/github-copilot/signup${NC}"
                        echo -e "    2. Re-run this installer and sign in with a different GitHub account"
                        echo ""
                        rm -f "$token_file"
                    else
                        echo -e "  ${GREEN}✓${NC} Authenticated with GitHub"
                    fi
                    break
                fi

                if [[ "$error" == "expired_token" ]]; then
                    echo -e "  ${YELLOW}!${NC} Auth timed out — sign in at http://localhost:7071/login"
                    break
                fi

                if [[ "$error" != "authorization_pending" && "$error" != "slow_down" && -n "$error" ]]; then
                    echo -e "  ${YELLOW}!${NC} Auth error: $error — sign in at http://localhost:7071/login"
                    break
                fi
            done
        fi
        set -e   # end best-effort auth block
    fi

    # Step 2: Launch brainstem
    echo ""
    echo -e "  ${CYAN}Starting RAPP Brainstem...${NC}"
    echo ""

    cd "$BRAINSTEM_SRC"

    # Free port 7071 — but only from a brainstem. Killing whatever happens to hold
    # the port would take down an unrelated dev server without warning.
    local existing_pid existing_cmd
    for existing_pid in $(lsof -ti:7071 2>/dev/null || true); do
        [ -n "$existing_pid" ] || continue
        existing_cmd=$(ps -p "$existing_pid" -o command= 2>/dev/null || true)
        case "$existing_cmd" in
            *brainstem.py*)
                echo -e "  ${YELLOW}⚠${NC} Stopping existing brainstem (PID $existing_pid)..."
                kill "$existing_pid" 2>/dev/null || true
                # Wait for the port to actually free instead of guessing.
                local _w
                for _w in 1 2 3 4 5; do
                    kill -0 "$existing_pid" 2>/dev/null || break
                    sleep 1
                done
                ;;
            "")
                # Couldn't identify it (no ps, or it exited already) — leave it alone.
                ;;
            *)
                echo -e "  ${YELLOW}⚠${NC} Port 7071 is in use by PID $existing_pid ($(echo "$existing_cmd" | cut -c1-60))"
                echo -e "     Not stopping it — quit that process first if brainstem fails to start."
                ;;
        esac
    done

    # Open the browser once the server actually answers (#14) — a fixed delay
    # races cold startups (token exchange, dep installs) and lands the user on
    # a dead-port error page. Poll /health, then open; after 60s open anyway so
    # the user still gets the tab (with the URL bar filled in) on a slow start.
    (
        for _ in $(seq 1 60); do
            if curl -sf -o /dev/null --max-time 1 "http://localhost:7071/health" 2>/dev/null; then
                break
            fi
            sleep 1
        done
        open "http://localhost:7071" 2>/dev/null || xdg-open "http://localhost:7071" 2>/dev/null || true
    ) &

    # Final dep safety net — if somehow we got here without deps, fix it
    if ! "$venv_python" -c "import flask, flask_cors, requests, dotenv" 2>/dev/null; then
        echo -e "  ${YELLOW}⚠${NC} Fixing missing dependencies..."
        "$VENV_DIR/bin/pip" install -r "$BRAINSTEM_HOME/src/rapp_brainstem/requirements.txt" --quiet 2>/dev/null || \
            "$VENV_DIR/bin/pip" install -r "$BRAINSTEM_HOME/src/rapp_brainstem/requirements.txt"
    fi

    # Use exec to replace shell — but only if stdin is a terminal.
    # When piped (curl | bash), exec can lose the TTY and hang.
    if [ -t 0 ]; then
        exec "$venv_python" brainstem.py
    elif ( : </dev/tty ) 2>/dev/null; then
        # Piped installer with a USABLE controlling terminal — reattach stdin.
        # Test by opening it: the /dev/tty node exists even without a controlling
        # terminal (ssh without -t, CI), where only the open fails — a bare `-e`
        # check would take this branch and die on the redirect.
        "$venv_python" brainstem.py </dev/tty
    else
        # No controlling terminal at all (ssh without -t, CI, a container). Reattaching
        # /dev/tty would error out; just run the server on the inherited stdin.
        "$venv_python" brainstem.py
    fi
}

main() {
    # Parse arguments (e.g. --version v0.6.0)
    while [ $# -gt 0 ]; do
        case "$1" in
            --version=*)
                PIN_VERSION="${1#*=}"
                if [ -z "$PIN_VERSION" ]; then
                    echo -e "  ${RED}✗${NC} --version needs a value, e.g. --version v0.6.0" >&2
                    exit 2
                fi
                shift
                ;;
            --version)
                # A bare `--version` used to run off the end of the argument list:
                # `shift 2` failed and `set -e` killed the installer with no output
                # at all. Say what is wrong instead.
                PIN_VERSION="${2:-}"
                case "$PIN_VERSION" in
                    ""|-*)
                        echo -e "  ${RED}✗${NC} --version needs a value, e.g. --version v0.6.0" >&2
                        echo "" >&2
                        usage >&2
                        exit 2
                        ;;
                esac
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                # Never silently swallow a typo like `--verison v0.6.0` — the user
                # would get the latest release while believing they pinned one.
                echo -e "  ${YELLOW}⚠${NC} Ignoring unknown option: $1" >&2
                shift
                ;;
        esac
    done

    print_banner

    if [ -n "$PIN_VERSION" ]; then
        echo -e "  ${CYAN}Pinning to version: ${PIN_VERSION}${NC}"
        echo ""
    fi

    # Check if this is an upgrade of an existing install
    # Skip the shortcut when --version is specified (always go through install_brainstem)
    if [ -z "$PIN_VERSION" ] && [ -d "$SRC_DIR/.git" ]; then
        echo "Checking for updates..."
        if ! check_for_upgrade; then
            # Already up to date — still verify everything works before launching.
            # The CLI wrapper and .env come BEFORE dependencies: they are cheap and
            # offline-safe, and a PyPI outage must not leave the user without a
            # `brainstem` command every single run.
            check_prereqs
            setup_venv
            install_cli
            create_env
            ensure_deps
            export PATH="$BRAINSTEM_BIN:/opt/homebrew/bin:/usr/local/bin:$PATH"
            launch_brainstem
            exit $?  # launch uses exec, but guard against fall-through
        fi
        # Upgrade available — fall through to full install path
    fi

    check_prereqs
    install_brainstem
    setup_venv
    # Same ordering as the fast path: if setup_deps fails, VERSION already matches
    # the remote, so a re-run takes the "already up to date" path — which must not
    # be the only thing that ever installs the CLI wrapper and .env.
    install_cli
    create_env
    setup_deps

    # Make sure brainstem and gh are on PATH for this session
    export PATH="$BRAINSTEM_BIN:/opt/homebrew/bin:/usr/local/bin:$PATH"

    local installed_version
    installed_version=$(cat "$LOCAL_VERSION_FILE" 2>/dev/null | tr -d '[:space:]')

    echo ""
    echo "═══════════════════════════════════════════════════"
    echo -e "  ${GREEN}✓ RAPP Brainstem v${installed_version} installed!${NC}"
    echo "═══════════════════════════════════════════════════"
    echo ""

    launch_brainstem
}

main "$@"
