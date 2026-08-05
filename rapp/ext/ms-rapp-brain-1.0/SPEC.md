# ms-rapp-brain/1.0

**A convention for turning a folder of plain Markdown notes into a browsable,
linkable, machine-readable knowledge base served from static files — readable
in Obsidian, and readable by anyone with a browser and no client at all.**

Status: **draft standard**, originated in the ms-rapp distribution.
Built on [`rapp-static-api/1.0`](../../standards/rapp-static-api-SPEC.md) and
the [ms-rapp extension pattern](../PATTERN.md). Requirement terms are
[RFC 2119]/[RFC 8174].

Reference implementation: this repository — [`brain/`](../../../brain/),
[`build.py`](build.py), [`brain.html`](../../../brain.html).

---

## 1. Why

Documentation that only lives in a site generator is hard to think in;
documentation that only lives in a personal notes app is hard to publish. The
second-brain conventions solve the first problem — one idea per note, dense
links between notes, indexes derived rather than written. This profile keeps
those properties and adds publication: the same folder is a working vault in a
notes client **and** a static site with search, backlinks, and a graph, with no
build-time site generator and no client requirement for readers.

The source of truth stays `.md` files in git. Everything else is derived.

## 2. The vault

A vault is a directory (`brain/` by default) of UTF-8 Markdown notes.

**Every note MUST** begin with YAML frontmatter containing at least:

```yaml
---
title: What this note is
tags: [ms-rapp, governance]
---
```

Optional frontmatter: `summary`, `updated` (ISO-8601 date), `aliases`
(alternate names a link may use), `status`.

**Links between notes use wikilink syntax:** `[[note-slug]]` or
`[[note-slug|display text]]`. A note's **slug** is its path under the vault
root without the `.md` extension. Slugs MUST be lowercase `[a-z0-9/-]`.

A link to a slug that does not exist is a **dangling link**. Dangling links are
recorded, never invented, and never fatal — the same forward-compatibility rule
the kernel states for unrecognized members.

## 3. Derived, never hand-written

Indexes, backlinks, tag lists, and the graph are **generated**. An implementation
MUST NOT keep a hand-maintained index of notes: it will drift, and a drifted
index is worse than none. The build step derives:

| Endpoint | Contents |
|---|---|
| `brain/index.json` | Every note: slug, title, tags, summary, size, outgoing links, backlink count, raw URL |
| `brain/notes/{slug}.json` | One note: metadata, outgoing links, **backlinks**, and where to fetch its Markdown |
| `brain/tags.json` | Every tag and the notes carrying it |
| `brain/graph.json` | `nodes` and `edges` for a graph view |

Rules:

1. **Backlinks are computed**, never declared. A note does not know who links
   to it; the build does.
2. Slugs containing `/` are flattened with `-` in endpoint filenames, and the
   original slug is preserved in the payload.
3. Every document carries `protocol`, `schema`, and `generated`.
4. Note **bodies are not copied into the API**. The endpoints carry metadata
   and a `raw_url`; a reader fetches the Markdown itself. This keeps the API
   small, keeps git the single source of truth, and means a note edit needs no
   endpoint rebuild to be readable.

## 4. Readers

A conformant reader:

- resolves `[[wikilinks]]` against `index.json` and marks dangling ones
  visually rather than 404-ing;
- shows **backlinks** for the open note;
- needs no notes client and no server — it is a static page fetching the same
  endpoints anyone else can.

Obsidian itself is a conformant reader by construction: the vault is ordinary
Markdown with ordinary wikilinks, so opening `brain/` in Obsidian works with no
export step.

## 5. Conformance

- [ ] Vault notes are plain Markdown with YAML frontmatter carrying `title`.
- [ ] Links use `[[slug]]` / `[[slug|text]]`; slugs are lowercase paths.
- [ ] Indexes, tags, backlinks, and graph are derived by one build step.
- [ ] Dangling links are reported, never invented, never fatal.
- [ ] Endpoints carry `protocol`, `schema`, `generated`.
- [ ] Note bodies are referenced by `raw_url`, not duplicated into the API.
- [ ] The vault opens directly in a Markdown notes client with no conversion.
- [ ] The extension conforms to [PATTERN.md](../PATTERN.md): removing its
      directory leaves every core endpoint byte-identical.
