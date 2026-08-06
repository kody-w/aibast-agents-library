#!/usr/bin/env python3
"""Fail if a customer name from a source analysis reaches the repository.

The FY27 priority scenarios were derived from a cross-customer analysis that
names real organisations against every scenario. The scenarios are ours to
publish; the attribution is not. This is the gate that keeps the second out.

It exists because the boundary is easy to cross by accident and impossible to
uncross: a name lands in a manifest or a provenance note, the registry is built,
the static API is published, and it is in someone's cache before anyone reads
the diff.

Two lessons are encoded in how it matches:

  * WORD BOUNDARIES, case-sensitive. A substring scan reported "EDF" inside hex
    digests in minified vendor JavaScript and "Tanium" inside the invented
    account name "Titanium Holdings" — six false hits that would have trained
    everyone to ignore the gate.
  * Binary and vendored files are skipped, for the same reason.

Add a name here when a new source analysis is ingested. Removing one requires a
reason in the commit message.

Exit code is the number of names found.

Usage:
    python3 tests/check_no_customer_names.py
    python3 tests/check_no_customer_names.py --add "Some Org"
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Organisations named in ingested source analyses. Never publishable.
CUSTOMER_NAMES = [
    "Banorte", "Invesco", "Sitecore", "Tanium", "DuPont", "Riigikantselei",
    "Manitoba", "Admiral", "ANDRITZ", "BePyme", "Fleetwood", "LexAssist",
    "Pipeline Pulse", "Õigusloome",
]

SKIP_SUFFIX = {".png", ".jpg", ".jpeg", ".gif", ".mp4", ".mov", ".caf", ".wav",
               ".zip", ".pyc", ".ico", ".woff", ".woff2", ".pdf", ".pptx"}
SKIP_DIRS = ("vendor/", "node_modules/", ".git/", "archive/")


def tracked_files() -> list[str]:
    out = []
    for args in (["git", "ls-files"],
                 ["git", "ls-files", "--others", "--exclude-standard"]):
        r = subprocess.run(args, capture_output=True, text=True, cwd=REPO_ROOT)
        out += r.stdout.split("\n")
    return [f for f in out if f]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--add", help="add a name to the denylist and exit")
    args = ap.parse_args()

    if args.add:
        src = pathlib.Path(__file__).read_text(encoding="utf-8")
        src = src.replace('    "Pipeline Pulse", "Õigusloome",',
                          f'    "Pipeline Pulse", "Õigusloome", "{args.add}",')
        pathlib.Path(__file__).write_text(src, encoding="utf-8")
        print(f"[pii] added {args.add!r}")
        return 0

    pat = re.compile(r"\b(" + "|".join(re.escape(n) for n in CUSTOMER_NAMES) + r")\b")
    hits: dict[str, set] = {}
    scanned = 0
    for f in tracked_files():
        if any(f.startswith(d) for d in SKIP_DIRS):
            continue
        p = REPO_ROOT / f
        if p.suffix.lower() in SKIP_SUFFIX or not p.is_file():
            continue
        # This file names them by definition.
        if p.resolve() == pathlib.Path(__file__).resolve():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        scanned += 1
        for m in pat.finditer(text):
            hits.setdefault(m.group(1), set()).add(f)

    print(f"[pii] scanned {scanned} text files against {len(CUSTOMER_NAMES)} names")
    if not hits:
        print("[pii] PASS — no customer name from an ingested analysis is in the repo")
        return 0
    for name, files in sorted(hits.items()):
        print(f"[pii] FAIL {name!r} in: {', '.join(sorted(files)[:5])}", file=sys.stderr)
    return len(hits)


if __name__ == "__main__":
    sys.exit(main())
