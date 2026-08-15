# Contributing an Agent

> ⚠️ **IMPORTANT:** This is an experimental project managed by a v-team from the Artificial Intelligence Business Applications Specialist Team (AIBAST), not an officially supported Microsoft product. Agent templates are starting points that must be customized before production use. AI-generated output may contain errors or unsupported patterns — human review remains important.

## Quick Version

```
1. Fork this repo
2. Create: agents/@yourname/my-agent.py    ← single file, that's it
3. Include: __manifest__ dict in the file
4. Run:    python build_registry.py (must pass)
5. PR:     Open pull request
```

---

## The Single File Principle

Every agent is **one `.py` file**. No manifest.json. No README.md. No subdirectory. The metadata lives inside the Python file as a `__manifest__` dict.

```
agents/@yourname/my-agent.py    ← this is the entire package
```

## Namespace Rules

Your namespace is `@yourgithubusername`. This is yours forever.

- `@yourname/agent-slug.py` — use lowercase kebab-case for filenames
- One agent per file
- Slugs must be unique within YOUR namespace (not globally)
- `@rapp/` is reserved for official base packages
- `@aibast-agents-library/` is the primary publisher for industry agent stacks

## Agent Template

```python
"""
My Agent — What it does in one line.

Longer description of what this agent does,
how to use it, and any important notes.
"""

# ═══════════════════════════════════════════════════════════════
# RAPP AGENT MANIFEST — Do not remove. Used by registry builder.
# ═══════════════════════════════════════════════════════════════
__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@yourname/my-agent",
    "version": "1.0.0",
    "display_name": "MyAgent",
    "description": "What this agent does in one sentence.",
    "author": "Your Name",
    "tags": ["category", "keyword1", "keyword2"],
    "category": "integrations",
    "quality_tier": "community",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}
# ═══════════════════════════════════════════════════════════════

from agents.basic_agent import BasicAgent


class MyAgent(BasicAgent):
    def __init__(self):
        self.name = __manifest__["display_name"]
        self.metadata = {
            "name": self.name,
            "description": __manifest__["description"],
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "Input parameter"
                    }
                },
                "required": ["input"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        input_data = kwargs.get('input', '')
        return f"Result: {input_data}"
```

## Quality Tiers

| Tier | Who | Meaning |
|------|-----|---------|
| `community` | Anyone | Submitted, basic validation passes |
| `verified` | Reviewed by maintainer | Tested, follows standards, no security issues |
| `official` | Core team | Maintained by core team, guaranteed compatibility |

New submissions start at `community`. Maintainers upgrade to `verified` after review.

## Agent Requirements

