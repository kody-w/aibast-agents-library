#!/usr/bin/env python3
"""Popularity — which solutions are actually being used, ranked and explained.

The library has been collecting signals for a while and never once answered the
question they exist to answer: of 48 solutions, which ones matter? This reads
every signal already snapshotted and produces one ranked table per run.

WHAT COUNTS, AND WHY IT IS WEIGHTED THAT WAY. The weights are printed in the
report next to the result, because a ranking whose weights are buried in a
script is a ranking nobody can argue with — and one nobody can argue with is
one nobody should trust.

  export   x5   Someone took a deck away. The strongest signal here: it costs
                a deliberate act and it means this is going in front of a
                customer. It is also the rarest, so it needs the largest weight
                to register at all against chattier metrics.
  install  x3   Someone downloaded the agent.py. Real intent, developer-shaped.
  play     x2   Someone watched the demo through. Interest, not commitment.
  comment  x2   Someone wrote a sentence. Rare enough to be worth more than a
                reaction, and the only signal that carries a reason with it.
  like     x1   One tap. The cheapest signal, weighted like one.

EVERY NUMBER IS PEOPLE, NOT EVENTS. All of these come from GitHub reactions and
comments, one per account, so nothing here can be inflated by refreshing a
page. That also means they are all UNDERCOUNTS: only signed-in people who
bothered to mark something appear. The report says so at the top rather than
letting a reader mistake it for traffic.

NO THREAD IS NOT ZERO. A solution whose Discussion has not been seeded is
reported as "not launched", never as a score of 0 — otherwise the newest
solutions would rank last for reasons that have nothing to do with anyone's
opinion of them, and the table would be a chart of seeding order.

Output:
  state/popularity.json   the ranked data, for the API and anything downstream
  docs/POPULARITY.md      the same thing as a report a person can read

Usage:
    python3 scripts/build_popularity.py
    python3 scripts/build_popularity.py --top 10
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE = REPO_ROOT / "state"
OUT = STATE / "popularity.json"
REPORT = REPO_ROOT / "docs" / "POPULARITY.md"
ONEPAGERS = REPO_ROOT / "data" / "onepagers.json"
REGISTRY = REPO_ROOT / "registry.json"

SCHEMA = "aibast-popularity/1.0"

# The ranking, in one place, so the report can print it verbatim.
WEIGHTS = {"exports": 5, "installs": 3, "plays": 2, "comments": 2, "likes": 1}

WHY = {
    "exports": "a deck taken away — the strongest and rarest signal",
    "installs": "an agent.py downloaded",
    "plays": "a demo watched",
    "comments": "a sentence written in the thread",
    "likes": "one tap",
}


def load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def agent_index() -> dict[str, str]:
    """Map a solution slug onto its registry agent name, where one exists.

    Only some solutions have an agent behind them — the rest are Copilot Studio
    or first-party configurations with nothing to download. A missing match is
    normal and is reported as "no agent", never as zero installs, because those
    are different facts.
    """
    reg = load(REGISTRY, {})
    names = [a.get("name", "") for a in (reg.get("agents") or [])]
    by_tail = {n.rsplit("/", 1)[-1]: n for n in names if n}
    out = {}
    doc = load(ONEPAGERS, {})
    for e in doc.get("onepagers", []):
        slug = e.get("slug")
        if not slug:
            continue
        for cand in (slug, slug.replace("-agent", ""), slug.replace("-", "_")):
            if cand in by_tail:
                out[slug] = by_tail[cand]
                break
    return out


def build() -> dict:
    exp = load(STATE / "export_engagement.json", {}).get("exports", {})
    vid = load(STATE / "video_engagement.json", {}).get("videos", {})
    rat = load(STATE / "discussion_ratings.json", {}).get("agents", {})
    onep = {e["slug"]: e for e in load(ONEPAGERS, {}).get("onepagers", [])
            if e.get("slug")}
    agents = agent_index()

    rows = []
    for slug, sol in sorted(onep.items()):
        e = exp.get(slug) or {}
        v = vid.get(slug) or {}
        agent_name = agents.get(slug)
        r = rat.get(agent_name) if agent_name else None

        signals = {
            "exports": int(e.get("exports") or 0),
            "installs": int((r or {}).get("downloads") or 0),
            "plays": int(v.get("plays") or 0),
            # Two threads can carry conversation about one solution. Both are
            # people talking about this thing, so both count.
            "comments": int(e.get("comments") or 0) + int(v.get("comments") or 0),
            "likes": int(e.get("likes") or 0) + int(v.get("likes") or 0)
                     + int((r or {}).get("upvotes") or 0),
        }
        contrib = {k: signals[k] * WEIGHTS[k] for k in WEIGHTS}
        score = sum(contrib.values())
        # WHICH SIGNAL CARRIED IT. A weight is per-unit, and the cheap signals
        # are far more numerous than the expensive ones — thirty plays will
        # out-total twelve exports even though an export is weighted higher.
        # That is the arithmetic working, and it is also exactly how a table
        # like this gets misread: the leader looks like "the most exported"
        # when it is really "the most watched". So the dominant contributor is
        # named on every row, and nobody has to reverse-engineer the score.
        led_by = max(contrib, key=lambda k: (contrib[k], -list(WEIGHTS).index(k))) \
            if score else None
        launched = bool(e.get("thread") or v.get("thread") or r)
        rows.append({
            "slug": slug,
            "display_name": sol.get("display_name") or slug,
            "industries": sol.get("industries")
                          or ([sol["industry"]] if sol.get("industry") else []),
            "signals": signals,
            "score": score,
            "led_by": led_by,
            "launched": launched,
            "decks": e.get("decks") or ["one-pager", "architecture"],
            "agent": agent_name,
            "thread": e.get("url") or v.get("url"),
        })

    live = [r for r in rows if r["launched"]]
    waiting = [r for r in rows if not r["launched"]]
    live.sort(key=lambda r: (-r["score"], r["display_name"]))
    waiting.sort(key=lambda r: r["display_name"])
    for i, r in enumerate(live, 1):
        r["rank"] = i

    totals = {k: sum(r["signals"][k] for r in rows) for k in WEIGHTS}
    return {
        "schema": SCHEMA,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "weights": WEIGHTS,
        "note": ("Every figure is people, not events: each comes from a GitHub "
                 "reaction or comment, one per account. They are therefore all "
                 "undercounts — only signed-in people who marked something "
                 "appear — and none of them is traffic. A solution with no "
                 "Discussion yet is listed as not launched rather than scored "
                 "zero."),
        "totals": totals,
        "counts": {"solutions": len(rows), "launched": len(live),
                   "not_launched": len(waiting)},
        "ranked": live,
        "not_launched": waiting,
    }


def report(doc: dict, top: int) -> str:
    w = doc["weights"]
    live, waiting, t = doc["ranked"], doc["not_launched"], doc["totals"]
    L = ["# Solution popularity", "",
         f"Generated {doc['generated']} · "
         f"{doc['counts']['launched']} of {doc['counts']['solutions']} solutions "
         "have a thread open.", "",
         "> " + doc["note"].replace("\n", " "), "",
         "## How the ranking is weighted", "",
         "| Signal | Weight | What it means |", "|---|---|---|"]
    for k in sorted(w, key=lambda x: -w[x]):
        L.append(f"| {k} | ×{w[k]} | {WHY[k]} |")
    L += ["", f"Across every solution: " +
          ", ".join(f"**{t[k]}** {k}" for k in sorted(w, key=lambda x: -w[x])) + ".", ""]

    if not any(t.values()):
        L += ["## No engagement recorded yet", "",
              "Every thread is open or waiting and nobody has marked anything. "
              "This is a real result, not a failure: the tallies exist, the "
              "exports are wired, and the first reaction will show up here on "
              "the next run. A ranking invented before there is anything to "
              "rank would be worse than an empty one.", ""]
    else:
        L += [f"## Most used ({'top ' + str(top) if len(live) > top else 'all'})", "",
              "| # | Solution | Score | Led by | Exports | Installs | Plays | Comments | Likes |",
              "|---|---|---|---|---|---|---|---|---|"]
        for r in live[:top]:
            s = r["signals"]
            L.append(f"| {r['rank']} | {r['display_name']} | **{r['score']}** | "
                     f"{r['led_by'] or '—'} | "
                     f"{s['exports']} | {s['installs']} | {s['plays']} | "
                     f"{s['comments']} | {s['likes']} |")
        L.append("")

    by_export = [r for r in live if r["signals"]["exports"]]
    if by_export:
        by_export = sorted(by_export, key=lambda r: -r["signals"]["exports"])[:10]
        L += ["## Most exported", "",
              "The same solutions ranked on exports alone — the question the "
              "export tally was added to answer, and the one the weighted score "
              "can bury under a louder signal.", "",
              "| Solution | Exports | Decks available |", "|---|---|---|"]
        L += [f"| {r['display_name']} | {r['signals']['exports']} | "
              f"{', '.join(r['decks'])} |" for r in by_export]
        L.append("")

    if waiting:
        L += ["## Not launched", "",
              "No Discussion has been seeded for these yet, so they have nothing "
              "to score. They are listed rather than ranked last, because "
              "ranking them would chart seeding order and call it popularity.",
              ""]
        L += ["- " + r["display_name"] for r in waiting[:60]]
        if len(waiting) > 60:
            L.append(f"- …and {len(waiting) - 60} more")
        L.append("")
    L += ["---", "",
          "Built by `scripts/build_popularity.py` from `state/export_engagement.json`, "
          "`state/video_engagement.json` and `state/discussion_ratings.json`.", ""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args()

    doc = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report(doc, args.top), encoding="utf-8")

    c = doc["counts"]
    t = doc["totals"]
    print(f"[popularity] {c['solutions']} solution(s): {c['launched']} launched, "
          f"{c['not_launched']} waiting on a thread")
    print("[popularity] " + ", ".join(f"{t[k]} {k}" for k in sorted(WEIGHTS)))
    if doc["ranked"] and doc["ranked"][0]["score"]:
        top = doc["ranked"][0]
        print(f"[popularity] leader: {top['display_name']} ({top['score']})")
    print(f"[popularity] {OUT.relative_to(REPO_ROOT)}, {REPORT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
