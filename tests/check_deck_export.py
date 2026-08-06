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

    # A second, real subject: an entry the architecture catalog knows and that
    # serves more than one industry. The end-to-end architecture slide is
    # required PER INDUSTRY, and a single-industry entry cannot prove that.
    multi_slug, multi_entry, multi_inds = "", None, []
    arch_file = REPO_ROOT / "data" / "architectures.json"
    if arch_file.is_file():
        for a in json.loads(arch_file.read_text(encoding="utf-8"))["architectures"]:
            if len(a.get("industries") or []) > 1:
                multi_slug, multi_entry, multi_inds = a["slug"], a, a["industries"]
                break

    srv, port = serve()
    tmp = Path(tempfile.mkdtemp())
    out, multi_out = tmp / "deck.pptx", tmp / "multi.pptx"
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
            if multi_entry:
                with pg.expect_download(timeout=30000) as dl2:
                    pg.evaluate("""(a) => RappDeck.export({
                        kind: "solution", entry: a.entry, slug: a.slug,
                        story: null, onStatus: function(){}
                    })""", {"entry": multi_entry, "slug": multi_slug})
                dl2.value.save_as(str(multi_out))
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
        check(len(slides) >= 7, "T-DECK-SLIDES",
              f"{len(slides)} slides — title, what it is, overview, "
              "walkthrough, architecture, setup, close")
        xml = " ".join(z.read(n).decode("utf-8", "replace") for n in slides)

    def strip(t):
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t))

    text = strip(xml)

    # The end-to-end architecture is REQUIRED in every deck, and it is required
    # even when the catalog cannot be reached — this deck is built from a
    # synthetic entry that is in no catalog, so it exercises the derived path.
    # Nobody buys a chat window; they buy the thing that sits in their estate.
    check("Example architecture for" in text, "T-DECK-ARCH-REQUIRED",
          "the deck carries the end-to-end architecture slide")
    columns = ["Knowledge", "Processing", "User Interface", "Reporting"]
    missing_cols = [c for c in columns if c not in text]
    check(not missing_cols, "T-DECK-ARCH-COLUMNS",
          "all four architecture columns present"
          if not missing_cols else f"missing columns: {missing_cols}")
    flow = ["Natural language input", "Preliminary checks",
            "Formulates a plan", "NL response after guideline checks",
            "Action taken in the system of record", "Feedback"]
    missing_flow = [f for f in flow if f not in text]
    check(not missing_flow, "T-DECK-ARCH-FLOW",
          "the six-step request flow is numbered through the columns"
          if not missing_flow else f"missing steps: {missing_flow}")
    bands = ["Model Context Protocol", "Entra ID"]
    missing_bands = [b_ for b_ in bands if b_ not in text]
    check(not missing_bands, "T-DECK-ARCH-BANDS",
          "tools and supporting-features bands present"
          if not missing_bands else f"missing: {missing_bands}")

    # The setup slide used to print "No configuration / None" over half a page
    # of white. True, and useless to the person holding the deck.
    check("No configuration" not in text, "T-DECK-NO-EMPTY-SETUP",
          "the setup slide no longer answers with an empty page")
    for phrase in ("Systems it connects to", "Who it is for"):
        check(phrase in text, "T-DECK-JEWELS",
              f"the setup slide carries {phrase!r} from the library catalogs")

    if multi_entry:
        with zipfile.ZipFile(multi_out) as z:
            mslides = sorted(n for n in z.namelist()
                             if re.fullmatch(r"ppt/slides/slide\d+\.xml", n))
            mtext = strip(" ".join(z.read(n).decode("utf-8", "replace")
                                   for n in mslides))
        seen = mtext.count("Example architecture for")
        check(seen == len(multi_inds), "T-DECK-ARCH-PER-INDUSTRY",
              f"{multi_slug}: {seen} architecture slide(s) for "
              f"{len(multi_inds)} industries {multi_inds}")
        missing_ind = [i for i in multi_inds if i.upper() not in mtext.upper()]
        check(not missing_ind, "T-DECK-ARCH-INDUSTRY-NAMED",
              "each architecture slide names its industry"
              if not missing_ind else f"unnamed: {missing_ind}")
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
