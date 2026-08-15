#!/usr/bin/env python3
"""Idempotently reconcile the AIBAST catalog's rating discussions.

There is one canonical GitHub Discussion per agent. Its title is the complete
publisher-qualified catalog name (for example
@aibast-agents-library/account-intelligence) in the configured announcement
category. Existing canonical or legacy slug-only threads are reused, missing
canonical threads are created, and rar/discussions.json remains {slug: url} for
the workshop and Brainstem.

Usage: GITHUB_TOKEN=<maintainer token> python3 tools/create_discussions.py
"""
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "rar" / "ratings-config.json").read_text())
PAGE_QUERY = """
query($owner:String!,$repo:String!,$after:String){
  repository(owner:$owner,name:$repo){
    id
    discussionCategories(first:25){nodes{id name}}
    discussions(first:100,after:$after){
      pageInfo{hasNextPage endCursor}
      nodes{title url category{name}}
    }
  }
}
"""


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


def canonical_title(slug):
    return CFG["title_format"].format(slug=slug)


def main(*, map_only=False):
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("GITHUB_TOKEN required (maintainer, discussions: write)")
        return 1
    owner, repo = CFG["repo"].split("/")
    after = None
    discussions = []
    repository = None
    while True:
        data = gql(
            token,
            PAGE_QUERY,
            {"owner": owner, "repo": repo, "after": after},
        )
        repository = data["repository"]
        page = repository["discussions"]
        discussions.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            break
        after = page["pageInfo"]["endCursor"]

    repo_id = repository["id"]
    cats = {
        category["name"]: category["id"]
        for category in repository["discussionCategories"]["nodes"]
    }
    cat_id = cats.get(CFG["category"])
    if not cat_id:
        print(f"Category '{CFG['category']}' not found — enable Discussions and create it first. Have: {list(cats)}")
        return 1
    existing = {
        node["title"]: node["url"]
        for node in discussions
        if (node.get("category") or {}).get("name") == CFG["category"]
    }
    agents = json.loads((ROOT / "rar" / "registry.json").read_text())["agents"]
    urls, created, missing = {}, 0, []
    for a in agents:
        slug = a["name"].split("/")[1]
        disp = a.get("display_name", slug)
        title = canonical_title(slug)
        existing_url = existing.get(title) or existing.get(slug)
        if existing_url:
            urls[slug] = existing_url
            continue
        if map_only:
            missing.append(title)
            continue
        body = (f"Community rating thread for **{disp}** in the AIBAST Agent Library.\n\n"
                f"React with a positive emoji (thumbs-up, heart, hooray, rocket) to recommend this "
                f"agent — counts refresh into the library daily. Comments and field reports welcome.")
        out = gql(token, """
          mutation($repoId:ID!,$catId:ID!,$title:String!,$body:String!){
            createDiscussion(input:{repositoryId:$repoId,categoryId:$catId,
              title:$title,body:$body}){discussion{url}}}""",
            {
                "repoId": repo_id,
                "catId": cat_id,
                "title": title,
                "body": body,
            })
        urls[slug] = out["createDiscussion"]["discussion"]["url"]
        created += 1
    (ROOT / "rar" / "discussions.json").write_text(
        json.dumps(dict(sorted(urls.items())), indent=1) + "\n")
    print(f"[discussions] {created} created, {len(urls)} total mapped -> rar/discussions.json")
    if missing:
        print(f"[discussions] {len(missing)} canonical threads still need creation")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--map-only",
        action="store_true",
        help="Map existing canonical discussions without creating missing threads.",
    )
    args = parser.parse_args()
    sys.exit(main(map_only=args.map_only))
