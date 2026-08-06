#!/usr/bin/env python3
"""Crawl the Microsoft Learn pages behind each first-party agent.

The library's standard for an aggregated entry is that it carries real content
and real provenance, not a name and a hyperlink. A row that says only "Sales
Qualification Agent — Overview | Configure" makes the reader leave to find out
anything, which is the behaviour aggregating was meant to remove.

So each first-party agent gets what every other entry gets: a summary, the
shape of what the documentation covers, its prerequisites where the page states
them, and a record of when it was read.

Two rules this obeys, because the content is Microsoft's and not ours:

  * SUMMARISE AND LINK, never mirror. What is stored is the page's own meta
    description, its section headings, and short prerequisite lines — enough to
    decide whether an agent fits a scenario. The Learn page stays the
    authoritative text and is linked from every field derived from it.
  * RECORD WHEN IT WAS READ. These products change; a crawled summary is true
    on a date and the page says so, rather than implying it is current forever.

A fetch failure is recorded and the previous content kept. A first-party agent
that cannot be reached is reported, never silently emptied.

Output: data/first_party_agents.json (enriched in place)

Usage:
    python3 scripts/crawl_first_party.py
    python3 scripts/crawl_first_party.py --only sales-research
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA = REPO_ROOT / "data" / "first_party_agents.json"
UA = "aibast-agents-library/1.0 (+https://github.com/microsoft/aibast-agents-library)"
TIMEOUT = 30


def fetch(url: str) -> tuple[str | None, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.read().decode("utf-8", "replace"), "ok"
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except Exception as e:                                     # noqa: BLE001
        return None, str(e)[:80]


def strip(t: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))).strip()


def meta(doc: str, name: str) -> str:
    m = re.search(rf'<meta name="{name}" content="([^"]*)"', doc)
    return html.unescape(m.group(1)).strip() if m else ""


def sections(doc: str) -> list[str]:
    """The page's own h2s, minus Learn's furniture."""
    skip = {"in this article", "related information", "next steps", "feedback",
            "see also", "additional resources"}
    out = []
    for h in re.findall(r"<h2[^>]*>(.*?)</h2>", doc, re.S):
        t = strip(h)
        if t and t.lower() not in skip and len(t) < 90 and t not in out:
            out.append(t)
    return out[:8]


def prerequisites(doc: str) -> list[str]:
    """Bullets under a Prerequisites heading, when the page has one."""
    m = re.search(r"<h[23][^>]*>\s*Prerequisites?\s*</h[23]>(.*?)<h[23]", doc, re.S | re.I)
    if not m:
        return []
    out = []
    for li in re.findall(r"<li[^>]*>(.*?)</li>", m.group(1), re.S)[:6]:
        t = strip(li)
        if 8 < len(t) < 220:
            out.append(t)
    return out


def crawl(url: str) -> dict:
    doc, status = fetch(url)
    rec = {"url": url, "status": status,
           "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
    if not doc:
        return rec
    rec["title"] = strip(re.search(r"<title>(.*?)</title>", doc, re.S).group(1)
                         ).replace(" | Microsoft Learn", "") if "<title>" in doc else ""
    rec["summary"] = meta(doc, "description")
    rec["sections"] = sections(doc)
    pre = prerequisites(doc)
    if pre:
        rec["prerequisites"] = pre
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", help="substring of an agent ref")
    args = ap.parse_args()

    doc = json.loads(DATA.read_text(encoding="utf-8"))
    agents = doc.get("agents", [])
    if args.only:
        agents = [a for a in agents if args.only.lower() in a["ref"].lower()]

    ok, failed = 0, []
    for a in agents:
        name = a["display_name"]
        content = a.setdefault("content", {})
        for key, url_key in (("overview", "overview_url"), ("configure", "configure_url")):
            url = a.get(url_key)
            if not url:
                continue
            rec = crawl(url)
            if rec["status"] != "ok":
                failed.append(f"{name} {key}: {rec['status']}")
                # Keep whatever was read last time rather than blanking it.
                if key in content:
                    content[key]["last_error"] = rec["status"]
                    continue
            content[key] = rec
            ok += 1
        sm = (content.get("overview") or {}).get("summary")
        print(f"  {name[:34]:36} {'ok' if sm else 'no summary':12} "
              f"{len((content.get('configure') or {}).get('sections') or [])} configure sections")

    doc["crawled"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    doc["crawl_note"] = ("Summaries, section lists and prerequisites are read from "
                         "the linked Microsoft Learn pages and are true as of the "
                         "date on each record. The linked page is authoritative; "
                         "nothing here is mirrored.")
    DATA.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[1p] {ok} page(s) read, {len(failed)} failed")
    for f in failed:
        print(f"    {f}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
