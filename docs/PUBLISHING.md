# Publishing on the AIBAST Agents Library

The library is multi-publisher by design. **Your GitHub username is your
publisher handle by default** — everything you publish lives under your own
track: `agents/@<your-github-username>/`.

## 1. Apply once

Open a [publisher application](../../issues/new?template=publisher-application.yml)
(2-minute issue form). It records your handle and what you plan to publish.
Your handle is `@<your-github-username>` unless a maintainer approves an
organization handle.

## 2. Write the agent (or skill)

Two output formats are welcome — pick per submission:

- **`agent.py`** — a single-file Python agent extending `BasicAgent` with a
  `metadata` function schema and a `perform(**kwargs)` method. Drop-in
  compatible with the RAPP brainstem: it self-registers from the `agents/`
  folder with no restart.
- **`skill.md`** — a single-file skill with YAML frontmatter and the RAPP
  deterministic layer embedded (explicit steps, pause points, verifiable
  outcomes — see the repo's root `skill.md` for the pattern).

Every submission carries a `__manifest__` (for `skill.md`, in the
frontmatter) with the required fields validated by `build_registry.py`:

```python
__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@<your-github-username>/<slug>",   # your track
    "version": "1.0.0",                          # semver
    "display_name": "My Agent",
    "description": "One sentence on the business problem it solves.",
    "author": "Your Name",
    "tags": ["industry", "use-case"],
    "category": "financial_services",            # see registry categories
    "requires_env": [],                          # config, never secrets
}
```

Rules that keep the library healthy:

- **One file per agent.** Self-contained, no sidecar modules.
- **No secrets, keys, tokens, or customer data.** Configuration goes through
  `requires_env`; the file itself must be safe to read in public.
- **State the use case.** The description should tell a business reader what
  problem it solves, not how the code works.

## 3. Submit a pull request

Fork, add `agents/@<your-github-username>/<slug>.py` (or `.md`), open a PR.
CI runs `build_registry.py` on every PR — a malformed manifest fails the
check with the exact reason. On merge:

- the registry rebuilds automatically and your agent appears in the
  [Agent Library](../agents.html) under your publisher track;
- the nightly metrics run seeds a **rating thread** for it in GitHub
  Discussions (upvotes, download tally, and the "how did it go?" signal
  poll), and it starts appearing on the
  [metrics dashboard](../metrics.html) leaderboards and publisher table.

## Aggregated skills

Converting a skill from an outside library into the RAPP ecosystem? Follow
[AGGREGATION.md](AGGREGATION.md) — conversion lands through this same
publisher flow, with attribution and a license check on top.

## RAPP Certified

Once an agent of yours is merged, a maintainer adds you to the public
certification roster and your GitHub username becomes verifiable from the
static API — with a live badge you can put in your own README. See
[CERTIFICATION.md](CERTIFICATION.md).
