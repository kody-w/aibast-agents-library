#!/usr/bin/env python3
"""Accumulate GitHub Traffic API snapshots (views, clones, top paths) into
rar/traffic.json. The API only keeps 14 days; committing daily rows builds
the durable history. Requires a PAT with administration:read as
TRAFFIC_TOKEN (the Actions GITHUB_TOKEN cannot read traffic) — skips
gracefully without it. NOTE: this is an AIBAST addition, page-level only —
the upstream pattern has no view tracking besides Clarity."""
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "rar" / "traffic.json"
CFG = json.loads((ROOT / "rar" / "ratings-config.json").read_text())


def get(url, token):
    req = urllib.request.Request(url, headers={
        "Authorization": f"bearer {token}", "User-Agent": "aibast-traffic"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    token = os.environ.get("TRAFFIC_TOKEN", "")
    if not token:
        print("[traffic] no TRAFFIC_TOKEN — skipping (views need a PAT with administration:read)")
        return 0
    base = f"https://api.github.com/repos/{CFG['repo']}/traffic"
    try:
        views = get(base + "/views", token)
        clones = get(base + "/clones", token)
        paths = get(base + "/popular/paths", token)
        referrers = get(base + "/popular/referrers", token)
    except Exception as e:  # noqa: BLE001
        print(f"[traffic] fetch failed, history unchanged: {e}")
        return 0
    hist = json.loads(OUT.read_text()) if OUT.exists() else {
        "_note": "Daily GitHub Traffic API snapshots, accumulated past the API's 14-day window. Page-level only.",
        "days": {}, "popular_paths_latest": []}
    for row in views.get("views", []):
        day = hist["days"].setdefault(row["timestamp"][:10], {})
        day["views"], day["unique_visitors"] = row["count"], row["uniques"]
    for row in clones.get("clones", []):
        day = hist["days"].setdefault(row["timestamp"][:10], {})
        day["clones"], day["unique_cloners"] = row["count"], row["uniques"]
    hist["popular_paths_latest"] = [
        {"path": p["path"], "views_14d": p["count"], "uniques_14d": p["uniques"]}
        for p in paths]
    hist["referrers_latest"] = [
        {"referrer": p["referrer"], "views_14d": p["count"], "uniques_14d": p["uniques"]}
        for p in referrers]
    hist["days"] = dict(sorted(hist["days"].items()))
    OUT.write_text(json.dumps(hist, indent=1) + "\n")
    print(f"[traffic] history now covers {len(hist['days'])} days; "
          f"top path: {hist['popular_paths_latest'][:1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
