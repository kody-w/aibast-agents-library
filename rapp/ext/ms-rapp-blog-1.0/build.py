#!/usr/bin/env python3
"""ms-rapp-blog/1.0 — extension builder.

Posts are Markdown files in blog/ with YAML frontmatter. The build derives the
index, per-post documents, tag lists and a JSON Feed. Post bodies are never
copied into the API — each entry carries a raw_url, so publishing a post is a
commit and nothing else.

Contract: rapp/ext/PATTERN.md §3.
"""
from __future__ import annotations

import re
from pathlib import Path

PROTOCOL = "ms-rapp-blog/1.0"
SPEC = "rapp/ext/ms-rapp-blog-1.0/SPEC.md"
NAMESPACES = ("blog/",)

POSTS = "blog"
REPO = "microsoft/aibast-agents-library"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/main"


def _frontmatter(text: str) -> tuple[dict, str]:
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
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            meta[k] = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
        else:
            meta[k] = v.strip("'\"")
    return meta, body.lstrip("\n")


def _excerpt(body: str, limit: int = 260) -> str:
    for para in body.split("\n\n"):
        p = para.strip()
        if p and not p.startswith(("#", ">", "-", "*", "|", "```")):
            p = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", p)
            p = re.sub(r"[*`_]", "", p).replace("\n", " ")
            return p if len(p) <= limit else p[: limit - 1].rsplit(" ", 1)[0] + "…"
    return ""


def build(ctx) -> dict:
    root = Path(POSTS)
    gen, pages = ctx.generated, ctx.pages_base
    posts = []
    if root.is_dir():
        for p in sorted(root.glob("*.md")):
            slug = p.stem.lower()
            try:
                text = p.read_text(encoding="utf-8")
            except OSError:
                continue
            meta, body = _frontmatter(text)
            if str(meta.get("draft", "")).lower() == "true":
                continue          # drafts live in the repo, never in the feed
            posts.append({
                "slug": slug,
                "title": meta.get("title") or slug.replace("-", " ").title(),
                "date": meta.get("date", ""),
                "author": meta.get("author", "AIBAST"),
                "tags": meta.get("tags", []) if isinstance(meta.get("tags", []), list) else [meta["tags"]],
                "summary": meta.get("summary") or _excerpt(body),
                "path": p.as_posix(),
                "bytes": len(text.encode("utf-8")),
                "raw_url": f"{RAW_BASE}/{p.as_posix()}",
                "url": f"{pages}/blog.html#{slug}",
                "post_url": f"{pages}/api/v1/blog/posts/{slug}.json",
            })
    posts.sort(key=lambda x: (x["date"], x["slug"]), reverse=True)

    kept = set()
    for post in posts:
        kept.add(ctx.write(f"blog/posts/{post['slug']}.json", {
            "protocol": PROTOCOL, "schema": "ms-rapp-blog-post/1.0",
            "generated": gen, **post}))
    ctx.prune("blog/posts", kept)

    tags: dict[str, list[str]] = {}
    for post in posts:
        for t in post["tags"]:
            tags.setdefault(str(t).lower(), []).append(post["slug"])

    ctx.write("blog/index.json", {
        "protocol": PROTOCOL, "schema": "ms-rapp-blog-index/1.0", "generated": gen,
        "title": "Field Notes from the Frontier",
        "description": "How ms-rapp is actually built — decisions, defects, and the lexicon that comes out of the work.",
        "count": len(posts),
        "reader": f"{pages}/blog.html",
        "feed": f"{pages}/api/v1/blog/feed.json",
        "tags": [{"tag": t, "count": len(v)} for t, v in sorted(tags.items())],
        "posts": posts,
    })

    # JSON Feed 1.1 — a reader subscribes without anyone running a feed service.
    ctx.write("blog/feed.json", {
        "version": "https://jsonfeed.org/version/1.1",
        "title": "ms-rapp — Field Notes from the Frontier",
        "home_page_url": f"{pages}/blog.html",
        "feed_url": f"{pages}/api/v1/blog/feed.json",
        "description": "Field notes from building ms-rapp.",
        "items": [{
            "id": p["url"], "url": p["url"], "title": p["title"],
            "summary": p["summary"], "date_published": (p["date"] + "T00:00:00Z") if p["date"] else None,
            "authors": [{"name": p["author"]}], "tags": p["tags"],
            "external_url": p["raw_url"],
        } for p in posts],
    })

    return {
        "spec": SPEC,
        "originated_by": "ms-rapp",
        "human_ui": {"blog": f"{pages}/blog.html"},
        "llms_lines": [
            "- [Field notes index]({PAGES}/api/v1/blog/index.json): posts on how this is built; each carries a raw_url.",
        ],
        "agent_recipes": [
            {"goal": "Read how the platform is built and why",
             "get": "blog/index.json",
             "then": "Each post carries raw_url for the Markdown, or subscribe to blog/feed.json (JSON Feed 1.1)."},
        ],
        "endpoints": ["blog/index.json", "blog/posts/{slug}.json", "blog/feed.json"],
    }
