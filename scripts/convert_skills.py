#!/usr/bin/env python3
"""Convert aggregated outside skills into RAPP single-file skills.

This is where aggregation stops being a search index and starts being useful:
an indexed entry links back to its origin, a CONVERTED entry is a single
`skill.md` you can download and drop straight onto a brainstem.

Only sources whose license the crawler RESOLVED as redistributable are
converted, and every converted file carries attribution, the upstream license,
and a link back — redistribution with credit, never quiet appropriation.

Output: skills/@<namespace>/<slug>.md, one self-contained file each.

Usage:
    python3 scripts/convert_skills.py             # convert everything eligible
    python3 scripts/convert_skills.py --only chart-builder
    python3 scripts/convert_skills.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCES = REPO_ROOT / "sources.json"
AGGREGATED = REPO_ROOT / "state" / "aggregated.json"
OUT_ROOT = REPO_ROOT / "skills"
USER_AGENT = "aibast-skill-converter"

CATEGORY_HINTS = [
    (("chart", "plot", "graph", "data", "csv", "excel"), "general"),
    (("doc", "word", "pdf", "presentation", "slide", "ppt"), "general"),
    (("crm", "sales", "deal", "opportunity"), "b2b_sales"),
    (("hr", "people", "employee"), "human_resources"),
    (("it", "ticket", "helpdesk", "incident"), "it_management"),
    (("finance", "invoice", "payment", "budget"), "financial_services"),
]


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    head, body = text[3:end], text[end + 4:]
    meta: dict = {}
    for line in head.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            meta[k] = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
        else:
            meta[k] = v.strip("'\"")
    return meta, body.lstrip("\n")


def guess_category(tags, text) -> str:
    hay = " ".join(list(tags) + [text[:400]]).lower()
    for words, cat in CATEGORY_HINTS:
        if any(w in hay for w in words):
            return cat
    return "general"


def yaml_list(values) -> str:
    return "[" + ", ".join(json.dumps(str(v)) for v in values) + "]"


def convert(entry: dict, source: dict, lic: dict) -> str:
    """Produce one RAPP-compliant single-file skill."""
    slug = entry["source_slug"]
    url = source["content_url_template"].format(slug=slug)
    raw = fetch_text(url)
    meta, body = split_frontmatter(raw)

    name = meta.get("name") or entry["display_name"]
    desc = meta.get("description") or entry.get("description", "")
    tags = meta.get("tags") or entry.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    version = meta.get("version") or "1.0.0"
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        version = "1.0.0"
    author = meta.get("author") or entry.get("author") or source["display_name"]
    when = meta.get("agentDescription") or desc
    origin = entry.get("url") or source.get("home_url", "")
    bundle = None
    if meta.get("bundle") and source.get("bundle_url_template"):
        bundle = source["bundle_url_template"].format(slug=slug)

    ref = f"@{source['namespace'].lstrip('@')}/{entry['ref'].split('/')[-1]}"

    return f"""---
schema: rapp-skill/1.0
name: {ref}
version: {version}
display_name: {json.dumps(name)}
description: {json.dumps(desc)}
author: {json.dumps(author)}
tags: {yaml_list(tags[:8])}
category: {guess_category(tags, body)}
requires_env: []
source_ref: {entry['ref']}
source_url: {origin}
source_license: {lic.get('spdx')}
converted_from: {source['display_name']}
converted_on: {datetime.now(timezone.utc).date().isoformat()}
---

# {name}

> **Converted skill.** This is a RAPP single-file skill converted from
> **{source['display_name']}** ([origin]({origin})), redistributed under
> **{lic.get('spdx')}** with attribution. Original author: {author}.
> Upstream license text: {lic.get('text_url')}
>
> Drop this file into your brainstem's skills folder, or read it and run the
> steps yourself. Everything the skill needs is in this one file.

## When to use this

{when}

## The deterministic layer

RAPP skills state their contract explicitly, so two runs of the same skill do
the same thing:

- **Inputs** — whatever the steps below name. If an input is missing, say so
  and stop rather than guessing.
- **Outputs** — the artifact the steps produce, named where it is written.
- **Verification** — before reporting success, confirm the output exists and
  matches what was asked. A silent partial result is a failure.
- **Configuration** — never hardcode an endpoint, key, or tenant. Read them
  from the environment (`requires_env` above lists what this skill needs).

## Skill

{body.strip()}

---

*Converted for the AIBAST Agents Library from {source['display_name']}.
The original is authoritative; this file adds the RAPP manifest and the
deterministic layer above, and changes nothing else about the instructions.*
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", help="convert a single source slug")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="stop after N conversions")
    args = ap.parse_args()

    cfg = json.loads(SOURCES.read_text(encoding="utf-8"))
    agg = json.loads(AGGREGATED.read_text(encoding="utf-8"))
    by_id = {s["id"]: s for s in cfg.get("sources", [])}
    lic_by_id = {s["id"]: s.get("license", {}) for s in agg.get("sources", [])}

    made, skipped, failed = [], [], []
    for entry in agg.get("skills", []):
        sid = entry["source_id"]
        source, lic = by_id.get(sid), lic_by_id.get(sid, {})
        if not source or not source.get("content_url_template"):
            skipped.append((entry["ref"], "source has no content location"))
            continue
        if not lic.get("redistributable"):
            # Doctrine: an unresolved or restrictive license stays index-only.
            skipped.append((entry["ref"], f"license {lic.get('spdx')} is not redistributable"))
            continue
        if args.only and entry["source_slug"] != args.only:
            continue
        try:
            text = convert(entry, source, lic)
        except Exception as exc:
            failed.append((entry["ref"], str(exc)))
            continue
        out = OUT_ROOT / source["namespace"] / f"{entry['ref'].split('/')[-1]}.md"
        if not args.dry_run:
            out.parent.mkdir(parents=True, exist_ok=True)
            if not out.exists() or out.read_text(encoding="utf-8") != text:
                out.write_text(text, encoding="utf-8")
        made.append(out.relative_to(REPO_ROOT).as_posix())
        if args.limit and len(made) >= args.limit:
            break

    print(f"[convert-skills] converted {len(made)}, skipped {len(skipped)}, failed {len(failed)}")
    for ref, why in skipped[:3]:
        print(f"  skipped {ref}: {why}", file=sys.stderr)
    for ref, why in failed[:5]:
        print(f"  FAILED {ref}: {why}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
