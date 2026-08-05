#!/usr/bin/env python3
"""ms-rapp-badge/1.0 — extension builder.

A drop-in module at the extension point defined by rapp/ext/PATTERN.md. The
core build step (scripts/build_api.py) discovers this file; it does not import
it by name and contains no badge logic. Delete this directory and the badge
endpoints disappear with zero edits anywhere else.

Contract (PATTERN.md §3): expose PROTOCOL, NAMESPACES, and build(ctx) -> dict.
"""
from __future__ import annotations

PROTOCOL = "ms-rapp-badge/1.0"
SPEC = "rapp/ext/ms-rapp-badge-1.0/SPEC.md"

# Every path this extension may write, relative to the API root. The core
# refuses anything outside these, so an extension cannot collide with core
# endpoints or with another extension.
NAMESPACES = ("badges.json", "badges/", "certified.json", "certified/", "wall.json")


def build(ctx) -> dict:
    """Generate the badge endpoints.

    ctx supplies everything from the core: ctx.load(path), ctx.write(rel, doc),
    ctx.prune(rel_dir, keep), ctx.agents, ctx.generated, ctx.pages_base.
    Returns the index.json "extensions" entry for this protocol.
    """
    catalog = ctx.load("badges.json", {"badges": []})
    roster = ctx.load("certified.json", {"members": [], "levels": {}})
    badge_by_id = {b["id"]: b for b in catalog.get("badges", [])}
    pages = ctx.pages_base
    gen = ctx.generated

    members = []
    for m in roster.get("members", []):
        user = str(m.get("username", "")).strip().lower()
        if not user:
            continue
        active = m.get("status", "active") == "active"
        awards = []
        for a in m.get("badges", []):
            meta = badge_by_id.get(a.get("id"))
            if not meta:
                # SPEC §4.3 / kernel §8: an unrecognized member is ignored,
                # never refused and never rendered from guessed metadata.
                continue
            awards.append({
                "id": meta["id"], "name": meta["name"], "tier": meta.get("tier"),
                "points": meta.get("points", 0), "color": meta.get("color", "0078d4"),
                "awarded_on": a.get("awarded_on"), "discussion": a.get("discussion"),
                "note": a.get("note"),
                "badge_url": f"{pages}/api/v1/certified/{user}/{meta['id']}/badge.json",
            })
        members.append({
            "username": user,
            "level": m.get("level", "certified"),
            "certified": active and bool(awards),
            "status": m.get("status", "active"),
            "certified_on": m.get("certified_on"),
            "revoked_on": m.get("revoked_on"),
            "reason": m.get("reason"),
            "note": m.get("note"),
            "badges": awards if active else [],
            "points": sum(a["points"] for a in awards) if active else 0,
            "profile_url": f"https://github.com/{user}",
            "verify_url": f"{pages}/api/v1/certified/{user}.json",
            "badge_url": f"{pages}/api/v1/certified/{user}/badge.json",
            "agents": sorted(
                a["name"] for a in ctx.agents
                if a.get("name", "").split("/")[0].lstrip("@").lower() == user
            ),
        })

    def shields(label, message, color):
        return {"schemaVersion": 1, "label": label, "message": message, "color": color}

    kept = set()
    for m in members:
        kept.add(ctx.write(f"certified/{m['username']}.json",
                           {"protocol": PROTOCOL, "schema": "aibast-certified/1.0",
                            "generated": gen, **m}))
        summary = (f"certified · {len(m['badges'])} badge"
                   f"{'' if len(m['badges']) == 1 else 's'}") if m["certified"] else "not certified"
        kept.add(ctx.write(f"certified/{m['username']}/badge.json",
                           shields("RAPP", summary,
                                   "brightgreen" if m["certified"] else "lightgrey")))
        for a in m["badges"]:
            kept.add(ctx.write(f"certified/{m['username']}/{a['id']}/badge.json",
                               shields("RAPP", a["name"], a["color"])))
    ctx.prune("certified", kept)

    holders = {}
    for m in members:
        for a in m["badges"]:
            holders.setdefault(a["id"], []).append(
                {"username": m["username"], "awarded_on": a["awarded_on"],
                 "discussion": a["discussion"]})

    kept_b = set()
    for b in catalog.get("badges", []):
        rows = sorted(holders.get(b["id"], []),
                      key=lambda h: (h["awarded_on"] or "", h["username"]))
        kept_b.add(ctx.write(f"badges/{b['id']}.json",
                             {"protocol": PROTOCOL, "schema": "aibast-badge/1.0",
                              "generated": gen, **b,
                              "holders": rows, "holder_count": len(rows)}))
    ctx.prune("badges", kept_b)

    ctx.write("badges.json", {
        "protocol": PROTOCOL, "schema": "aibast-badge-catalog/1.0", "generated": gen,
        "count": len(catalog.get("badges", [])),
        "lookup": f"{pages}/api/v1/badges/{{badge_id}}.json",
        "badges": [{**b, "holder_count": len(holders.get(b["id"], []))}
                   for b in catalog.get("badges", [])],
    })

    wall = sorted((m for m in members if m["certified"]),
                  key=lambda m: (-m["points"], -len(m["badges"]), m["username"]))
    ctx.write("wall.json", {
        "protocol": PROTOCOL, "schema": "aibast-wall/1.0", "generated": gen,
        "count": len(wall), "page": f"{pages}/wall.html",
        "members": [{k: m[k] for k in
                     ("username", "level", "points", "badges", "profile_url",
                      "verify_url", "badge_url", "agents")} for m in wall],
    })

    ctx.write("certified.json", {
        "protocol": PROTOCOL, "schema": "aibast-certified-roster/1.0", "generated": gen,
        "levels": roster.get("levels", {}),
        "count": sum(1 for m in members if m["certified"]),
        "lookup": f"{pages}/api/v1/certified/{{username}}.json",
        "note": ("Query any GitHub username. A username absent from this roster is "
                 "not certified; an entry with certified=false was revoked."),
        "members": members,
    })

    return {
        "spec": SPEC,
        "originated_by": "ms-rapp",
        "endpoints": [
            "badges.json", "badges/{badge_id}.json", "certified.json",
            "certified/{username}.json", "certified/{username}/badge.json",
            "certified/{username}/{badge_id}/badge.json", "wall.json",
        ],
    }
