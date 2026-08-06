#!/usr/bin/env python3
"""vBrainstem usage — installs and runs recorded from the browser brainstem.

Same pattern as ``discussion_ratings.py`` (agents) and ``video_engagement.py``
(videos), applied to the public interactive demo at ``/vbrainstem/``: GitHub
Discussions is the backend, one thread per agent titled with its ``@scope/slug``,
and a pinned tally comment carrying an HTML-comment sentinel that clients react
:+1: on. One reaction is one GitHub account, so a count is *unique people* and
cannot be inflated. A build-time snapshot is what the page reads. There is no
server and there must not be one.

Two numbers, and what each one honestly means:

  installs  :+1: on ``<!-- aibast:download-tally -->`` — the tally
            ``discussion_ratings.py`` already owns. Loading an agent into the
            browser brainstem downloads the same ``agent.py`` the CLI installs,
            so it is the same event and belongs on the same tally rather than a
            parallel number that would double-count the catalog.
  runs      :+1: on ``<!-- aibast:vbrainstem-run-tally -->`` — this file's own
            tally, provisioned by ``tally`` below. It means: this many distinct
            GitHub accounts have actually executed this agent in the browser
            brainstem. It is NOT executions; a person who runs an agent fifty
            times is one.

What the number is not. A visitor who is not signed in cannot react — a browser
has no credential to react with, and giving it one would be worse than the gap.
So the demo page records the reaction only for a signed-in visitor and otherwise
offers a link to the tally comment. ``runs`` is therefore a floor: everyone it
counts really ran the agent, and some people who ran it are missing. That is the
trade the whole pattern makes, and the page says so next to the number.

Subcommands:
  tally   provision the run-tally comment on agent threads (idempotent, capped)
  fetch   snapshot installs/runs into state/vbrainstem_usage.json
  track   register one run (:+1: the run tally) — the CLI twin of what the
          browser does, useful for testing the loop end to end

Usage:
    GITHUB_TOKEN=... python3 scripts/vbrainstem_usage.py tally --limit 40
    GITHUB_TOKEN=... python3 scripts/vbrainstem_usage.py fetch

Config (env, with defaults):
  GITHUB_TOKEN / GH_TOKEN     read for fetch, write for tally/track
  AIBAST_RATINGS_REPO         owner/repo          (default: microsoft/aibast-agents-library)
  AIBAST_RATINGS_CATEGORY     discussion category (default: Announcements)

Non-fatal by design: a missing token, a network error or a missing category
warns and leaves the snapshot untouched — never a failed build.
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
        ADD_COMMENT_MUTATION,
        ADD_REACTION_MUTATION,
        TALLY_MARKER,
        graphql,
        is_agent_title,
        load_registry_agents,
        marker_comment_of,
    )
except ImportError as exc:  # pragma: no cover
    print(f"[vbrainstem] cannot reuse discussion_ratings: {exc}", file=sys.stderr)
    raise SystemExit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = REPO_ROOT / "state" / "vbrainstem_usage.json"

REPO = os.environ.get("AIBAST_RATINGS_REPO", "microsoft/aibast-agents-library")
CATEGORY = os.environ.get("AIBAST_RATINGS_CATEGORY", "Announcements")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""

SCHEMA = "aibast-vbrainstem-usage/1.0"


def warn(msg: str) -> None:
    """Own prefix: a warning from here must not read as one from the agent
    ratings job, or a failing run gets triaged against the wrong script."""
    print(f"[vbrainstem] {msg}", file=sys.stderr)


RUN_MARKER = "<!-- aibast:vbrainstem-run-tally -->"

RUN_BODY = (
    RUN_MARKER
    + "\n### ▷ Ran in the browser brainstem\n\n"
    "React :+1: **on this comment** when you have actually run this agent in the "
    "[browser brainstem](https://microsoft.github.io/aibast-agents-library/vbrainstem/). "
    "One reaction per GitHub account, so this counts *people who ran it*, not how "
    "many times it ran — and not how many people opened the page.\n\n"
    "Signed in, the demo page adds this reaction for you the first time an agent "
    "of yours does real work. Signed out it links you here instead, because a web "
    "page cannot react on your behalf and should not pretend otherwise.\n\n"
    "Installs are tallied on the download comment in this same thread; upvotes go "
    "on the top post."
)

# A query of our own rather than the shared one: this snapshot needs each
# comment's URL so the demo page can deep-link the exact tally to react on.
DISCUSSIONS_QUERY = """
query ($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    discussions(first: 100, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        number
        title
        url
        category { name }
        comments(first: 25) {
          nodes {
            id
            url
            body
            reactionGroups { content reactors { totalCount } }
          }
        }
      }
    }
  }
}
"""


def fetch_all_discussions(owner: str, name: str) -> list[dict]:
    nodes: list[dict] = []
    after = None
    while True:
        data = graphql(
            DISCUSSIONS_QUERY, {"owner": owner, "name": name, "after": after}
        )
        conn = (data.get("repository") or {}).get("discussions") or {}
        nodes.extend(conn.get("nodes") or [])
        page = conn.get("pageInfo") or {}
        if not page.get("hasNextPage"):
            return nodes
        after = page.get("endCursor")


def thumbs_up(comment: dict | None) -> int:
    """THUMBS_UP reactors on a comment — one per unique GitHub account."""
    if not comment:
        return 0
    for group in comment.get("reactionGroups") or []:
        if group.get("content") == "THUMBS_UP":
            return int((group.get("reactors") or {}).get("totalCount", 0))
    return 0


def agent_threads(nodes: list[dict], registry_names: set[str]) -> dict[str, dict]:
    """Discussion nodes that are real agent threads, keyed by agent name.

    Belt: the title must be agent-name-shaped and in the right category.
    Suspenders: it must exist in registry.json, so a thread cannot invent an
    agent. Duplicates resolve to the lowest number — the seeded original.
    """
    out: dict[str, dict] = {}
    for node in nodes:
        if ((node.get("category") or {}).get("name")) != CATEGORY:
            continue
        title = str(node.get("title", "")).strip()
        if not is_agent_title(title) or title not in registry_names:
            continue
        prev = out.get(title)
        if prev is None or node.get("number", 0) < prev.get("number", 0):
            out[title] = node
    return out


def build_snapshot(nodes: list[dict], registry_names: set[str]) -> dict:
    threads = agent_threads(nodes, registry_names)
    agents: dict[str, dict] = {}
    total_installs = total_runs = with_run_tally = 0
    for name in sorted(registry_names):
        node = threads.get(name)
        if not node:
            agents[name] = {"installs": 0, "runs": 0, "thread": False,
                            "url": None, "run_url": None}
            continue
        install_c = marker_comment_of(node, TALLY_MARKER)
        run_c = marker_comment_of(node, RUN_MARKER)
        installs, runs = thumbs_up(install_c), thumbs_up(run_c)
        total_installs += installs
        total_runs += runs
        with_run_tally += 1 if run_c else 0
        agents[name] = {
            "installs": installs,
            # Kept under the name the storefront already uses for this number,
            # so a reader never has to reconcile "installs" with "downloads".
            "downloads": installs,
            "runs": runs,
            "thread": True,
            "url": node.get("url"),
            "run_url": (run_c or {}).get("url") or node.get("url"),
        }
    return {
        "schema": SCHEMA,
        "repo": REPO,
        "category": CATEGORY,
        "note": (
            "Counts from the browser brainstem at /vbrainstem/. An install is a "
            "THUMBS_UP on the agent thread's download tally; a run is a THUMBS_UP "
            "on its vbrainstem run tally. One reaction per GitHub account, so both "
            "are unique people, not events — and both are a floor, because a "
            "signed-out visitor cannot react and is never counted."
        ),
        "totals": {
            "agents": len(registry_names),
            "with_thread": sum(1 for a in agents.values() if a["thread"]),
            "with_run_tally": with_run_tally,
            "installs": total_installs,
            "runs": total_runs,
        },
        "agents": agents,
    }


def persist(doc: dict) -> bool:
    """Write only on change, so a no-op run makes no commit."""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    new = json.dumps(doc, indent=2, sort_keys=True) + "\n"
    if OUT.is_file() and OUT.read_text(encoding="utf-8") == new:
        print(f"[vbrainstem] {OUT.relative_to(REPO_ROOT)} unchanged")
        return False
    OUT.write_text(new, encoding="utf-8")
    print(f"[vbrainstem] wrote {OUT.relative_to(REPO_ROOT)}")
    return True


def cmd_fetch() -> int:
    if not TOKEN:
        warn("no GITHUB_TOKEN set; leaving the usage snapshot unchanged.")
        return 0
    owner, _, name = REPO.partition("/")
    if not owner or not name:
        warn(f"invalid AIBAST_RATINGS_REPO '{REPO}'; expected owner/repo.")
        return 0
    registry_names = set(load_registry_agents())
    if not registry_names:
        warn("registry has no agents; leaving the snapshot unchanged.")
        return 0
    try:
        nodes = fetch_all_discussions(owner, name)
    except Exception as exc:                                    # noqa: BLE001
        # Offline or unauthenticated is not a build failure: a real snapshot
        # must never be replaced by zeroes a failed fetch produced.
        warn(f"could not reach GitHub ({exc}); keeping the last snapshot.")
        return 0
    doc = build_snapshot(nodes, registry_names)
    persist(doc)
    t = doc["totals"]
    print(f"[vbrainstem] {t['with_run_tally']}/{t['agents']} run tallies · "
          f"{t['installs']} installs · {t['runs']} runs")
    return 0


def cmd_tally(limit: int, delay: float, only: str | None) -> int:
    """Add the run-tally comment to agent threads that lack it. Idempotent."""
    if not TOKEN:
        warn("no GITHUB_TOKEN set; cannot add run-tally comments.")
        return 0
    owner, _, name = REPO.partition("/")
    registry_names = set(load_registry_agents())
    try:
        nodes = fetch_all_discussions(owner, name)
    except Exception as exc:                                    # noqa: BLE001
        warn(f"tally preflight failed ({exc}); nothing added.")
        return 0
    targets = [
        (title, node.get("id"))
        for title, node in sorted(agent_threads(nodes, registry_names).items())
        if marker_comment_of(node, RUN_MARKER) is None
        and (not only or title == only)
    ]
    if not targets:
        print("[vbrainstem] every targeted thread already has a run tally.")
        return 0
    batch = targets[:limit]
    print(f"[vbrainstem] adding {len(batch)} of {len(targets)} run tally "
          f"comment(s) (limit {limit})...")
    added = 0
    for title, disc_id in batch:
        try:
            graphql(ADD_COMMENT_MUTATION,
                    {"discussionId": disc_id, "body": RUN_BODY})
            added += 1
        except Exception as exc:                                # noqa: BLE001
            # Almost certainly a secondary rate limit. Stop; the next run picks
            # up where this one left off.
            warn(f"stopping after {added} comment(s): {exc}")
            break
        time.sleep(delay)
    print(f"[vbrainstem] added {added}; {len(targets) - added} still missing.")
    return 0


def cmd_track(agent_name: str) -> int:
    """Register one run: THUMBS_UP on the agent's run tally comment."""
    if not TOKEN:
        warn("no GITHUB_TOKEN set; run not tracked.")
        return 0
    owner, _, name = REPO.partition("/")
    registry_names = set(load_registry_agents())
    try:
        nodes = fetch_all_discussions(owner, name)
        node = agent_threads(nodes, registry_names).get(agent_name)
        if not node:
            warn(f"no discussion for '{agent_name}'; run not tracked.")
            return 0
        run_c = marker_comment_of(node, RUN_MARKER)
        if not run_c:
            warn(f"'{agent_name}' has no run tally yet; "
                 "run `vbrainstem_usage.py tally` first.")
            return 0
        graphql(ADD_REACTION_MUTATION, {"subjectId": run_c["id"]})
        print(f"[vbrainstem] run registered for {agent_name} "
              f"(discussion #{node.get('number')}).")
    except Exception as exc:                                    # noqa: BLE001
        warn(f"track failed ({exc}); run not tracked.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)
    tally = sub.add_parser("tally", help="provision run-tally comments")
    tally.add_argument("--limit", type=int, default=40)
    tally.add_argument("--delay", type=float, default=1.2)
    tally.add_argument("--only", help="target a single agent name")
    track = sub.add_parser("track", help="register one run")
    track.add_argument("agent", help="agent name, e.g. @aibast-agents-library/art-generator")
    sub.add_parser("fetch", help="snapshot installs/runs to state/")
    args = ap.parse_args()
    if args.command == "tally":
        return cmd_tally(args.limit, args.delay, args.only)
    if args.command == "track":
        return cmd_track(args.agent)
    return cmd_fetch()


if __name__ == "__main__":
    sys.exit(main())
