#!/usr/bin/env python3
"""Daily GitHub-native community snapshot into rar/community.json:
adoption (stars/forks/watchers over time), conversations per agent
(discussion comment counts), and in-the-wild mentions (code search for the
library namespace in other public repos). Non-fatal; append-only history."""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    from .fetch_ratings import catalog_discussion
except ImportError:
    from fetch_ratings import catalog_discussion

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "rar" / "community.json"
CFG = json.loads((ROOT / "rar" / "ratings-config.json").read_text())


def api(url, token, accept="application/vnd.github+json"):
    req = urllib.request.Request(url, headers={
        "Authorization": f"bearer {token}", "User-Agent": "aibast-community",
        "Accept": accept})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("[community] no GITHUB_TOKEN — skipping")
        return 0
    today = datetime.now(timezone.utc).date().isoformat()
    hist = json.loads(OUT.read_text()) if OUT.exists() else {
        "_note": ("Daily GitHub-native community snapshot: adoption trendline, "
                  "conversations per agent, and public in-the-wild mentions of the "
                  "library namespace outside this repo."),
        "adoption": {}, "conversations": {}, "in_the_wild": {}}
    try:
        repo = api(f"https://api.github.com/repos/{CFG['repo']}", token)
        hist["adoption"][today] = {
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "watchers": repo.get("subscribers_count", 0),
        }
    except Exception as e:  # noqa: BLE001
        print(f"[community] repo snapshot failed: {e}")
    try:
        q = urllib.parse.quote(f'"@aibast-agents-library/" -repo:{CFG["repo"]}')
        hits = api(f"https://api.github.com/search/code?q={q}&per_page=1", token,
                   accept="application/vnd.github.text-match+json")
        hist["in_the_wild"][today] = {"code_mentions_outside_repo": hits.get("total_count", 0)}
    except Exception as e:  # noqa: BLE001
        print(f"[community] code search skipped: {e}")
    try:
        owner, name = CFG["repo"].split("/")
        canonical_convo, legacy_convo, after = {}, {}, None
        while True:
            body = json.dumps({"query": """
              query($o:String!,$r:String!,$a:String){
                repository(owner:$o,name:$r){discussions(first:100,after:$a){
                  pageInfo{hasNextPage endCursor}
                  nodes{title category{name} comments{totalCount}}}}}""",
              "variables": {"o": owner, "r": name, "a": after}}).encode()
            req = urllib.request.Request("https://api.github.com/graphql", data=body,
                headers={"Authorization": f"bearer {token}",
                         "Content-Type": "application/json",
                         "User-Agent": "aibast-community"})
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.load(r)["data"]["repository"]["discussions"]
            for n in d["nodes"]:
                if (n.get("category") or {}).get("name") != CFG["category"]:
                    continue
                total = n["comments"]["totalCount"]
                if not total:
                    continue
                slug, is_canonical = catalog_discussion(n["title"])
                if not slug:
                    continue
                destination = canonical_convo if is_canonical else legacy_convo
                destination[slug] = total
            if not d["pageInfo"]["hasNextPage"]:
                break
            after = d["pageInfo"]["endCursor"]
        convo = dict(legacy_convo)
        convo.update(canonical_convo)
        if convo or not hist["conversations"]:
            hist["conversations"] = dict(sorted(convo.items()))
    except Exception as e:  # noqa: BLE001
        print(f"[community] conversations skipped: {e}")
    hist["adoption"] = dict(sorted(hist["adoption"].items()))
    OUT.write_text(json.dumps(hist, indent=1) + "\n")
    print(f"[community] adoption days: {len(hist['adoption'])} | "
          f"agents with conversations: {len(hist['conversations'])} | "
          f"in-the-wild rows: {len(hist['in_the_wild'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
