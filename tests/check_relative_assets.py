#!/usr/bin/env python3
"""In-repo assets must be linked by repo-relative path, not canonical URL.

The static API publishes canonical `microsoft.github.io` URLs for machine
consumers, which is right — an API result should be dereferenceable from
anywhere. A PAGE is different: it is already being served from some origin, and
hardcoding the canonical one means every download button 404s on a fork, a
preview deploy, or a local checkout until the change merges upstream.

That is exactly how this was found: the skill.md download on the fork pointed at
the upstream site, where the file did not exist yet.

Repo-relative resolves on whichever origin is serving the page, so it is correct
before AND after merge.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["onepager.html", "agents.html", "solutions.html", "scan.html",
         "metrics.html", "wall.html", "api.html", "index.html"]

# An href/src built from one of these fields points at a file in THIS repo, so
# it must fall back to the relative path before the absolute URL.
ABSOLUTE_FIELDS = ("download_url", "raw_url", "pages_url")
RELATIVE_FALLBACKS = ("path", "file", "src")


def main() -> int:
    problems = []
    for name in PAGES:
        page = ROOT / name
        if not page.is_file():
            continue
        for i, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1):
            if not re.search(r'\b(href|src)\s*=\s*["\']?\s*\+?', line) and "href=" not in line:
                continue
            for field in ABSOLUTE_FIELDS:
                if f".{field}" not in line:
                    continue
                # Acceptable when a relative fallback is offered first.
                if any(f".{alt}" in line for alt in RELATIVE_FALLBACKS):
                    continue
                # A plain link out to GitHub's UI is not an in-repo asset.
                if "github_url" in line or "target=" in line:
                    continue
                problems.append(
                    f"{name}:{i} links an in-repo asset by {field} with no "
                    f"relative fallback — this 404s on a fork until merge")

    for p in problems:
        print(f"  FAIL {p}", file=sys.stderr)
    if not problems:
        print(f"[relative-assets] {len(PAGES)} pages: in-repo downloads resolve "
              "on whichever origin serves them")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
