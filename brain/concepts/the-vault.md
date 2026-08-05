---
title: This vault
tags: [ms-rapp, extension, docs]
summary: Markdown notes that are both an Obsidian vault and a published site.
updated: 2026-08-05
---

# This vault

The documentation you are reading is a folder of plain Markdown notes in
`brain/`, with YAML frontmatter and `[[wikilinks]]`. That means:

- **Open `brain/` in Obsidian** and it works — no export, no conversion.
- **Or read it in a browser** at `brain.html`, which fetches the notes from
  GitHub raw and resolves the same links. No client required.

Indexes, tags, backlinks, and the graph are **derived** by the build, never
hand-maintained — a hand-written index drifts, and a drifted index is worse
than none. A note does not know who links to it; the build computes that.

The API endpoints carry metadata and a `raw_url`, never the note body, so
editing a note makes the change readable without rebuilding anything.

Specification: `ms-rapp-brain/1.0`. Related: [[concepts/extensions]],
[[how-to/use-the-static-api]].
