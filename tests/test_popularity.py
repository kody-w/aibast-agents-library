#!/usr/bin/env python3
"""Gates on the popularity report and the export signal that feeds it.

The failure this exists to prevent is a silent one. If a new export button ever
ships without going through the one function that records exports, that
solution's count reads zero forever — and zero is indistinguishable from
"nobody wanted it". The report would then be confidently wrong about which
solutions matter, with nothing on any surface to suggest it.

So the gates below check the WIRING, not just the arithmetic:

  * every writeFile in deck.js goes through save(), the choke point
  * every page that exports also loads export-signal.js
  * the report agrees with the snapshot it was built from
  * an unlaunched solution is never scored as a zero
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DECK = ROOT / "deck.js"
SIGNAL = ROOT / "export-signal.js"
POP = ROOT / "state" / "popularity.json"
EXP = ROOT / "state" / "export_engagement.json"
GUIDES = ROOT / "data" / "config_guides"

# Every page with an export button. Adding an exporter to a page not listed
# here is the mistake this list exists to catch.
EXPORT_PAGES = ["onepager.html", "architecture.html", "roadmap.html", "config.html"]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ── the choke point ──────────────────────────────────────────────────────

def test_only_save_writes_a_file():
    """writeFile is called in exactly one place: save()."""
    src = read(DECK)
    calls = [m.start() for m in re.finditer(r"\.writeFile\s*\(", src)]
    assert len(calls) == 1, (
        f"deck.js calls writeFile {len(calls)} times. Every export must go "
        "through save() so it is counted; a second call site is an export "
        "that will never appear in the popularity report."
    )
    save_at = src.index("function save(")
    body_end = src.index("\n  }", save_at)
    assert save_at < calls[0] < body_end, "the writeFile call is not inside save()"


def test_save_emits_the_signal():
    src = read(DECK)
    save = src[src.index("function save("):]
    save = save[:save.index("\n  }")]
    assert "RappExport" in save and "signal(" in save, \
        "save() writes the file but records nothing"
    # The download must survive a broken counter.
    assert "catch" in save, "a failing signal must not break the download"


def test_every_exporter_uses_save():
    """Each export entry point ends in save(), not its own writeFile."""
    src = read(DECK)
    for fn in ("writeDeck", "exportRoadmap", "exportConfigGuide"):
        assert f"function {fn}(" in src, f"{fn} is missing from deck.js"
        body = src[src.index(f"function {fn}("):]
        body = body[:body.index("\n  }\n")]
        assert "save(pptx" in body, f"{fn} does not route its export through save()"


@pytest.mark.parametrize("page", EXPORT_PAGES)
def test_export_pages_load_the_signal(page):
    p = ROOT / page
    if not p.is_file():
        pytest.skip(f"{page} is not present")
    src = read(p)
    if "RappDeck" not in src:
        pytest.skip(f"{page} does not export")
    assert "export-signal.js" in src, (
        f"{page} exports a deck but never loads export-signal.js, so every "
        "export from this page is invisible to the popularity report."
    )


def test_signal_never_blocks_or_writes():
    src = read(SIGNAL)
    assert "localStorage" in src, "the local record is missing"
    # Nothing may be POSTed anywhere: there is no backend, and a page that
    # tried would be sending visitor behaviour to a third party.
    assert not re.search(r'method\s*:\s*["\']POST', src), \
        "export-signal.js must not POST anything"
    assert "catch" in src, "a failed count must never surface as a failed export"


# ── the report ───────────────────────────────────────────────────────────

def test_report_agrees_with_the_snapshot():
    doc = json.loads(read(POP))
    rows = doc["ranked"] + doc["not_launched"]
    assert doc["counts"]["solutions"] == len(rows)
    for key in doc["weights"]:
        assert doc["totals"][key] == sum(r["signals"][key] for r in rows), \
            f"the {key} total disagrees with the rows it was summed from"


def test_ranking_is_ordered_and_scored_by_the_published_weights():
    doc = json.loads(read(POP))
    w = doc["weights"]
    scores = [r["score"] for r in doc["ranked"]]
    assert scores == sorted(scores, reverse=True), "the ranked list is not ordered"
    for r in doc["ranked"]:
        assert r["score"] == sum(r["signals"][k] * w[k] for k in w), (
            f"{r['slug']} scores {r['score']}, which is not what the published "
            "weights produce — the report would be unarguable-with."
        )


def test_unlaunched_solutions_are_listed_not_ranked_zero():
    doc = json.loads(read(POP))
    for r in doc["not_launched"]:
        assert not r["launched"]
        assert r["slug"] not in {x["slug"] for x in doc["ranked"]}, \
            f"{r['slug']} is both unlaunched and ranked"


def test_led_by_names_the_dominant_signal():
    """A row's led_by must be the signal that actually carried its score."""
    doc = json.loads(read(POP))
    w = doc["weights"]
    for r in doc["ranked"]:
        if not r["score"]:
            assert r["led_by"] is None
            continue
        contrib = {k: r["signals"][k] * w[k] for k in w}
        assert contrib[r["led_by"]] == max(contrib.values()), (
            f"{r['slug']} is labelled '{r['led_by']}' but that is not the "
            "signal that carried its score — the row invites the exact "
            "misreading the column exists to prevent."
        )


