#!/usr/bin/env python3
"""Aggregate outside skill/agent libraries into the AIBAST Agents Library index.

The library's aggregation posture (full design: docs/AGGREGATION.md):

  1. INDEX — catalog metadata only: name, description, tags, author, a link
     back to the origin, and any counts the source itself publishes.
  2. NORMALIZE — every source lands in one record shape under a synthetic
     ``@namespace/slug`` ref that matches the library's own naming rules, so
     the Discussions rating machinery and the metrics dashboard work on
     aggregated entries with no special case.
  3. NEVER MIRROR — skill bodies and source files are not copied into this
     repository by the crawler. Content enters the library proper only via
     the conversion pipeline: a human (or agent) converts it to a
     RAPP-compliant single-file ``skill.md`` or ``agent.py``, it passes the
     quality gates, and it lands as a normal publisher PR with attribution.

Signal fusion: source-published engagement (downloads, ratings, featured) is
carried through as ``source_signal`` and kept strictly separate from this
library's own Discussions counters — different populations measured different
ways are shown side by side, never summed.

Ranking: each record gets a ``front_page_score`` so the gallery can surface
the best entry among duplicate use cases (several sources will solve the same
problem — the aggregator's job is to put the good one on top). Today the
score is source signal only; as conversion + gate verdicts land in
``state/gate_verdicts.json`` they dominate the score (a gated, converted
skill always outranks a raw indexed one).

Usage:
    python scripts/crawl_skills.py             # crawl every enabled source
    python scripts/crawl_skills.py --only cat-agent-skills
    python scripts/crawl_skills.py --dry-run   # print, write nothing
    python scripts/crawl_skills.py --strict    # a skipped source fails the run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SHAPES_DIR = REPO_ROOT / "sentinel" / "sources"
SOURCES_FILE = REPO_ROOT / "sources.json"
OUT_FILE = REPO_ROOT / "state" / "aggregated.json"
GATES_FILE = REPO_ROOT / "state" / "gate_verdicts.json"

SCHEMA = "aibast-aggregated/1.0"
USER_AGENT = "aibast-aggregator (+https://github.com/microsoft/aibast-agents-library)"

SLUG_OK = re.compile(r"^[a-z0-9_]+$")

FAILURES: list[str] = []


def warn(msg: str) -> None:
    print(f"[crawl-skills] {msg}", file=sys.stderr)


def fail(msg: str) -> None:
    """A warning that also arms --strict (source contributed nothing)."""
    FAILURES.append(msg)
    warn(msg)


# Licenses permissive enough to redistribute a converted single file, provided
# attribution and the upstream license text travel with it.
REDISTRIBUTABLE = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "0BSD", "Unlicense"}


def resolve_license(repo: str) -> dict:
    """Ask the origin's own host what the license is. Never trust a
    hand-written field: it goes stale, and it goes stale in the direction that
    matters. An unresolvable license is recorded as unknown, which keeps the
    source index-only."""
    if not repo:
        return {"spdx": None, "verified": False, "source": None,
                "reason": "source declares no repository"}
    try:
        doc = fetch_json(f"https://api.github.com/repos/{repo}/license")
    except Exception as exc:
        return {"spdx": None, "verified": False, "source": None,
                "reason": f"license lookup failed ({exc})"}
    spdx = ((doc.get("license") or {}).get("spdx_id") or "").strip()
    if not spdx or spdx in ("NOASSERTION", "NONE"):
        return {"spdx": spdx or None, "verified": False,
                "source": doc.get("html_url"),
                "reason": "host could not classify the license"}
    return {"spdx": spdx, "verified": True,
            "name": (doc.get("license") or {}).get("name"),
            "source": doc.get("html_url"),
            "text_url": doc.get("download_url"),
            "redistributable": spdx in REDISTRIBUTABLE}


def fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))


def normalize_slug(raw: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", str(raw).lower()).strip("_")
    return slug or "unnamed"


def clip(text: str, limit: int = 400) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def parse_cat_skills(items: list, source: dict) -> list[dict]:
    """Adapter for the ``cat-skills/1`` shape.

    One adapter per source format: adding a differently-shaped source means
    adding a function here and a ``format`` entry in sources.json — the record
    shape everything downstream consumes stays fixed.
    """
    ns = source["namespace"]
    tmpl = source.get("item_url_template", "")
    out = []
    for it in items:
        raw_slug = it.get("slug") or it.get("name") or ""
        if not raw_slug:
            continue
        slug = normalize_slug(raw_slug)
        signal = {}
        if isinstance(it.get("downloads"), int):
            signal["downloads"] = it["downloads"]
        if isinstance(it.get("rating"), (int, float)) and it.get("rating"):
            signal["rating"] = it["rating"]
        if it.get("featured"):
            signal["featured"] = True
        out.append({
            "ref": f"{ns}/{slug}",
            "source_id": source["id"],
            "source_slug": raw_slug,
            "display_name": it.get("title") or it.get("display_name") or raw_slug,
            "description": clip(it.get("description")),
            "tags": [str(t) for t in (it.get("tags") or []) if t][:10],
            "author": str(it.get("author") or source.get("publisher") or ""),
            "category": str(it.get("category") or "aggregated"),
            "url": tmpl.replace("{slug}", str(raw_slug)) or source.get("home_url", ""),
            "source_signal": signal,
        })
    return out


ADAPTERS = {
    "cat-skills/1": parse_cat_skills,
}


def load_gate_verdicts() -> dict:
    """Verdicts from the quality-gate pipeline, keyed by ref. Empty until
    the gate workflow has scored something — absent is indistinguishable
    from unscored, so callers need no special case."""
    try:
        doc = json.loads(GATES_FILE.read_text(encoding="utf-8"))
        return doc.get("verdicts", {}) if isinstance(doc, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def front_page_score(rec: dict, verdict: dict | None) -> int:
    """Rank for surfacing among duplicate use cases.

    Gate-scored, converted entries dominate raw indexed ones by construction:
    a passing gate contributes 1000 per gate passed, conversion 500, while
    raw source signal can only ever contribute hundreds.
    """
    score = 0
    sig = rec.get("source_signal") or {}
    score += min(int(sig.get("downloads", 0)), 400)
    score += int(float(sig.get("rating", 0)) * 20)
    if sig.get("featured"):
        score += 100
    if verdict:
        if verdict.get("converted"):
            score += 500
        for gate in ("quality", "usability", "effectiveness"):
            g = (verdict.get("gates") or {}).get(gate) or {}
            if g.get("passed"):
                score += 1000
    return score


ALLOW_SHRINK = False


def crawl(only: str | None, dry_run: bool, strict: bool) -> int:
    if not SOURCES_FILE.exists():
        warn("sources.json missing; nothing to crawl.")
        return 1
    cfg = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    verdicts = load_gate_verdicts()
    records: list[dict] = []
    seen_refs: set[str] = set()
    sources_out = []

    for source in cfg.get("sources", []):
        sid = source.get("id", "?")
        if only and sid != only:
            continue
        if not source.get("enabled", False):
            warn(f"{sid}: disabled, skipping.")
            continue
        # Aggregation is gated on a locked shape. Every source repository is
        # laid out differently, and a crawler that guesses fails in the worst
        # way: it silently returns fewer skills than the repository holds, and
        # "0 found" looks exactly as plausible as "300 found" from outside. The
        # scout (scripts/profile_source.py) records the shape with its evidence
        # before anything is taken from a source.
        shape_file = SHAPES_DIR / f"{sid}.json"
        if not shape_file.is_file():
            fail(f"{sid}: no shape on file; run "
                 f"`python3 scripts/profile_source.py <owner/repo> --id {sid}` "
                 "before aggregating from it.")
            continue
        shape = json.loads(shape_file.read_text(encoding="utf-8"))
        if shape.get("status") not in ("locked", "provisional"):
            fail(f"{sid}: shape status is {shape.get('status')!r}; not usable.")
            continue

        adapter = ADAPTERS.get(source.get("format", ""))
        if adapter is None:
            fail(f"{sid}: no adapter for format '{source.get('format')}'.")
            continue
        try:
            payload = fetch_json(source["index_url"])
        except (OSError, ValueError, urllib.error.URLError) as exc:
            fail(f"{sid}: fetch failed ({exc}); source skipped.")
            continue
        items = payload.get("skills") if isinstance(payload, dict) else payload
        if not isinstance(items, list) or not items:
            fail(f"{sid}: index had no items; source skipped.")
            continue
        lic = resolve_license(source.get("repo", ""))
        parsed = adapter(items, source)
        pages = "https://microsoft.github.io/aibast-agents-library"
        for rec in parsed:
            rec["license"] = lic
            # A converted single file is the point of aggregating at all: an
            # indexed entry is a link, a converted one is something you can run.
            slug = rec["ref"].split("/")[-1]
            local = REPO_ROOT / "skills" / source["namespace"] / f"{slug}.md"
            if local.is_file():
                rel = f"skills/{source['namespace']}/{slug}.md"
                rec["rapp_skill"] = {
                    "path": rel,
                    "download_url": f"{pages}/{rel}",
                    "raw_url": f"https://raw.githubusercontent.com/microsoft/aibast-agents-library/main/{rel}",
                    "bytes": local.stat().st_size,
                    "format": "skill.md",
                    "license": lic.get("spdx"),
                }
        kept = 0
        for rec in parsed:
            if rec["ref"] in seen_refs:
                warn(f"{sid}: slug collision on {rec['ref']}; first one wins.")
                continue
            seen_refs.add(rec["ref"])
            v = verdicts.get(rec["ref"])
            rec["gate_verdict"] = v or None
            rec["front_page_score"] = front_page_score(rec, v)
            records.append(rec)
            kept += 1
        sources_out.append({
            "id": sid,
            "display_name": source.get("display_name", sid),
            "home_url": source.get("home_url", ""),
            "repo_url": f"https://github.com/{source['repo']}" if source.get("repo") else None,
            "license": lic,
            "items": kept,
        })
        if lic["verified"]:
            print(f"[crawl-skills] {sid}: license resolved as {lic['spdx']} "
                  f"({'redistributable' if lic.get('redistributable') else 'index-only'})",
                  file=sys.stderr)
        else:
            warn(f"{sid}: license unresolved ({lic['reason']}) — staying index-only")
        warn(f"{sid}: indexed {kept} item(s).")

    if strict and FAILURES:
        warn(f"--strict: {len(FAILURES)} source failure(s); refusing to write.")
        return 1
    if not records and not dry_run and OUT_FILE.exists():
        warn("no records crawled; keeping existing snapshot.")
        return 0

    # A crawl that suddenly returns far fewer skills is far more likely to be a
    # source that changed shape, a rate limit, or a partial fetch than a
    # repository that genuinely deleted most of its content. Overwriting the
    # snapshot in that state loses the catalog quietly, and the daily job would
    # look green while doing it. Refuse, and say what to check.
    if not dry_run and OUT_FILE.exists():
        try:
            previous = json.loads(OUT_FILE.read_text(encoding="utf-8"))
            was = len(previous.get("skills", []))
        except (OSError, ValueError):
            was = 0
        if was and len(records) < was * 0.5:
            warn(f"refusing to write: {len(records)} skill(s) crawled against "
                 f"{was} in the existing snapshot. A source has probably changed "
                 "shape — re-scout it with scripts/profile_source.py, or pass "
                 "--allow-shrink if the loss is real.")
            if not ALLOW_SHRINK:
                return 1

    records.sort(key=lambda r: (-r["front_page_score"], r["ref"]))
    snapshot = {
        "schema": SCHEMA,
        "sources": sources_out,
        "stats": {
            "total": len(records),
            "scored_by_gates": sum(1 for r in records if r["gate_verdict"]),
            "converted": sum(1 for r in records if r.get("rapp_skill")),
        },
        "skills": records,
    }
    if dry_run:
        print(json.dumps(snapshot, indent=2))
        return 0
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(f"[crawl-skills] wrote {len(records)} record(s) to "
          f"{OUT_FILE.relative_to(REPO_ROOT)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", help="crawl a single source id")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--allow-shrink", action="store_true",
                        help="permit a snapshot that loses more than half its skills")
    args = parser.parse_args()
    global ALLOW_SHRINK
    ALLOW_SHRINK = args.allow_shrink
    return crawl(args.only, args.dry_run, args.strict)


if __name__ == "__main__":
    sys.exit(main())
