#!/usr/bin/env python3
"""AIBAST RAR ratings fetcher — the GitHub-native half of the approved
cat-agent-skills metrics pattern, ported faithfully.

One canonical GitHub Discussion per agent, whose title is its complete
publisher-qualified AIBAST catalog name. Legacy slug-only threads remain
readable during migration. This script harvests positive reactions into
rar/ratings.json. Deliberate properties copied from the pattern:
- Only positive reactions count; a downvote can never reduce a score.
- Discussions outside the configured category, or with non-slug titles,
  are ignored.
- NON-FATAL by design: any failure leaves the previous snapshot in place
  and prints a warning — never a failed build, never an empty clobber.
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "rar" / "ratings.json"
CFG = json.loads((ROOT / "rar" / "ratings-config.json").read_text())
SLUG_RE = re.compile(r"(?!-)(?!.*--)[a-z0-9-]{1,64}(?<!-)")
POSITIVE = set(CFG["positive_reactions"])
CATALOG = json.loads((ROOT / "rar" / "registry.json").read_text())
CATALOG_NAMES = {
    agent["name"]: agent["name"].split("/", maxsplit=1)[1]
    for agent in CATALOG["agents"]
}
CATALOG_SLUGS = set(CATALOG_NAMES.values())
QUERY = """
query($owner:String!,$repo:String!,$after:String){
  repository(owner:$owner,name:$repo){
    discussions(first:100,after:$after){
      pageInfo{hasNextPage endCursor}
      nodes{title category{name}
        reactionGroups{content reactors{totalCount}}}}}}
"""


def catalog_discussion(title):
    if title in CATALOG_NAMES:
        return CATALOG_NAMES[title], True
    if title in CATALOG_SLUGS and SLUG_RE.fullmatch(title):
        return title, False
    return None, False


def main():
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("[ratings] no GITHUB_TOKEN — leaving snapshot unchanged")
        return 0
    owner, repo = CFG["repo"].split("/")
    canonical_ratings, legacy_ratings, after = {}, {}, None
    try:
        while True:
            body = json.dumps({"query": QUERY, "variables": {
                "owner": owner, "repo": repo, "after": after}}).encode()
            req = urllib.request.Request(
                "https://api.github.com/graphql", data=body,
                headers={"Authorization": f"bearer {token}",
                         "Content-Type": "application/json",
                         "User-Agent": "aibast-ratings"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
            disc = data["data"]["repository"]["discussions"]
            for node in disc["nodes"]:
                title = (node.get("title") or "").strip()
                if (node.get("category") or {}).get("name") != CFG["category"]:
                    continue
                slug, is_canonical = catalog_discussion(title)
                if is_canonical:
                    destination = canonical_ratings
                elif slug:
                    destination = legacy_ratings
                else:
                    continue
                score = sum(g["reactors"]["totalCount"]
                            for g in node.get("reactionGroups", [])
                            if g["content"] in POSITIVE)
                if score > 0:
                    destination[slug] = score
            if not disc["pageInfo"]["hasNextPage"]:
                break
            after = disc["pageInfo"]["endCursor"]
    except Exception as e:  # noqa: BLE001 — non-fatal by design
        print(f"[ratings] fetch failed, snapshot unchanged: {e}")
        return 0
    ratings = dict(legacy_ratings)
    ratings.update(canonical_ratings)
    previous = json.loads(OUT.read_text()) if OUT.exists() else {}
    if not ratings and previous:
        print("[ratings] refusing to clobber a non-empty snapshot with an empty one")
        return 0
    OUT.write_text(json.dumps(dict(sorted(ratings.items())), indent=1) + "\n")
    print(f"[ratings] snapshot written: {len(ratings)} rated agents")
    return 0


if __name__ == "__main__":
    sys.exit(main())
