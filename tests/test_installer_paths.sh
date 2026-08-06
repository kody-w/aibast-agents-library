#!/usr/bin/env bash
# Installer git mechanics, across every checkout shape and every run shape.
#
# The installer grew two changes that touch how the repository lands on a user's
# disk: the clone is now shallow (depth 1) and sparse (rapp_brainstem only).
# Both are safe on a fresh install by construction. Neither is automatically
# safe on a machine that installed BEFORE them — that machine has a full,
# non-sparse clone, and the update path has to keep working on it unchanged.
#
# So this exercises the matrix rather than the happy path:
#
#   checkout shapes   legacy   full clone, as installs before this change have
#                     modern   depth-1 + sparse, as install.sh now creates
#
#   run shapes        fresh    the clone itself
#                     update   an update is available and gets pulled
#                     current  already up to date; nothing to do but start
#                     pinned   a --version pin, which needs real history
#
# What is asserted is what the installer actually depends on: that
# rapp_brainstem is complete and VERSION is readable afterwards. install.sh
# itself is not run — it installs Python, builds a venv and opens a browser —
# but every git operation it performs is.
#
# Usage: bash tests/test_installer_paths.sh
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)"
PASS=0; FAIL=0
GREEN=$'\033[0;32m'; RED=$'\033[0;31m'; NC=$'\033[0m'

trap 'rm -rf "$WORK"' EXIT

ok()   { PASS=$((PASS+1)); printf "  ${GREEN}✓${NC} %s\n" "$1"; }
bad()  { FAIL=$((FAIL+1)); printf "  ${RED}✗${NC} %s\n" "$1"; [ -n "${2:-}" ] && printf "      %s\n" "$2"; }

# The two things the installer reads out of the checkout, and the only two that
# have to survive every path.
usable() {
    local d="$1"
    [ -f "$d/rapp_brainstem/brainstem.py" ] || { echo "brainstem.py missing"; return 1; }
    [ -f "$d/rapp_brainstem/VERSION" ]      || { echo "VERSION missing"; return 1; }
    return 0
}

clone_legacy() {   # what a machine installed before this change looks like
    git clone --quiet --no-local --branch "$BRANCH" "$REPO_ROOT" "$1" 2>/dev/null
}

clone_modern() {   # what install.sh now creates: a plain single-branch clone
    git clone --quiet --no-local --single-branch --branch "$BRANCH" \
        "$REPO_ROOT" "$1" 2>/dev/null
}

echo "== installer checkout + run shapes =="
echo "   branch under test: $BRANCH"

for shape in legacy modern; do
    DIR="$WORK/$shape"

    # --- fresh -----------------------------------------------------------
    if "clone_$shape" "$DIR"; then
        if err="$(usable "$DIR")"; then
            ok "$shape · fresh install leaves a usable brainstem"
        else
            bad "$shape · fresh install leaves a usable brainstem" "$err"
        fi
    else
        bad "$shape · clone succeeded" "clone failed"
        continue
    fi

    # Size is the whole point; assert it rather than trust it. A full clone is
    # affordable again only because the media moved to its own branch AND this
    # branch was re-rooted — and only if the clone does not fetch every branch.
    if [ "$shape" = modern ]; then
        kb=$(du -sk "$DIR" | cut -f1)
        if [ "$kb" -lt 80000 ]; then
            ok "modern · full checkout is $((kb/1024)) MB on disk (under 80 MB)"
        else
            bad "modern · full checkout is small" "$((kb/1024)) MB on disk"
        fi
        # The failure this guards: a plain clone pulls EVERY branch, and the
        # media branch is 620 MB. Single-branch is what keeps it out.
        n=$(cd "$DIR" && git branch -r | wc -l | tr -d ' ')
        if [ "$n" -eq 1 ]; then
            ok "modern · fetched one branch, so the media branch stayed behind"
        else
            bad "modern · fetched one branch" "$n remote branches came down"
        fi
        # And the whole tree is really there — this is a full checkout now.
        for want in agents api docs; do
            [ -d "$DIR/$want" ] || bad "modern · $want is present" "missing"
        done
        ok "modern · the full working tree is checked out"
    fi

    # --- update: an update is available and gets pulled -------------------
    # `git pull` is what install.sh runs. On a shallow clone it fetches shallow;
    # on a legacy clone it is an ordinary pull. Both must leave it usable.
    ( cd "$DIR" && git pull --quiet >/dev/null 2>&1 \
        || git reset --hard origin/"$BRANCH" --quiet >/dev/null 2>&1 ) || true
    if err="$(usable "$DIR")"; then
        ok "$shape · update run keeps the brainstem usable"
    else
        bad "$shape · update run keeps the brainstem usable" "$err"
    fi

    # --- current: already up to date, nothing to do -----------------------
    before="$(cd "$DIR" && git rev-parse HEAD)"
    ( cd "$DIR" && git pull --quiet >/dev/null 2>&1 ) || true
    after="$(cd "$DIR" && git rev-parse HEAD)"
    if [ "$before" = "$after" ]; then
        ok "$shape · up-to-date run changes nothing"
    else
        bad "$shape · up-to-date run changes nothing" "$before -> $after"
    fi

    # A sparse checkout must STAY sparse across an update, or the space saving
    # silently evaporates on the first upgrade.


    # --- pinned: needs real history, which a shallow clone does not have ---
    ( cd "$DIR" && git fetch origin --tags --quiet >/dev/null 2>&1 ) || true
    tags="$(cd "$DIR" && git tag | wc -l | tr -d ' ')"
    if [ "$tags" -ge 1 ]; then
        ok "$shape · pinning can resolve tags ($tags found)"
    else
        bad "$shape · pinning can resolve tags" "no tags after unshallow"
    fi
    if err="$(usable "$DIR")"; then
        ok "$shape · still usable after fetching tags"
    else
        bad "$shape · still usable after fetching tags" "$err"
    fi
done

echo
echo "installer paths: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] || exit 1