def test_every_solution_has_an_export_subject():
    """No solution may be exportable but uncounted."""
    exp = json.loads(read(EXP))["exports"]
    onep = json.loads(read(ROOT / "data" / "onepagers.json"))["onepagers"]
    missing = [e["slug"] for e in onep if e.get("slug") and e["slug"] not in exp]
    assert not missing, f"solutions with no export subject: {missing}"


# ── the guides ───────────────────────────────────────────────────────────

def test_config_guides_are_well_formed():
    if not GUIDES.is_dir():
        pytest.skip("no configuration guides yet")
    kinds = {"title", "summary", "statement", "architecture", "products",
             "adventure", "steps", "synthetic", "close"}
    for p in sorted(GUIDES.glob("*.json")):
        g = json.loads(read(p))
        assert g["slug"] == p.stem, f"{p.name}: slug does not match the filename"
        assert g.get("slides"), f"{p.name}: no slides"
        for s in g["slides"]:
            assert s.get("kind") in kinds, \
                f"{p.name}: slide kind '{s.get('kind')}' has no renderer"
            assert s.get("title") or s["kind"] == "architecture", \
                f"{p.name}: a {s['kind']} slide has no title"


def test_every_content_slide_states_its_conclusion():
    """A slide without a takeaway makes the reader derive the point.

    That is the difference between a deck that informs and one that argues,
    and it is the thing that gets a different conclusion in every room. The
    title and closing slides are exempt: they carry no argument to conclude.
    """
    if not GUIDES.is_dir():
        pytest.skip("no configuration guides yet")
    for p in sorted(GUIDES.glob("*.json")):
        g = json.loads(read(p))
        for s in g["slides"]:
            if s["kind"] in {"title", "close"}:
                continue
            assert s.get("takeaway"), \
                f"{p.name}: the '{s['id']}' slide states no conclusion"
            assert len(s["takeaway"]) < 160, \
                f"{p.name}: the '{s['id']}' takeaway is a paragraph, not a point"


def test_guide_products_resolve_to_a_real_catalog_entry():
    """A guide may not invent a product id — a wrong id renders a blank mark."""
    if not GUIDES.is_dir():
        pytest.skip("no configuration guides yet")
    known = {p["id"] for p in
             json.loads(read(ROOT / "data" / "products.json"))["products"]}
    for p in sorted(GUIDES.glob("*.json")):
        g = json.loads(read(p))
        for s in g["slides"]:
            ids = [r.get("id") for r in s.get("rows", []) if s["kind"] == "products"]
            ids += [r.get("microsoft_id") for r in s.get("rows", [])
                    if s["kind"] == "adventure"]
            for pid in filter(None, ids):
                assert pid in known, (
                    f"{p.name}: product id '{pid}' is not in the products "
                    "catalog, so its mark would silently render as nothing."
                )
