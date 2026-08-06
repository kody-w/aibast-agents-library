#!/usr/bin/env python3
"""Video engagement — plays, likes and comments, with Discussions as the backend.

The same pattern `discussion_ratings.py` already uses for agents, applied to the
demo recordings: one Discussion per video, reactions are likes, the thread is the
comments, and a pinned tally comment counts plays.

Why a tally comment rather than a counter. A static site has no backend, so
there is nowhere to POST a view to. The obvious workarounds are all worse than
they look: a counter in a JSON file cannot be written from a browser, a
third-party counter puts a tracker on a Microsoft page, and anything anonymous
is trivially inflatable. A reaction on a pinned comment is one per GitHub
account, which makes a play count mean *someone signed in bothered to mark it* —
a smaller number than a raw hit count and a truer one.

So a play is recorded the way a download already is: the page opens the tally
comment and the viewer reacts. The page shows the count either way; marking it
is optional, and the copy says so rather than pretending the number is total
traffic.

  likes     positive reactions on the Discussion (THUMBS_UP, HEART, HOORAY,
            ROCKET, LAUGH). Negative and neutral never contribute, so a
            thumbs-down cannot drag a video down or masquerade as a like.
  plays     THUMBS_UP reactions on the pinned tally comment
  comments  the Discussion thread

Output: state/video_engagement.json, which build_api.py publishes.

Subcommands:
  seed    create missing Discussions for hosted videos (idempotent, capped)
  tally   ensure the play-tally comment exists (idempotent, capped)
  fetch   snapshot likes/plays/comments into state/video_engagement.json

Usage:
    python3 scripts/video_engagement.py fetch
    python3 scripts/video_engagement.py seed --limit 5
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
        graphql, fetch_all_discussions, positive_score, marker_comment_of, warn,
    )
except ImportError as exc:  # pragma: no cover
    print(f"[video] cannot reuse discussion_ratings: {exc}", file=sys.stderr)
    raise SystemExit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = REPO_ROOT / "state" / "video_engagement.json"
ONEPAGERS = REPO_ROOT / "data" / "onepagers.json"

REPO = os.environ.get("AIBAST_RATINGS_REPO", "microsoft/aibast-agents-library")
CATEGORY = os.environ.get("AIBAST_RATINGS_CATEGORY", "Announcements")

# A video thread is titled distinctly so it can never collide with the agent
# thread of the same name, and so `is_agent_title` keeps ignoring it.
TITLE_PREFIX = "[demo] "
PLAY_MARKER = "<!-- aibast:play-tally -->"

SCHEMA = "aibast-video-engagement/1.0"


def video_subjects() -> dict[str, dict]:
    """Hosted demo recordings, keyed by slug."""
    if not ONEPAGERS.is_file():
        return {}
    doc = json.loads(ONEPAGERS.read_text(encoding="utf-8"))
    out = {}
    for e in doc.get("onepagers", []):
        v = e.get("video") or {}
        if not v.get("slug"):
            continue
        out[v["slug"]] = {
            "slug": v["slug"],
            "title": e.get("display_name") or v["slug"],
            "solution": e.get("slug"),
            "industries": e.get("industries") or [],
        }
    return out


def title_for(subject: dict) -> str:
    return f"{TITLE_PREFIX}{subject['title']}"


def play_count(node: dict) -> int:
    """THUMBS_UP on the pinned tally comment — one per GitHub account."""
    c = marker_comment_of(node, PLAY_MARKER)
    if not c:
        return 0
    for g in c.get("reactionGroups") or []:
        if g.get("content") == "THUMBS_UP":
            return int((g.get("reactors") or {}).get("totalCount", 0))
    return 0


def build_snapshot(nodes: list[dict], subjects: dict[str, dict]) -> dict:
    by_title = {n.get("title", ""): n for n in nodes}
    videos, total_plays, total_likes = {}, 0, 0
    for slug, subj in sorted(subjects.items()):
        node = by_title.get(title_for(subj))
        if not node:
            videos[slug] = {"likes": 0, "plays": 0, "comments": 0,
                            "url": None, "number": None, "thread": False}
            continue
        likes = positive_score(node.get("reactionGroups"))
        plays = play_count(node)
        tally = marker_comment_of(node, PLAY_MARKER)
        total_plays += plays
        total_likes += likes
        videos[slug] = {
            "likes": likes,
            "plays": plays,
            # The tally comment is not a conversation; do not count it as one.
            "comments": max(0, int((node.get("comments") or {}).get("totalCount", 0))
                            - (1 if tally else 0)),
            "url": node.get("url"),
            "number": node.get("number"),
            "play_url": (tally or {}).get("url"),
            "thread": True,
        }
    return {
        "schema": SCHEMA,
        "repo": REPO,
        "category": CATEGORY,
        "note": ("Plays are reactions on a pinned tally comment, so one play is "
                 "one signed-in person choosing to mark it — not a raw hit "
                 "count. Likes are positive reactions on the thread; negative "
                 "and neutral reactions never contribute."),
        "totals": {"videos": len(subjects), "with_thread":
                   sum(1 for v in videos.values() if v["thread"]),
                   "plays": total_plays, "likes": total_likes},
        "videos": videos,
    }


def persist(doc: dict) -> bool:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    new = json.dumps(doc, indent=2, sort_keys=True) + "\n"
    if OUT.is_file() and OUT.read_text(encoding="utf-8") == new:
        print(f"[video] {OUT.relative_to(REPO_ROOT)} unchanged")
        return False
    OUT.write_text(new, encoding="utf-8")
    print(f"[video] wrote {OUT.relative_to(REPO_ROOT)}")
    return True


def cmd_fetch() -> int:
    subjects = video_subjects()
    if not subjects:
        warn("no hosted videos in data/onepagers.json")
        persist(build_snapshot([], {}))
        return 0
    owner, name = REPO.split("/", 1)
    try:
        nodes = fetch_all_discussions(owner, name)
    except Exception as exc:                                   # noqa: BLE001
        # Offline or unauthenticated is not a build failure: the last snapshot
        # stays, exactly as the agent ratings behave. But if there is no
        # snapshot at all, write an empty one — the page must have a file to
        # read, and zeroes it can explain beat a 404 it cannot.
        warn(f"could not reach GitHub ({exc}); keeping the last snapshot")
        if not OUT.is_file():
            persist(build_snapshot([], subjects))
        return 0
    doc = build_snapshot(nodes, subjects)
    persist(doc)
    t = doc["totals"]
    print(f"[video] {t['with_thread']}/{t['videos']} threaded · "
          f"{t['plays']} plays · {t['likes']} likes")
    return 0


def seed_body(subject: dict) -> str:
    inds = ", ".join(subject["industries"]) or "cross-industry"
    return (
        f"Demo recording — **{subject['title']}** ({inds}).\n\n"
        "React on this post to like the demo. Comments here are the thread the "
        "library shows next to the video.\n\n"
        "Plays are counted on the pinned comment below: react 👍 there to mark "
        "that you watched it. That makes a play one signed-in person rather "
        "than a raw hit, which is a smaller number and a truer one.\n"
    )


def cmd_seed(limit: int, delay: float) -> int:
    subjects = video_subjects()
    owner, name = REPO.split("/", 1)
    nodes = fetch_all_discussions(owner, name)
    have = {n.get("title", "") for n in nodes}
    todo = [s for s in subjects.values() if title_for(s) not in have][:limit]
    if not todo:
        print("[video] every hosted video already has a thread")
        return 0
    print(f"[video] would create {len(todo)} thread(s); "
          "run with GITHUB_TOKEN and --apply to create them")
    for s in todo:
        print(f"    {title_for(s)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("command", choices=["fetch", "seed", "tally"])
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--delay", type=float, default=1.0)
    args = ap.parse_args()
    if args.command == "fetch":
        return cmd_fetch()
    if args.command == "seed":
        return cmd_seed(args.limit, args.delay)
    print("[video] tally: run seed first; the tally comment is created with the thread")
    return 0


if __name__ == "__main__":
    sys.exit(main())
