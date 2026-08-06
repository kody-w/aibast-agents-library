#!/usr/bin/env python3
"""ms-rapp-brain/1.0 — extension builder.

Scans the Markdown vault and derives the index, per-note documents (with
computed backlinks), tag lists, and the link graph. Note bodies are never
copied into the API: each endpoint carries a raw_url, so editing a note needs
no rebuild to be readable.

Contract: rapp/ext/PATTERN.md §3.
"""
from __future__ import annotations

import re
from pathlib import Path

PROTOCOL = "ms-rapp-brain/1.0"
SPEC = "rapp/ext/ms-rapp-brain-1.0/SPEC.md"
NAMESPACES = ("brain/",)

VAULT = "brain"
REPO = "microsoft/aibast-agents-library"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/main"

WIKILINK = re.compile(r"\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]")


def _frontmatter(text: str) -> tuple[dict, str]:
    """Parse the leading YAML block without a YAML dependency: this profile
    only defines scalar and simple-list fields, so a tolerant reader is
    correct and keeps the build dependency-free."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    head, body = text[3:end], text[end + 4:]
    meta: dict = {}
    for line in head.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if val.startswith("[") and val.endswith("]"):
            meta[key] = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
        else:
            meta[key] = val.strip("'\"")
    return meta, body.lstrip("\n")


def _endpoint_name(slug: str) -> str:
    return slug.replace("/", "-")


def build(ctx) -> dict:
    root = Path(VAULT)
    gen = ctx.generated
    pages = ctx.pages_base

    notes: dict[str, dict] = {}
    if root.is_dir():
        for p in sorted(root.rglob("*.md")):
            slug = p.relative_to(root).as_posix()[:-3].lower()
            try:
                text = p.read_text(encoding="utf-8")
            except OSError:
                continue
            meta, body = _frontmatter(text)
            links, seen = [], set()
            for m in WIKILINK.finditer(body):
                target = m.group(1).strip().lower()
                if target and target not in seen:
                    seen.add(target)
                    links.append(target)
            notes[slug] = {
                "slug": slug,
                "title": meta.get("title") or slug.rsplit("/", 1)[-1].replace("-", " ").title(),
                "summary": meta.get("summary", ""),
                "tags": meta.get("tags", []) if isinstance(meta.get("tags", []), list) else [meta["tags"]],
                "updated": meta.get("updated"),
                "status": meta.get("status"),
                "aliases": meta.get("aliases", []) if isinstance(meta.get("aliases", []), list) else [meta["aliases"]],
                "path": p.as_posix(),
                "bytes": len(text.encode("utf-8")),
                "links": links,
                "raw_url": f"{RAW_BASE}/{p.as_posix()}",
                "note_url": f"{pages}/api/v1/brain/notes/{_endpoint_name(slug)}.json",
                "reader_url": f"{pages}/brain.html#{slug}",
            }

    # Backlinks are computed, never declared (SPEC §3.1). Dangling links are
    # recorded and reported — never invented, never fatal.
    alias_to_slug = {}
    for slug, n in notes.items():
        for a in n["aliases"]:
            alias_to_slug[str(a).lower()] = slug
    backlinks: dict[str, list[str]] = {s: [] for s in notes}
    dangling: list[dict] = []
    edges = []
    for slug, n in notes.items():
        resolved = []
        for target in n["links"]:
            t = target if target in notes else alias_to_slug.get(target)
            if t:
                resolved.append(t)
                backlinks[t].append(slug)
                edges.append({"from": slug, "to": t})
            else:
                dangling.append({"from": slug, "to": target})
        n["links"] = resolved

    kept = set()
    for slug, n in notes.items():
        kept.add(ctx.write(f"brain/notes/{_endpoint_name(slug)}.json", {
            "protocol": PROTOCOL, "schema": "ms-rapp-brain-note/1.0", "generated": gen,
            **n, "backlinks": sorted(set(backlinks[slug])),
        }))
    ctx.prune("brain/notes", kept)

    tags: dict[str, list[str]] = {}
    for slug, n in notes.items():
        for tag in n["tags"]:
            tags.setdefault(str(tag).lower(), []).append(slug)

    ctx.write("brain/index.json", {
        "protocol": PROTOCOL, "schema": "ms-rapp-brain-index/1.0", "generated": gen,
        "vault": VAULT, "count": len(notes),
        "reader": f"{pages}/brain.html",
        "raw_base": RAW_BASE,
        "dangling_links": dangling,
        "notes": [{k: n[k] for k in
                   ("slug", "title", "summary", "tags", "updated", "path",
                    "bytes", "links", "raw_url", "note_url")}
                  | {"backlinks": len(set(backlinks[s]))}
                  for s, n in sorted(notes.items())],
    })

    ctx.write("brain/tags.json", {
        "protocol": PROTOCOL, "schema": "ms-rapp-brain-tags/1.0", "generated": gen,
        "count": len(tags),
        "tags": [{"tag": t, "count": len(v), "notes": sorted(v)}
                 for t, v in sorted(tags.items())],
    })

    ctx.write("brain/graph.json", {
        "protocol": PROTOCOL, "schema": "ms-rapp-brain-graph/1.0", "generated": gen,
        "nodes": [{"id": s, "title": n["title"], "tags": n["tags"],
                   "degree": len(n["links"]) + len(set(backlinks[s]))}
                  for s, n in sorted(notes.items())],
        "edges": edges,
    })

    # Ecosystem compatibility: the RAPP vault convention (pages/vault/_manifest.json)
    # is already read by existing tooling. Emitting that shape too means a
    # RAPP-vault reader can open this vault unmodified, while our derived
    # index adds the computed backlinks and graph that shape does not carry.
    ctx.write("brain/_manifest.json", {
        "protocol": PROTOCOL, "schema": "ms-rapp-brain-manifest/1.0", "generated": gen,
        "title": "ms-rapp Vault",
        "subtitle": "Documentation for the ms-rapp distribution",
        "github": f"https://github.com/{REPO}",
        "entry": "index.md",
        "index": f"{pages}/api/v1/brain/index.json",
        "raw_base": f"{RAW_BASE}/{VAULT}",
        "notes": [{"path": f"{s}.md", "title": n["title"],
                   "section": (s.rsplit("/", 1)[0] if "/" in s else None),
                   "status": n.get("status") or "published"}
                  for s, n in sorted(notes.items())],
    })

    return {
        "spec": SPEC,
        "originated_by": "ms-rapp",
        "reader": f"{pages}/brain.html",
        "human_ui": {"docs": f"{pages}/brain.html"},
        "llms_lines": [
            "- [Documentation vault index]({PAGES}/api/v1/brain/index.json): every note, with its links and backlinks.",
            "- [Vault reader]({PAGES}/brain.html): the same notes for humans; the folder also opens in Obsidian.",
        ],
        "agent_recipes": [
            {"goal": "Learn how the platform works",
             "get": "brain/index.json",
             "then": "Each note carries raw_url; follow .links to traverse the documentation graph, "
                     "or fetch llms-full.txt for everything inline."},
        ],
        "endpoints": ["brain/index.json", "brain/notes/{slug}.json",
                      "brain/tags.json", "brain/graph.json", "brain/_manifest.json"],
    }