1. **Single file** — everything in one `.py` file
2. **`__manifest__` dict** with all required fields
3. **Inherits `BasicAgent`** — the only hard dependency
4. **Returns a string** — `perform()` always returns `str`
5. **No secrets in code** — use `os.environ.get()` and declare in `requires_env`
6. **Works offline** — handle missing env vars gracefully (return error message, don't crash)
7. **No network calls in `__init__`** — keep constructor fast for agent loading

## Versioning

Use [semantic versioning](https://semver.org/):

- **MAJOR** (2.0.0) — breaking changes to `perform()` signature
- **MINOR** (1.1.0) — new features, new parameters (backward compatible)
- **PATCH** (1.0.1) — bug fixes, documentation

## Validation

Before submitting, run the registry builder locally:

```bash
python build_registry.py
```

This validates your manifest and ensures the registry builds cleanly.

## PR Checklist

- [ ] `agents/@yourname/my-agent.py` file exists (single file!)
- [ ] `__manifest__` dict is present with all required fields
- [ ] Agent inherits from `BasicAgent`
- [ ] `python build_registry.py` passes with no errors
- [ ] No secrets, API keys, or customer data in code
- [ ] `requires_env` lists all needed environment variables

---

## Staging contributions

### Blog posts

Use the **Contribute** panel on the public [Agent Library](library.html#contribute)
when you do not want to work directly with Markdown and JSON. The page validates
your article, produces a staging preview, and downloads two files:

```text
submissions/blog/<slug>/post.md
submissions/blog/<slug>/metadata.json
```

`post.md` is the canonical article. `metadata.json` is its sidecar record:
author, audience, prerequisites, evidence, limitations, tags, and current
links. This follows the same review boundary as a portable RAR agent: one
canonical artifact plus metadata that makes validation deterministic.

### Quality bar

Every submission must state:

1. A concrete problem and intended audience
2. Prerequisites before a reader starts
3. Technical approach and reproducible evidence
4. Explicit limitations and boundaries
5. An actionable next step
6. A named author, publication date, lowercase tags, and current HTTPS links

Validate and render locally:

```bash
python scripts/blog_pipeline.py validate
python scripts/blog_pipeline.py render
python scripts/blog_pipeline.py check
```

`blog.html` contains a generated region. Do not hand-edit that region; update
the canonical files and re-run the generator. `check` fails when generated
output drifts from the canonical submissions.

### Secure handoff

GitHub Pages cannot safely authenticate an API write. The contributor downloads
the canonical submission and metadata sidecar, then attaches both files to the
prefilled public GitHub issue body while signed in. The marker
`<!-- aibast-blog-submission:v1 -->` is the first body line so it survives the
raw `?body=` handoff. Pages contains no PAT, client secret, app private key, or
privileged browser token.

Automated issue-to-PR ingestion is deliberately deferred: staging Pages events
run from the default branch rather than the live staging branch, and untrusted
attachments must not be processed in a write-token job. A maintainer manually
validates canonical files in staging before any review or promotion.

## Library-source contributions

The same Pages form supports a **library source** contribution. Its canonical
shape is:

```text
submissions/libraries/<slug>/metadata.json
submissions/libraries/<slug>/source.md
```

Capture the schema version, source name, canonical GitHub HTTPS URL pinned to a
repository commit, source type and format, owner, SPDX license, immutable ref,
manifest locator, SHA-256 digest, trust tier/status, enabled state, review
cadence, trust/review notes, and why it is useful. New sources begin as
`community_suggested` with `enabled: false`; a browser displays metadata only.
It never fetches, imports, renders, or executes source content from the
submitted URL.

Every discovered item is namespaced as `library-slug:item-slug`; bare item slugs
are rejected because they collide across sources. First-party and subscribed
sources must be GitHub repositories, releases, or raw files bound to a
repo+commit. Mutable branches, opaque web pages, file/SSH/private-IP targets,
and executable installers are rejected before any ingestion attempt.

### GitHub Discussions curation

The optional Giscus integration uses GitHub’s App/GraphQL authentication flow;
Pages holds no token. The deployment-only
`aibast-librarian-giscus-config/1.0` placeholder is disabled until verified
Giscus repo/category IDs are supplied. Library-source suggestions use
**Ideas** with a term such as `library-slug:source`. Approved item curation uses
**Announcements** with `library-slug:item-slug`. Comments and reactions are
curation signals only: they do not acknowledge terms, grant access, approve
restricted material, or replace Forms/Issue access requests.

Validate and regenerate the staging librarian catalog:

```bash
python scripts/librarian_pipeline.py validate
python scripts/librarian_pipeline.py render
python scripts/librarian_pipeline.py check
```

Automated source ingestion is deferred pending a reviewed staging deployment
gate. Any remote acquisition must run in reviewed CI or a trusted backend,
never in the browser.

### Internal workshop access configuration

`Internal workshop videos & one-pagers (SharePoint)` intentionally has no
public location URL. The public librarian lists only safe asset IDs, titles,
and descriptions. A tenant-approved Microsoft Forms URL may be supplied only
by trusted deployment configuration using the
`aibast-internal-workshop-access-config/1.0` schema in
`assets/internal-workshop-access-config.example.js`. The checked-in value is
always disabled with a `null` URL.

When configured, Forms is the preferred path for internal users because it
keeps identity, business justification, expected reach, impact, and follow-up
permission private. GitHub Issues remain the public/community fallback and
accept only asset IDs, a non-sensitive purpose, an impact band, and legal/trust
acknowledgements. Do not create a Form, submit a Form, or add a private URL
without owner and tenant approval.

The acknowledgement text is versioned (`terms_version: 2026-08-15`) and is an
engineering control pending organizational legal/privacy review. It does not
make a binding contract or determine legal compliance. Required
use/risk/confidentiality statements are separate from optional aggregate
analytics and follow-up consent.

### Deferred staging automation design

The public fallback is a raw, marker-first `?body=` GitHub issue handoff, not
an Issue Form. There is intentionally no active
`internal-workshop-access.yml` or `librarian-snapshot.yml` workflow in this
staging branch. GitHub issue, schedule, and manual-dispatch workflows are
loaded from the repository default branch rather than this live Pages branch,
so this staging prototype must not claim automatic triage, comments, metrics,
source synchronization, or access approval.

The committed schemas, validation scripts, and aggregate-only metric shape are
deferred design inputs for a separately reviewed deployment. Until then,
maintainers manually review public-safe issues, grant any approved access only
through an approved private channel, and record only approved, denied, or
fulfilled status publicly.

No active collector reads public access requests. If a separately approved
collector is introduced, it must parse the versioned
`optional_aggregate_metrics_consent: true` marker and exclude requests that
are false or missing from analytics. Operational owner review may still record
public-safe request status separately. The aggregate sidecar must never publish
requester identities; GitHub itself retains public issue authorship under its
own service terms.
