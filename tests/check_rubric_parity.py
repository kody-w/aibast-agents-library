#!/usr/bin/env python3
"""sentinel.js and scripts/review_skills.py must be the same rubric.

The scan page tells outsiders what this library believes about their skills. If
the browser implementation drifts from the reference, we are telling them
something we do not check ourselves.

This compares the declared surface: same check ids, same principles, same
version. Behavioural parity — every check, over every skill in the library — is
proved in tests/render_headless.py, which runs both and diffs the verdicts.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def main() -> int:
    js = (ROOT / "sentinel.js").read_text(encoding="utf-8")
    py = (ROOT / "scripts" / "review_skills.py").read_text(encoding="utf-8")
    problems = []

    js_ids = set(re.findall(r'add\("(K\d+)"', js))
    py_ids = set(re.findall(r'add\("(K\d+)"', py))
    if js_ids != py_ids:
        problems.append(f"check ids differ: {sorted(js_ids ^ py_ids)}")

    js_p = set(re.findall(r"^\s{4}(\w+):", js, re.M)) & set(re.findall(r'"(\w+)":', py))
    for principle in ("provenance", "usability", "determinism", "safety", "completeness"):
        if principle not in js or principle not in py:
            problems.append(f"principle missing from one side: {principle}")

    js_v = re.search(r'RUBRIC_VERSION = "([^"]+)"', js)
    py_v = re.search(r'RUBRIC_VERSION = "([^"]+)"', py)
    if not js_v or not py_v or js_v.group(1) != py_v.group(1):
        problems.append("rubric versions differ")

    for p in problems:
        print(f"  FAIL {p}", file=sys.stderr)
    return 1 if problems else 0

if __name__ == "__main__":
    sys.exit(main())
