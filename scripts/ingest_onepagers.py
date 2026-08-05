#!/usr/bin/env python3
"""Ingest captured AIBAST solution one-pagers into the library's data layer.

The AIBAST solution catalog was authored as slides and published to an
internal SharePoint site. Those artifacts were extracted to a local capture
directory; this script turns that capture into structured, publishable data
so the GitHub Pages library can reproduce the one-pager surface feature for
feature — with traceability and engagement tracking the slide deck never had.

What it does NOT carry across:

  * SharePoint URLs. Those links embed a sharing token in the path; a token
    is a credential, and credentials never enter a public repository. The
    output is checked for them and the run fails if one survives.
  * Anything that looks like a person. The capture is solution marketing
    copy, but the check is cheap and the cost of missing one is not.

Source layout expected under --source:
    onepagers/NN-slug.html       rendered one-pager (the visual contract)
    listings/slug.md             captured catalog listing (industries, personas)
    crosswalk.json               numbering -> {name, video, pptx, listing}
    onepager_video_urls.csv      name,industry,onePager_pptx,demoVideo

Output:
    data/onepagers.json          committed source of truth for the surface

Usage:
    python3 scripts/ingest_onepagers.py --source ~/Desktop/aibast_bible
    python3 scripts/ingest_onepagers.py --source ... --check
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_FILE = REPO_ROOT / "data" / "onepagers.json"
MEDIA_DIR = REPO_ROOT / "media" / "videos"

SCHEMA = "aibast-onepagers/1.0"

# A SharePoint sharing URL carries an access token in its path. Publishing one
# is publishing a credential, so this is a hard failure, not a warning.
FORBIDDEN_URL = re.compile(r"https?://[a-z0-9.-]*sharepoint\.com\S*", re.I)
# Cheap PII tripwires over the copy we are about to publish.
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")

LBL_BLOCK = re.compile(
    r'<div class="lbl">([^<]+)</div>(.*?)(?=<div class="lbl">|<div class="src">|<div class="foot">)',
    re.S,
)
TAG = re.compile(r"<[^>]+>")


def text_of(fragment: str) -> str:
    return html.unescape(TAG.sub(" ", fragment)).strip()


def items_of(fragment: str, cls: str) -> list[str]:
    out = []
    for m in re.finditer(rf'<{"li" if cls == "li" else "span"}[^>]*>(.*?)</', fragment, re.S):
        v = text_of(m.group(1))
        if v:
            out.append(re.sub(r"\s+", " ", v))
    return out


def parse_onepager(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    doc: dict = {"capture_file": path.name}

    m = re.search(r'<div class="kicker">(.*?)</div>', raw, re.S)
    doc["industry"] = text_of(m.group(1)).title() if m else ""
    m = re.search(r"<h1>(.*?)</h1>", raw, re.S)
    doc["display_name"] = text_of(m.group(1)) if m else ""
    m = re.search(r'<p class="lede">(.*?)</p>', raw, re.S)
    doc["lede"] = re.sub(r"\s+", " ", text_of(m.group(1))) if m else ""

    for label, frag in LBL_BLOCK.findall(raw):
        key = label.strip().lower()
        if key.startswith("who"):
            doc["audience"] = [
                p.strip() for p in re.split(r"·|;", text_of(frag)) if p.strip()
            ]
        elif key.startswith("business"):
            doc["business_value"] = items_of(frag, "li")
        elif key.startswith("built"):
            doc["built_with"] = items_of(frag, "chip")
        elif key.startswith("featured"):
            doc["featured_tools"] = items_of(frag, "chip")

    m = re.search(r'<div class="foot">(.*?)</div>', raw, re.S)
    doc["footnote"] = re.sub(r"\s+", " ", text_of(m.group(1))) if m else ""
    return doc


def parse_listing(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    out: dict = {"listing_file": path.name, "personas": [], "industries": [], "requires": []}
    body: list[str] = []
    for line in lines:
        s = line.strip()
        if s.startswith("#"):
            continue
        low = s.lower()
        if low.startswith("industries:"):
            out["industries"] = [p.strip() for p in re.split(r"[;|]", s.split(":", 1)[1]) if p.strip()]
        elif low.startswith("personas:"):
            out["personas"] = [p.strip() for p in re.split(r"[;|]", s.split(":", 1)[1]) if p.strip()]
        elif low.startswith("agent requirements"):
            out["requires"] = [p.strip() for p in re.split(r"[;|]", s.split(":", 1)[1]) if p.strip()]
        elif s:
            body.append(s)
    out["summary"] = " ".join(body).strip()
    return out


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return re.sub(r"-+", "-", s)


def video_slug(filename: str) -> str:
    stem = Path(filename).stem.lstrip("#")
    stem = re.sub(r"^[0-9]+(-[0-9]+)?-", "", stem)
    return slugify(stem)


def build(source: Path) -> dict:
    op_dir, listing_dir = source / "onepagers", source / "listings"
    if not op_dir.is_dir():
        raise SystemExit(f"no one-pagers under {op_dir}")

    listings = {p.stem: parse_listing(p) for p in sorted(listing_dir.glob("*.md"))} if listing_dir.is_dir() else {}

    crosswalk = {}
    cw_file = source / "crosswalk.json"
    if cw_file.is_file():
        for num, rec in json.loads(cw_file.read_text(encoding="utf-8")).items():
            entry = {**rec, "number": int(num)}
            # The catalog listing name and the demo-recording name drifted apart
            # for several solutions, so index under both spellings.
            for alias in (rec.get("name"), rec.get("canonical"), Path(rec.get("listing", "")).stem):
                if alias:
                    crosswalk.setdefault(slugify(alias), entry)

    industries_by_name = {}
    csv_file = source / "onepager_video_urls.csv"
    if csv_file.is_file():
        with csv_file.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                industries_by_name[slugify(row["name"])] = [
                    p.strip() for p in re.split(r"[|,]", row.get("industry", "")) if p.strip()
                ]

    entries = []
    for path in sorted(op_dir.glob("*.html")):
        doc = parse_onepager(path)
        slug = re.sub(r"^\d+-", "", path.stem)
        doc["slug"] = slug
        name_slug = slugify(doc["display_name"])

        listing = listings.get(slug) or listings.get(name_slug) or {}
        for key in ("personas", "industries", "requires", "summary", "listing_file"):
            if listing.get(key):
                doc[key] = listing[key]
        if not doc.get("industries") and industries_by_name.get(name_slug):
            doc["industries"] = industries_by_name[name_slug]
        if not doc.get("industries") and doc.get("industry"):
            doc["industries"] = [doc["industry"]]

        cw = crosswalk.get(name_slug) or crosswalk.get(slugify(slug)) or {}
        if cw.get("number"):
            doc["catalog_number"] = cw["number"]
        if cw.get("video"):
            vslug = video_slug(cw["video"])
            local = MEDIA_DIR / f"{vslug}.mp4"
            doc["video"] = {
                "slug": vslug,
                "hosted": local.is_file(),
                "src": f"media/videos/{vslug}.mp4" if local.is_file() else None,
                "size_mb": round(local.stat().st_size / 1048576, 2) if local.is_file() else None,
            }
        entries.append(doc)

    entries.sort(key=lambda d: (d.get("catalog_number") or 999, d["slug"]))
    return {
        "schema": SCHEMA,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "AIBAST solution catalog (captured); sharing URLs deliberately omitted",
        "count": len(entries),
        "hosted_videos": sum(1 for e in entries if (e.get("video") or {}).get("hosted")),
        "onepagers": entries,
    }


def audit(doc: dict) -> list[str]:
    blob = json.dumps(doc)
    problems = []
    for hit in set(FORBIDDEN_URL.findall(blob)):
        problems.append(f"sharing URL survived ingest (carries an access token): {hit[:60]}")
    for hit in set(EMAIL.findall(blob)):
        problems.append(f"email address in publishable copy: {hit}")
    for entry in doc["onepagers"]:
        missing = [k for k in ("display_name", "lede", "business_value", "built_with") if not entry.get(k)]
        if missing:
            problems.append(f"{entry['slug']}: capture parsed with empty {', '.join(missing)}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", default="~/Desktop/aibast_bible", help="capture directory")
    ap.add_argument("--check", action="store_true", help="audit only, write nothing")
    args = ap.parse_args()

    doc = build(Path(args.source).expanduser())
    problems = audit(doc)
    for p in problems:
        print(f"  FAIL {p}", file=sys.stderr)
    if problems:
        return 1

    print(f"[onepagers] {doc['count']} one-pagers, {doc['hosted_videos']} with hosted video")
    if not args.check:
        OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUT_FILE.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        print(f"[onepagers] wrote {OUT_FILE.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
