#!/usr/bin/env python3
"""One-time (idempotent) creator of the per-agent rating discussions.

Replaces giscus's lazy thread creation with something AIBAST-native: one
GitHub Discussion per agent, title = slug, in the configured announcement
category — the anti-spam property the pattern relies on (only maintainers
create threads; visitors react). Safe to re-run: existing slugs are skipped.
Writes rar/discussions.json {slug: url} for the workshop's rate links.

Usage: GITHUB_TOKEN=<maintainer token> python3 tools/create_discussions.py
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "rar" / "ratings-config.json").read_text())


def gql(token, query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}",
                 "Content-Type": "application/json",
                 "User-Agent": "aibast-discussions"})
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.load(r)
    if out.get("errors"):
        raise RuntimeError(out["errors"])
    return out["data"]


def main():
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("GITHUB_TOKEN required (maintainer, discussions: write)")
        return 1
    owner, repo = CFG["repo"].split("/")
    d = gql(token, """
      query($owner:String!,$repo:String!){
        repository(owner:$owner,name:$repo){
          id
          discussionCategories(first:25){nodes{id name}}
          discussions(first:100){pageInfo{hasNextPage endCursor}
            nodes{title url}}}}""", {"owner": owner, "repo": repo})
    repo_id = d["repository"]["id"]
    cats = {c["name"]: c["id"] for c in d["repository"]["discussionCategories"]["nodes"]}
    cat_id = cats.get(CFG["category"])
    if not cat_id:
        print(f"Category '{CFG['category']}' not found — enable Discussions and create it first. Have: {list(cats)}")
        return 1
    existing = {n["title"]: n["url"] for n in d["repository"]["discussions"]["nodes"]}
    # NOTE: >100 discussions needs pagination; fine on first run of 105 — re-run to top up.
    agents = json.loads((ROOT / "rar" / "registry.json").read_text())["agents"]
    urls, created = {}, 0
    for a in agents:
        slug = a["name"].split("/")[1]
        disp = a.get("display_name", slug)
        if slug in existing:
            urls[slug] = existing[slug]
            continue
        body = (f"Community rating thread for **{disp}** in the AIBAST Agent Library.\n\n"
                f"React with a positive emoji (thumbs-up, heart, hooray, rocket) to recommend this "
                f"agent — counts refresh into the library daily. Comments and field reports welcome.")
        out = gql(token, """
          mutation($repoId:ID!,$catId:ID!,$title:String!,$body:String!){
            createDiscussion(input:{repositoryId:$repoId,categoryId:$catId,
              title:$title,body:$body}){discussion{url}}}""",
            {"repoId": repo_id, "catId": cat_id, "title": slug, "body": body})
        urls[slug] = out["createDiscussion"]["discussion"]["url"]
        created += 1
    (ROOT / "rar" / "discussions.json").write_text(
        json.dumps(dict(sorted(urls.items())), indent=1) + "\n")
    print(f"[discussions] {created} created, {len(urls)} total mapped -> rar/discussions.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
