# ms-rapp-blog/1.0

**Publishing a post is committing a Markdown file. Nothing else.**

Status: draft standard, originated in the ms-rapp distribution. Built on
[`rapp-static-api/1.0`](../../standards/rapp-static-api-SPEC.md) and the
[extension pattern](../PATTERN.md).

## 1. Posts

A post is one Markdown file in `blog/` with YAML frontmatter:

```yaml
---
title: Field notes from the frontier
date: 2026-08-05
author: AIBAST
tags: [method, lexicon]
summary: Optional. Derived from the first paragraph when absent.
draft: false
---
```

`draft: true` keeps a post in the repository and out of the index and feed.

## 2. Derived

| Endpoint | Contents |
|---|---|
| `blog/index.json` | Every published post, newest first, with summary and raw URL |
| `blog/posts/{slug}.json` | One post's metadata |
| `blog/feed.json` | JSON Feed 1.1, so a reader can subscribe with no feed service |

Rules:

1. **Bodies are never copied into the API.** Each entry carries `raw_url`; a
   reader fetches the Markdown. Editing a post needs no rebuild to be readable.
2. **Ordering is by `date`, newest first**, with the slug as a stable
   tiebreaker — so the same inputs always produce the same order.
3. A summary is the author's `summary`, or the first prose paragraph.
4. Every generated document carries `protocol`, `schema`, `generated`.

## 3. Conformance

- [ ] Posts are Markdown with frontmatter carrying `title` and `date`.
- [ ] `draft: true` is excluded from index and feed.
- [ ] Index, per-post documents and the feed are derived by one build step.
- [ ] Bodies are referenced by `raw_url`, never duplicated.
- [ ] The feed validates as JSON Feed 1.1.
- [ ] Conforms to [PATTERN.md](../PATTERN.md): removing the directory leaves
      every core endpoint byte-identical.
