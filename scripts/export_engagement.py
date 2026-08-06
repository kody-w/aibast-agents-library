#!/usr/bin/env python3
"""Export engagement — which solutions people actually take into a room.

Every deck this site can produce — the one-pager, the reference architecture,
the configuration guide — leaves through one function in deck.js, and that
function records that it happened. This is the other half: the thread the
record lands in, and the snapshot a workflow can rank.

WHY EXPORTS AND NOT VIEWS. A view means someone landed, and page views are the
metric everyone already has and nobody trusts. Taking the deck away is a
deliberate act with a cost — it means this solution is going in front of a
customer. Of everything a static site can observe, it is the closest thing to
intent, and until now it left no trace at all.

THE MECHANISM is the one the download tally and the play tally already use,
for the same reason: a static page has nowhere to POST a number to. So an
export is a THUMBS_UP on a pinned tally comment — one per GitHub account. The
count therefore means "people who marked that they exported this", never
"downloads", and every surface that shows it says so in words. It is a smaller
number than the true one and a truer one, and it cannot be inflated by
refreshing.

A solution gets its OWN thread, titled "[solution] <name>", exactly as a demo
recording gets "[demo] <name>". A solution and the agent behind it are not the
same subject and must never share a tally — only 9 of 48 solutions even map
onto a registry agent, so folding them together would silently attribute one
thing's popularity to another.

Output: state/export_engagement.json, published by build_api.py and read by
export-signal.js in the browser.

Subcommands:
  seed    create missing solution Discussions (idempotent, capped)
  tally   ensure the export-tally comment exists (idempotent, capped)
  fetch   snapshot exports/comments into state/export_engagement.json

Usage:
    python3 scripts/export_engagement.py fetch
    GITHUB_TOKEN=... python3 scripts/export_engagement.py seed --limit 10
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from discussion_ratings import (  # noqa: E402
        EXPORT_BODY, EXPORT_MARKER, graphql, fetch_all_discussions,
        marker_comment_of, positive_score, warn,
    )
except ImportError as exc:  # pragma: no cover
    print(f"[export] cannot reuse discussion_ratings: {exc}", file=sys.stderr)
    raise SystemExit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = REPO_ROOT / "state" / "export_engagement.json"
ONEPAGERS = REPO_ROOT / "data" / "onepagers.json"
GUIDES = REPO_ROOT / "data" / "config_guides"

REPO = os.environ.get("AIBAST_RATINGS_REPO", "microsoft/aibast-agents-library")
CATEGORY = os.environ.get("AIBAST_RATINGS_CATEGORY", "Announcements")
SCHEMA = "aibast-export-engagement/1.0"

# Distinct from "[demo] " so a solution thread can never collide with the demo
# thread of the same name, and so is_agent_title keeps ignoring both.
TITLE_PREFIX = "[solution] "

TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""


def subjects() -> dict[str, dict]:
    """Everything a deck can be exported for, keyed by slug."""
    out: dict[str, dict] = {}
    doc = json.loads(ONEPAGERS.read_text(encoding="utf-8"))
    guided = {p.stem for p in GUIDES.glob("*.json")} if GUIDES.is_dir() else set()
    for e in doc.get("onepagers", []):
        slug = e.get("slug")
        if not slug:
            continue
        out[slug] = {
            "slug": slug,
            "title": e.get("display_name") or slug,
            "industries": e.get("industries") or ([e["industry"]] if e.get("industry") else []),
            # Which decks exist for this solution. A solution with a guide has
            # more to export, and the report says so rather than comparing a
            # three-deck solution against a one-deck one as though they were
            # the same opportunity.
            "decks": ["one-pager", "architecture"] + (["config-guide"] if slug in guided else []),
        }
    # The roadmap is exportable too and is nobody's solution. It gets a subject
    # so its exports are counted somewhere rather than dropped on the floor.
    out["roadmap"] = {"slug": "roadmap", "title": "AIBAST Roadmap",
                      "industries": [], "decks": ["roadmap"]}
    return out


def title_for(subject: dict) -> str:
    return f"{TITLE_PREFIX}{subject['title']}"


def export_count(node: dict) -> int:
    """THUMBS_UP reactors on the export tally — one per person."""
    c = marker_comment_of(node, EXPORT_MARKER)
    if not c:
        return 0
    for g in c.get("reactionGroups") or []:
        if g.get("content") == "THUMBS_UP":
            return (g.get("reactors") or {}).get("totalCount", 0)
    return 0


def build_snapshot(nodes: list[dict], subs: dict[str, dict]) -> dict:
    by_title = {n.get("title", ""): n for n in nodes}
    exports: dict[str, dict] = {}
    for slug, s in sorted(subs.items()):
        node = by_title.get(title_for(s))
        if not node:
            # An unseeded subject is reported as a real zero with thread:false,
            # so a page can say "no thread yet" instead of "0 exports" — those
            # are different facts and conflating them makes a new solution look
            # unpopular rather than unlaunched.
            exports[slug] = {"exports": 0, "likes": 0, "comments": 0,
                             "thread": False, "url": None, "number": None,
                             "decks": s["decks"]}
            continue
        tally = marker_comment_of(node, EXPORT_MARKER)
        n_comments = (node.get("comments") or {}).get("totalCount", 0)
        exports[slug] = {
            "exports": export_count(node),
            "likes": positive_score(node.get("reactionGroups")),
            # The tally comment is machinery, not conversation.
            "comments": max(0, n_comments - (1 if tally else 0)),
            "thread": True,
            "url": node.get("url"),
            "export_url": (tally or {}).get("url") or node.get("url"),
            "number": node.get("number"),
            "decks": s["decks"],
        }
    total = sum(v["exports"] for v in exports.values())
    return {
        "schema": SCHEMA,
        "repo": REPO,
        "category": CATEGORY,
        "note": ("An export is a THUMBS_UP on the pinned export-tally comment of a "
                 "solution's Discussion — one per GitHub account. It counts people "
                 "who marked that they took a deck away, not downloads. Nothing is "
                 "written from the browser."),
        "totals": {"subjects": len(exports), "exports": total,
                   "threads": sum(1 for v in exports.values() if v["thread"])},
        "exports": exports,
    }


def persist(doc: dict) -> bool:
    prev = None
    if OUT.is_file():
        try:
            prev = json.loads(OUT.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            prev = None
    # A failed fetch must never erase real counts.
    if prev and prev.get("totals", {}).get("exports", 0) and not doc["totals"]["exports"]:
        warn("fetch returned no exports but the snapshot has some; keeping it.")
        return False
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return True


def cmd_fetch() -> int:
    subs = subjects()
    nodes: list[dict] = []
    if TOKEN:
        try:
            owner, name = REPO.split("/", 1)
            nodes = fetch_all_discussions(owner, name)
        except Exception as exc:                               # noqa: BLE001
            warn(f"fetch failed ({exc}); the snapshot is unchanged.")
            return 0
    else:
        warn("no GITHUB_TOKEN set; writing a shape-only snapshot.")
    doc = build_snapshot(nodes, subs)
    persist(doc)
    t = doc["totals"]
    print(f"[export] {t['subjects']} subject(s), {t['threads']} thread(s), "
          f"{t['exports']} export(s)")
    return 0


def seed_body(s: dict) -> str:
    inds = ", ".join(s.get("industries") or []) or "Cross-industry"
    decks = ", ".join(s.get("decks") or [])
    return (
        f"**{s['title']}** ({inds}).\n\n"
        "This thread is where this solution's engagement lives: react on this "
        "post if it is useful, reply if you have used it, and use the export "
        "tally below when you take a deck away.\n\n"
        f"Decks available: {decks}.\n\n"
        "Nothing here is written by a page — every number comes from a "
        "reaction a signed-in person left."
    )


def _mutate(query: str, variables: dict) -> dict:
    return graphql(query, variables)


CREATE = """
mutation ($repositoryId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
  createDiscussion(input: {repositoryId: $repositoryId, categoryId: $categoryId,
                           title: $title, body: $body}) {
    discussion { id number url }
  }
}
"""

ADD_COMMENT = """
mutation ($discussionId: ID!, $body: String!) {
  addDiscussionComment(input: {discussionId: $discussionId, body: $body}) {
    comment { id url }
  }
}
"""

REPO_QUERY = """
query ($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    id
    discussionCategories(first: 25) { nodes { id name } }
  }
}
"""


def _repo_and_category() -> tuple[str, str]:
    owner, name = REPO.split("/", 1)
    data = graphql(REPO_QUERY, {"owner": owner, "name": name})
    repo = (data.get("repository") or {})
    cats = ((repo.get("discussionCategories") or {}).get("nodes") or [])
    cat = next((c["id"] for c in cats if c.get("name") == CATEGORY), None)
    if not repo.get("id") or not cat:
        raise RuntimeError(f"repository or category '{CATEGORY}' not found")
    return repo["id"], cat


def cmd_seed(limit: int, delay: float) -> int:
    if not TOKEN:
        warn("no GITHUB_TOKEN set; nothing seeded.")
        return 0
    subs = subjects()
    owner, name = REPO.split("/", 1)
    try:
        nodes = fetch_all_discussions(owner, name)
        repo_id, cat_id = _repo_and_category()
    except Exception as exc:                                   # noqa: BLE001
        warn(f"seed preflight failed ({exc}); nothing created.")
        return 0
    have = {n.get("title", "") for n in nodes}
    todo = [s for s in subs.values() if title_for(s) not in have][:limit]
    made = 0
    for s in todo:
        try:
            r = _mutate(CREATE, {"repositoryId": repo_id, "categoryId": cat_id,
                                 "title": title_for(s), "body": seed_body(s)})
            d = ((r.get("createDiscussion") or {}).get("discussion") or {})
            if d.get("id"):
                # A thread without its tally is a thread that cannot be
                # counted, so it is provisioned in the same breath.
                _mutate(ADD_COMMENT, {"discussionId": d["id"], "body": EXPORT_BODY})
                made += 1
                print(f"    {title_for(s)}  #{d.get('number')}")
        except Exception as exc:                               # noqa: BLE001
            warn(f"seed failed for {s['slug']} ({exc})")
        time.sleep(delay)
    print(f"[export] {made} thread(s) created, {len(subs) - len(have & set(map(title_for, subs.values())))} remaining")
    return 0


def cmd_tally(limit: int, delay: float) -> int:
    """Add the export tally to solution threads that predate it."""
    if not TOKEN:
        warn("no GITHUB_TOKEN set; nothing added.")
        return 0
    subs = subjects()
    owner, name = REPO.split("/", 1)
    try:
        nodes = fetch_all_discussions(owner, name)
    except Exception as exc:                                   # noqa: BLE001
        warn(f"tally preflight failed ({exc}); nothing added.")
        return 0
    wanted = {title_for(s) for s in subs.values()}
    added = 0
    for node in nodes:
        if node.get("title") not in wanted or added >= limit:
            continue
        if marker_comment_of(node, EXPORT_MARKER) is not None:
            continue
        try:
            _mutate(ADD_COMMENT, {"discussionId": node["id"], "body": EXPORT_BODY})
            added += 1
            print(f"    {node.get('title')}  #{node.get('number')}")
        except Exception as exc:                               # noqa: BLE001
            warn(f"tally failed for #{node.get('number')} ({exc})")
        time.sleep(delay)
    print(f"[export] {added} tally comment(s) added")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)
    seed = sub.add_parser("seed", help="create missing solution Discussions")
    seed.add_argument("--limit", type=int, default=20)
    seed.add_argument("--delay", type=float, default=1.2)
    tally = sub.add_parser("tally", help="ensure export-tally comments exist")
    tally.add_argument("--limit", type=int, default=40)
    tally.add_argument("--delay", type=float, default=1.2)
    sub.add_parser("fetch", help="snapshot exports to state/")
    args = ap.parse_args()
    if args.command == "seed":
        return cmd_seed(args.limit, args.delay)
    if args.command == "tally":
        return cmd_tally(args.limit, args.delay)
    return cmd_fetch()


if __name__ == "__main__":
    sys.exit(main())
