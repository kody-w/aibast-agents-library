#!/usr/bin/env python3
"""RAPP/1 corpus mirror sync — keeps rapp/ aligned with the upstream kernel.

The manifest (rapp/MIRROR-MANIFEST.json) is the single source of truth:
hand-maintained pins (upstream repo, path, revision COMMIT SHA, license) plus
derived fields this tool writes (sha256, bytes, fetched_at).

Modes (mutually exclusive):
  --fetch               download every entry at its PINNED revision, verify,
                        write files + derived manifest fields
  --check               verify local files hash-match the manifest, that
                        upstream still serves identical bytes at each pin,
                        AND that the kernel's live authority file still
                        agrees with the mirrored one (pin freshness)
  --check --local-only  integrity only, no network (deterministic)

Failure semantics for --check (network mode):
  * local hash mismatch ............................ FAIL
  * upstream serves different bytes at the pin ..... FAIL (history rewritten)
  * pinned revision GONE (HTTP 404/410/451) ........ FAIL (source removed)
  * kernel authority no longer matches our pin ..... FAIL (pin-bump needed)
  * other transport errors ......................... skipped, reported in the
                                                     summary — never called OK

Observe-mode by construction: this tool NEVER moves a pin. Advancing to a
newer upstream revision is a human pull request that edits the manifest and
re-runs --fetch (see rapp/SUCCESSION.md for the pin-bump process).

All mirrored files must live under rapp/ — out-of-tree manifest paths are
refused outright.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "rapp" / "MIRROR-MANIFEST.json"
MIRROR_ROOT = (REPO_ROOT / "rapp").resolve()
AUTHORITY_LOCAL = "rapp/spec/RAPP1_AUTHORITY.json"
AUTHORITY_UPSTREAM = ("kody-w/rapp-map", "main", "RAPP1_AUTHORITY.json")

GONE = (404, 410, 451)


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def safe_path(local: str) -> Path:
    """Resolve a manifest key; refuse anything outside rapp/."""
    p = (REPO_ROOT / local).resolve()
    if not p.is_relative_to(MIRROR_ROOT):
        raise SystemExit(f"[corpus-sync] REFUSING out-of-tree local path: {local!r}")
    return p


def fetch(repo: str, revision: str, path: str) -> bytes:
    url = f"https://raw.githubusercontent.com/{repo}/{revision}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "aibast-corpus-sync"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def cmd_fetch() -> int:
    m = load_manifest()
    now = datetime.now(timezone.utc).isoformat()
    failures = 0
    for local, e in m["files"].items():
        p = safe_path(local)
        try:
            data = fetch(e["repo"], e["revision"], e["path"])
        except Exception as exc:
            print(f"[corpus-sync] FETCH FAIL {local}: {exc}", file=sys.stderr)
            failures += 1
            continue
        h = sha256(data)
        if e.get("sha256") and e["sha256"] != h:
            print(f"[corpus-sync] PIN VIOLATION {local}: upstream bytes at "
                  f"{e['revision']} changed ({e['sha256'][:12]} -> {h[:12]}) — "
                  f"pinned history rewritten upstream?", file=sys.stderr)
            failures += 1
            continue
        changed = not p.exists() or sha256(p.read_bytes()) != h
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        if changed or not e.get("fetched_at"):
            e["fetched_at"] = now
        e["sha256"] = h
        e["bytes"] = len(data)
        print(f"[corpus-sync] {local}  {len(data)} B  {h[:12]}"
              + ("" if changed else "  (unchanged)"))
    MANIFEST.write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8")
    return 1 if failures else 0


def check_authority_freshness() -> int:
    """The kernel's live authority file must agree with our mirrored pin.
    Disagreement is genuine upstream drift: the kernel re-pinned and the
    LTS needs a pin-bump PR."""
    local = json.loads((REPO_ROOT / AUTHORITY_LOCAL).read_text(encoding="utf-8"))
    repo, rev, path = AUTHORITY_UPSTREAM
    try:
        live = json.loads(fetch(repo, rev, path).decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code in GONE:
            print(f"[corpus-sync] AUTHORITY GONE: {repo}@{rev}/{path} -> {exc.code}",
                  file=sys.stderr)
            return 1
        print(f"[corpus-sync] authority unreachable ({exc}); freshness unknown",
              file=sys.stderr)
        return 0
    except Exception as exc:
        print(f"[corpus-sync] authority unreachable ({exc}); freshness unknown",
              file=sys.stderr)
        return 0
    if live.get("sha256") != local.get("sha256") or live.get("commit") != local.get("commit"):
        print(f"[corpus-sync] AUTHORITY DRIFT: kernel now pins "
              f"{str(live.get('commit'))[:12]}/{str(live.get('sha256'))[:12]}, "
              f"this mirror pins {str(local.get('commit'))[:12]}/"
              f"{str(local.get('sha256'))[:12]} — pin-bump PR needed "
              f"(rapp/SUCCESSION.md)", file=sys.stderr)
        return 1
    print("[corpus-sync] authority freshness OK (kernel pin == mirrored pin)")
    return 0


def cmd_check(local_only: bool) -> int:
    m = load_manifest()
    failures = 0
    skipped = 0
    for local, e in m["files"].items():
        p = safe_path(local)
        if not p.exists():
            print(f"[corpus-sync] MISSING {local}", file=sys.stderr)
            failures += 1
            continue
        h = sha256(p.read_bytes())
        if h != e.get("sha256"):
            print(f"[corpus-sync] LOCAL DRIFT {local}: {h[:12]} != manifest "
                  f"{str(e.get('sha256'))[:12]}", file=sys.stderr)
            failures += 1
            continue
        if not local_only:
            try:
                up = sha256(fetch(e["repo"], e["revision"], e["path"]))
            except urllib.error.HTTPError as exc:
                if exc.code in GONE:
                    print(f"[corpus-sync] UPSTREAM GONE {local}: "
                          f"{e['repo']}@{e['revision']} -> HTTP {exc.code}",
                          file=sys.stderr)
                    failures += 1
                else:
                    skipped += 1
                continue
            except Exception:
                skipped += 1
                continue
            if up != e["sha256"]:
                print(f"[corpus-sync] UPSTREAM PIN VIOLATION {local}: "
                      f"{e['repo']}@{e['revision']} now serves {up[:12]}",
                      file=sys.stderr)
                failures += 1
    if not local_only:
        failures += check_authority_freshness()
    n = len(m["files"])
    tail = " (local-only)" if local_only else (
        f" (local + upstream pins{f', {skipped} upstream check(s) skipped' if skipped else ''})")
    if failures:
        print(f"[corpus-sync] CHECK FAILED: {failures} problem(s) across {n} mirrors")
        return 1
    print(f"[corpus-sync] check OK: {n} mirrors intact{tail}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--fetch", action="store_true")
    g.add_argument("--check", action="store_true")
    ap.add_argument("--local-only", action="store_true",
                    help="with --check: skip all network verification")
    a = ap.parse_args()
    if a.fetch:
        return cmd_fetch()
    return cmd_check(a.local_only)


if __name__ == "__main__":
    sys.exit(main())
