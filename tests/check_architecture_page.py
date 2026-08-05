#!/usr/bin/env python3
"""architecture.html must wire every part of the format it claims to draw.

Column titles come from the data rather than the markup, so asserting on
literal strings in the HTML tests the wrong thing — this checks the wiring, and
tests/render_headless.py checks what actually renders.
"""
import sys
from pathlib import Path

PAGE = Path(__file__).resolve().parent.parent / "architecture.html"

REQUIRED = [
    ("c.knowledge", "the Knowledge column"),
    ("c.processing", "the Processing column"),
    ("c.interface", "the User Interface column"),
    ("c.reporting", "the Reporting column"),
    ("tools_band", "the Tools band"),
    ("foundation_band", "the Supporting Features band"),
    ("a.flow", "the numbered request flow"),
    ("architectures.json", "the generated architecture data"),
    ("window.print", "print / save as PDF"),
    ('class="group"', "the dashed grouping boxes"),
    ('class="hl"', "the governance highlight"),
    ('class="step"', "the flow steps"),
]


def main() -> int:
    html = PAGE.read_text(encoding="utf-8")
    missing = [why for token, why in REQUIRED if token not in html]
    for why in missing:
        print(f"  FAIL architecture.html does not draw {why}", file=sys.stderr)
    if not missing:
        print(f"[architecture-page] all {len(REQUIRED)} parts of the format are wired")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
