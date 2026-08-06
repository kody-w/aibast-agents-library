#!/usr/bin/env python3
"""Prove the PowerPoint export produces a real, openable deck.

The button it replaced called `window.print()`, which cannot fail and cannot be
tested — the browser either printed something or it didn't, and what came out
was a picture of a web page. A deck is a file with a structure, so it can be
checked: it must be a valid OOXML package, it must contain the number of slides
we built, and the agent's own words must actually be in the slide XML rather
than in an image nobody can edit.

That last check is the point. A screenshot pasted into a slide would pass
"is it a pptx"; only reading the text out of the slide parts proves the deck is
native and a human can retitle, reorder, or reuse it.

Exit code is the number of failures.

Usage:
    python3 tests/check_deck_export.py
    python3 tests/check_deck_export.py --agent account-intelligence
"""
from __future__ import annotations

import argparse
import http.server
import json
import re
import socketserver
import sys
import tempfile
import threading
import zipfile
from functools import partial
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FAILS: list[str] = []


def check(ok: bool, gate: str, detail: str) -> bool:
    FAILS.append(f"{gate}: {detail}") if not ok else None
    print(f"  {'PASS' if ok else 'FAIL'}  {gate}  {detail}")
    return ok


def serve():
    handler = partial(http.server.SimpleHTTPRequestHandler,
                      directory=str(REPO_ROOT))
    srv = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--agent", default="account-intelligence")
    args = ap.parse_args()

    print("Deck export gates")

    lib = REPO_ROOT / "vendor" / "pptxgen.min.js"
    check(lib.is_file() and lib.stat().st_size > 100_000, "T-DECK-VENDORED",
          f"pptxgen.min.js vendored ({lib.stat().st_size // 1024 if lib.is_file() else 0} KB) "
          "— no CDN, so it works behind an enterprise proxy")

    for page in ("onepager.html", "architecture.html"):
        html = (REPO_ROOT / page).read_text(encoding="utf-8")
        check("window.print()" not in html, "T-DECK-NO-PDF",
              f"{page} no longer offers a printed PDF")
        check("Export as PowerPoint" in html, "T-DECK-BUTTON",
              f"{page} offers the PowerPoint export")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        check(False, "T-DECK-BUILD", "playwright unavailable; cannot build a deck")
        return len(FAILS)

    story_path = REPO_ROOT / "media" / "walkthroughs" / f"agent-{args.agent}.json"
    if not story_path.is_file():
        check(False, "T-DECK-BUILD", f"no storyboard at {story_path.name}")
        return len(FAILS)
    story = json.loads(story_path.read_text(encoding="utf-8"))

    srv, port = serve()
    out = Path(tempfile.mkdtemp()) / "deck.pptx"
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            ctx = b.new_context(accept_downloads=True)
            pg = ctx.new_page()
            pg.goto(f"http://127.0.0.1:{port}/onepager.html?agent={args.agent}",
                    wait_until="load")
            pg.wait_for_function("() => typeof PptxGenJS !== 'undefined' "
                                 "&& typeof RappDeck !== 'undefined'", timeout=20000)
            with pg.expect_download(timeout=30000) as dl:
                pg.evaluate("""(story) => RappDeck.export({
                    kind: "agent",
                    entry: {name: "test", description: "A test agent for the gate.",
                            tags: ["sales"], requires_env: ["EXAMPLE_KEY"],
                            category: "b2b_sales"},
                    story: story, onStatus: function(){}
                })""", story)
            dl.value.save_as(str(out))
            b.close()
    except Exception as e:                                   # noqa: BLE001
        check(False, "T-DECK-BUILD", f"the browser could not produce a deck: {e}")
        srv.shutdown()
        return len(FAILS)
    srv.shutdown()

    if not check(out.is_file() and out.stat().st_size > 8_000, "T-DECK-BUILD",
                 f"deck written, {out.stat().st_size // 1024 if out.is_file() else 0} KB"):
        return len(FAILS)

    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        slides = sorted(n for n in names
                        if re.fullmatch(r"ppt/slides/slide\d+\.xml", n))
        check("[Content_Types].xml" in names and bool(slides),
              "T-DECK-OOXML", f"valid OOXML package with {len(slides)} slide(s)")
        check(len(slides) >= 6, "T-DECK-SLIDES",
              f"{len(slides)} slides — title, what it is, overview, "
              "walkthrough, setup, close")
        xml = " ".join(z.read(n).decode("utf-8", "replace") for n in slides)

    def strip(t):
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t))

    text = strip(xml)
    check("Get started on your agentic journey today" in text,
          "T-DECK-CTA", "the close carries the campaign call to action")

    name = story.get("subject", {}).get("display_name", "")
    check(bool(name) and name.split()[0] in text, "T-DECK-SUBJECT",
          f"the deck names its subject ({name!r})")

    # Native, not a screenshot: the storyboard's own panel copy has to be in the
    # slide XML as text. An image would satisfy every check above and none of this.
    panels = {}
    for sc in story.get("scenes", []):
        if sc.get("act") == "overview" and sc.get("panels"):
            panels = sc["panels"]
    wanted = [k for k in panels] + [v for vals in panels.values() for v in vals[:1]]
    missing = [w for w in wanted if w and w not in text]
    check(not missing, "T-DECK-NATIVE-TEXT",
          "panel copy is real editable text in the slides"
          if not missing else f"missing from slide XML: {missing[:3]}")

    # PptxGenJS always writes one small package-level image asset. What matters
    # is that the CONTENT is not pictures: a screenshot deck carries a big image
    # per slide, so compare image bytes against slide count.
    with zipfile.ZipFile(out) as z:
        media = [n for n in z.namelist() if n.startswith("ppt/media/")]
        mbytes = sum(z.getinfo(n).file_size for n in media)
    check(mbytes < 60_000 * len(slides), "T-DECK-NOT-SCREENSHOTS",
          f"{len(media)} media asset(s), {mbytes // 1024} KB across {len(slides)} "
          "slides — shapes and text, not screenshots")

    print(f"\n{len(FAILS)} failed")
    for f in FAILS:
        print(f"  ✗ {f}")
    return len(FAILS)


if __name__ == "__main__":
    sys.exit(main())
