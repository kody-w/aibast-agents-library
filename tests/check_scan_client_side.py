#!/usr/bin/env python3
"""scan.html must never send a visitor's content anywhere.

The page's whole promise is that you can point it at your own skills without
handing them to us. That promise is only worth stating if it is enforced, so
this fails the build if the page grows an upload path.
"""
import re
import sys
from pathlib import Path

PAGE = Path(__file__).resolve().parent.parent / "scan.html"
# Hosts the page may contact: the visitor's own source, and our own origin.
ALLOWED = {"api.github.com", "raw.githubusercontent.com", "github.com"}

def main() -> int:
    html = PAGE.read_text(encoding="utf-8")
    problems = []

    for host in {m.group(1) for m in re.finditer(r"https?://([A-Za-z0-9.-]+)", html)}:
        if host not in ALLOWED and not host.endswith("github.io"):
            problems.append(f"contacts an unexpected host: {host}")

    # Reading is fine; submitting is not.
    for banned in ("XMLHttpRequest", "sendBeacon", "FormData", "WebSocket",
                   "api_key", "apiKey", "Authorization"):
        if banned in html:
            problems.append(f"page contains {banned!r}")
    if re.search(r"method\s*:\s*[\"']POST", html):
        problems.append("page issues a POST")

    if "nothing you paste is uploaded" not in html:
        problems.append("the page no longer states the privacy promise it must keep")

    for p in problems:
        print(f"  FAIL {p}", file=sys.stderr)
    return 1 if problems else 0

if __name__ == "__main__":
    sys.exit(main())
