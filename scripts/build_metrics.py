#!/usr/bin/env python3
"""Build state/metrics.json — the public metrics snapshot for the
AIBAST Agents Library dashboard (metrics.html).

Sources, all public and verifiable:
  * GitHub repo API        — stars, forks, open issues
  * GitHub traffic API     — clones, page views, popular paths, referrers
                             (requires admin-read; without it the last
                             authorized read is reused so figures never
                             zero out — they just stop advancing)
  * jsDelivr CDN stats     — per-file fetch counts for agent files
  * registry.json          — agents, publishers, categories, sizes
  * state/discussion_ratings.json — upvotes, tracked installer downloads,
                             comments and signal-poll counts from GitHub
                             Discussions (built by discussion_ratings.py)
  * state/aggregated.json  — aggregated outside skills (crawl_skills.py)

GitHub only exposes a rolling 14-day traffic window, so each run merges the
window into state/metrics_history.json deduplicated by date — the all-time
totals grow from the first day of tracking and never double-count.

Runs without a token: every fetch degrades gracefully and the snapshot is
rebuilt from registry + prior history. Never fails the build.

Usage:  [GITHUB_TOKEN=...] python scripts/build_metrics.py
Env:    AIBAST_METRICS_REPO   owner/repo   (default: microsoft/aibast-agents-library)
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE = REPO_ROOT / "state"
REGISTRY_FILE = REPO_ROOT / "registry.json"
METRICS_FILE = STATE / "metrics.json"
HISTORY_FILE = STATE / "metrics_history.json"
RATINGS_FILE = STATE / "discussion_ratings.json"
AGGREGATED_FILE = STATE / "aggregated.json"

REPO = os.environ.get("AIBAST_METRICS_REPO", "microsoft/aibast-agents-library")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""

SCHEMA = "aibast-metrics/1.0"


def log(msg: str) -> None:
    print(f"[build-metrics] {msg}")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_json(url: str):
    headers = {"User-Agent": "aibast-metrics", "Accept": "application/vnd.github+json"}
    if TOKEN and "github.com" in url:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))


def try_fetch(url: str, label: str):
    try:
        return fetch_json(url)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        log(f"{label}: unavailable ({getattr(exc, 'code', exc)})")
        return None


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


# ── collectors ──────────────────────────────────────────────────────────────

def collect_repo() -> dict:
    d = try_fetch(f"https://api.github.com/repos/{REPO}", "repo")
    if not d:
        return {}
    return {
        "stars": d.get("stargazers_count", 0),
        "forks": d.get("forks_count", 0),
        "open_issues": d.get("open_issues_count", 0),
    }


def collect_releases() -> dict:
    rows = try_fetch(f"https://api.github.com/repos/{REPO}/releases?per_page=20",
                     "releases") or []
    releases, total = [], 0
    for r in rows if isinstance(rows, list) else []:
        assets = [{"name": a.get("name"), "downloads": a.get("download_count", 0)}
                  for a in r.get("assets", [])]
        dl = sum(a["downloads"] for a in assets)
        total += dl
        releases.append({
            "tag": r.get("tag_name"), "name": r.get("name"),
            "published_at": r.get("published_at"),
            "assets": assets, "downloads": dl,
        })
    return {"releases": releases, "total_downloads": total}


def collect_traffic() -> dict:
    """Traffic endpoints need admin read. On 403/anything, mark live=False
    so the dashboard can say the figures are from the last authorized read."""
    base = f"https://api.github.com/repos/{REPO}/traffic"
    clones = try_fetch(f"{base}/clones", "traffic/clones")
    if clones is None:
        return {"live": False}
    views = try_fetch(f"{base}/views", "traffic/views") or {}
    paths = try_fetch(f"{base}/popular/paths", "traffic/paths") or []
    refs = try_fetch(f"{base}/popular/referrers", "traffic/referrers") or []
    return {
        "live": True,
        "as_of": now_iso(),
        "clones_14d": clones.get("count", 0),
        "clone_uniques_14d": clones.get("uniques", 0),
        "views_14d": views.get("count", 0),
        "view_uniques_14d": views.get("uniques", 0),
        "daily_clones": [{"date": c.get("timestamp", "")[:10],
                          "count": c.get("count", 0),
                          "uniques": c.get("uniques", 0)}
                         for c in clones.get("clones", [])],
        "daily_views": [{"date": v.get("timestamp", "")[:10],
                         "count": v.get("count", 0)}
                        for v in views.get("views", [])],
        "paths": [{"path": p.get("path"), "count": p.get("count", 0)}
                  for p in paths[:15]] if isinstance(paths, list) else [],
        "referrers": [{"referrer": r.get("referrer"), "count": r.get("count", 0)}
                      for r in refs[:15]] if isinstance(refs, list) else [],
    }


def collect_jsdelivr(agents: list[dict]) -> dict:
    owner_repo = REPO.replace("/", "/")
    stats = try_fetch(
        f"https://data.jsdelivr.com/v1/stats/packages/gh/{owner_repo}?period=year",
        "jsdelivr")
    files = try_fetch(
        f"https://data.jsdelivr.com/v1/stats/packages/gh/{owner_repo}/files?period=year&limit=50",
        "jsdelivr/files") or []
    by_file = {}
    if isinstance(files, list):
        for f in files:
            by_file[str(f.get("name", "")).lstrip("/")] = (
                (f.get("hits") or {}).get("total", 0)
            )
    file_rows = []
    for a in agents:
        hits = by_file.get(a.get("_file", ""), 0)
        if hits:
            file_rows.append({"file": a["_file"], "agent": a["name"],
                              "kind": "agent", "hits": hits})
    for name, hits in by_file.items():
        if hits and not any(r["file"] == name for r in file_rows):
            file_rows.append({"file": name, "agent": None,
                              "kind": "other", "hits": hits})
    file_rows.sort(key=lambda r: -r["hits"])
    total = ((stats or {}).get("hits") or {}).get("total", 0)
    return {
        "total_hits": total,
        "bandwidth": ((stats or {}).get("bandwidth") or {}).get("total", 0),
        "rank": ((stats or {}).get("hits") or {}).get("rank"),
        "files": file_rows[:25],
        "agent_file_hits": sum(r["hits"] for r in file_rows if r["kind"] == "agent"),
    }


# ── history accumulation ────────────────────────────────────────────────────

def merge_history(history: dict, traffic: dict, cdn_total: int) -> dict:
    daily = {d["date"]: d for d in history.get("daily", [])}
    if traffic.get("live"):
        for c in traffic.get("daily_clones", []):
            row = daily.setdefault(c["date"], {"date": c["date"], "clones": 0,
                                               "clone_uniques": 0, "views": 0,
                                               "cdn": 0})
            row["clones"] = max(row.get("clones", 0), c["count"])
            row["clone_uniques"] = max(row.get("clone_uniques", 0), c["uniques"])
        for v in traffic.get("daily_views", []):
            row = daily.setdefault(v["date"], {"date": v["date"], "clones": 0,
                                               "clone_uniques": 0, "views": 0,
                                               "cdn": 0})
            row["views"] = max(row.get("views", 0), v["count"])
        history["last_traffic"] = {
            "as_of": traffic["as_of"],
            "clones_14d": traffic["clones_14d"],
            "clone_uniques_14d": traffic["clone_uniques_14d"],
            "views_14d": traffic["views_14d"],
            "view_uniques_14d": traffic["view_uniques_14d"],
            "paths": traffic["paths"], "referrers": traffic["referrers"],
        }
    # CDN: attribute growth since the last snapshot to today.
    today = datetime.now(timezone.utc).date().isoformat()
    prev_cdn = history.get("cdn_total", 0)
    if cdn_total > prev_cdn:
        row = daily.setdefault(today, {"date": today, "clones": 0,
                                       "clone_uniques": 0, "views": 0, "cdn": 0})
        row["cdn"] = row.get("cdn", 0) + (cdn_total - prev_cdn)
        history["cdn_total"] = cdn_total
    elif "cdn_total" not in history:
        history["cdn_total"] = cdn_total
    history["daily"] = sorted(daily.values(), key=lambda d: d["date"])
    history.setdefault("tracking_since", today)
    return history


# ── assembly ────────────────────────────────────────────────────────────────

def slim(a: dict, ratings: dict) -> dict:
    r = ratings.get(a["name"], {})
    return {
        "name": a["name"], "display_name": a.get("display_name"),
        "category": a.get("category", "uncategorized"),
        "tier": a.get("quality_tier", "community"),
        "file": a.get("_file"), "lines": a.get("_lines", 0),
        "upvotes": r.get("upvotes", 0), "downloads": r.get("downloads", 0),
        "comments": r.get("comments", 0), "score": r.get("score", 0),
        "signals": r.get("signals", {}), "discussion": r.get("url", ""),
    }


def top(rows: list[dict], key: str, n: int = 15) -> list[dict]:
    ranked = [r for r in rows if r.get(key)]
    ranked.sort(key=lambda r: (-r[key], r["name"]))
    return ranked[:n]


def main() -> int:
    registry = load_json(REGISTRY_FILE, {"agents": [], "stats": {}})
    agents = registry.get("agents", [])
    stats = registry.get("stats", {})
    ratings_doc = load_json(RATINGS_FILE, {})
    ratings = ratings_doc.get("agents", {}) if isinstance(ratings_doc, dict) else {}
    aggregated = load_json(AGGREGATED_FILE, {"stats": {}, "skills": [], "sources": []})

    repo = collect_repo()
    releases = collect_releases()
    traffic = collect_traffic()
    cdn = collect_jsdelivr(agents)

    history = load_json(HISTORY_FILE, {})
    history = merge_history(history, traffic, cdn["total_hits"])
    last_traffic = history.get("last_traffic", {})

    daily = history.get("daily", [])
    all_clones = sum(d.get("clones", 0) for d in daily)
    rows = [slim(a, ratings) for a in agents]
    tracked_downloads = sum(r["downloads"] for r in rows)
    upvotes = sum(r["upvotes"] for r in rows)
    comments = sum(r["comments"] for r in rows)

    # Publisher rollup
    pubs: dict[str, dict] = {}
    for r in rows:
        p = r["name"].split("/")[0]
        row = pubs.setdefault(p, {"name": p, "agents": 0, "upvotes": 0,
                                  "downloads": 0, "comments": 0, "score": 0})
        row["agents"] += 1
        row["upvotes"] += r["upvotes"]
        row["downloads"] += r["downloads"]
        row["comments"] += r["comments"]
        row["score"] += r["score"]
    publishers = sorted(pubs.values(), key=lambda p: (-p["score"], -p["agents"]))

    # Category rollup
    cats: dict[str, dict] = {}
    for r in rows:
        c = cats.setdefault(r["category"], {"name": r["category"], "agents": 0,
                                            "upvotes": 0, "downloads": 0})
        c["agents"] += 1
        c["upvotes"] += r["upvotes"]
        c["downloads"] += r["downloads"]
    categories = sorted(cats.values(), key=lambda c: -c["agents"])

    downloads_total = (all_clones + history.get("cdn_total", 0)
                       + releases["total_downloads"] + tracked_downloads)

    snapshot = {
        "schema": SCHEMA,
        "repo_name": REPO,
        "generated_at": now_iso(),
        "totals": {
            "downloads": downloads_total,
            "clones": all_clones,
            "cdn_hits": history.get("cdn_total", 0),
            "agent_file_downloads": cdn["agent_file_hits"],
            "release_downloads": releases["total_downloads"],
            "tracked_downloads": tracked_downloads,
            "upvotes": upvotes,
            "comments": comments,
            "agents": stats.get("total_agents", len(agents)),
            "publishers": stats.get("publishers", len(pubs)),
            "categories": stats.get("categories", len(cats)),
            "total_lines": sum(a.get("_lines", 0) for a in agents),
            "clones_14d": last_traffic.get("clones_14d"),
            "clone_uniques_14d": last_traffic.get("clone_uniques_14d"),
            "page_views": sum(d.get("views", 0) for d in daily),
            "view_uniques_14d": last_traffic.get("view_uniques_14d"),
            "tracking_since": history.get("tracking_since"),
            "days_tracked": len(daily),
        },
        "repo": repo,
        "traffic": {
            "live": traffic.get("live", False),
            "as_of": last_traffic.get("as_of") or traffic.get("as_of"),
            "paths": last_traffic.get("paths", []),
            "referrers": last_traffic.get("referrers", []),
        },
        "cdn": cdn,
        "releases": releases,
        "daily": daily,
        "leaderboards": {
            "most_downloaded": top(rows, "downloads"),
            "most_upvoted": top(rows, "upvotes"),
            "most_discussed": top(rows, "comments"),
            "top_score": top(rows, "score"),
            "largest": top(rows, "lines"),
            "categories": categories,
            "publishers": publishers,
        },
        "aggregated": {
            "total": (aggregated.get("stats") or {}).get("total", 0),
            "converted": (aggregated.get("stats") or {}).get("converted", 0),
            "scored_by_gates": (aggregated.get("stats") or {}).get("scored_by_gates", 0),
            "sources": aggregated.get("sources", []),
        },
        "sources": [
            {"name": "GitHub traffic API", "metric": "clones, page views, paths, referrers",
             "url": f"https://github.com/{REPO}/graphs/traffic"},
            {"name": "jsDelivr CDN", "metric": "per-file fetches of agent files",
             "url": f"https://data.jsdelivr.com/v1/stats/packages/gh/{REPO}"},
            {"name": "GitHub releases", "metric": "release asset downloads",
             "url": f"https://github.com/{REPO}/releases"},
            {"name": "GitHub Discussions", "metric": "upvotes, tracked installer downloads, comments, signals",
             "url": f"https://github.com/{REPO}/discussions"},
            {"name": "registry.json", "metric": "agents, publishers, categories",
             "url": "registry.json"},
            {"name": "state/aggregated.json", "metric": "aggregated outside skills",
             "url": "state/aggregated.json"},
        ],
    }

    STATE.mkdir(parents=True, exist_ok=True)
    METRICS_FILE.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    HISTORY_FILE.write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")
    log(f"wrote {METRICS_FILE.relative_to(REPO_ROOT)} "
        f"({snapshot['totals']['agents']} agents, "
        f"traffic {'live' if traffic.get('live') else 'reused'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
