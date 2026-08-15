# Contributing an Agent

> ⚠️ **IMPORTANT:** This is an experimental project managed by a v-team from the Artificial Intelligence Business Applications Specialist Team (AIBAST), not an officially supported Microsoft product. Agent templates are starting points that must be customized before production use. AI-generated output may contain errors or unsupported patterns — human review remains important.

## Quick Version

For a standalone, hot-loadable Python agent proposal:

```
1. Fork this repo
2. Create one readable *_agent.py file under an approved publisher path
3. Include: __manifest__ dict in the file
4. Run:    python build_registry.py && python build_rar.py
5. PR:     Open pull request
```

For an AIBAST industry stack, extend the existing stack layout and include the
required Copilot Studio source and stack manifest. Publication remains curated;
a pull request is a proposal, not automatic registry admission.

Public contributions use an AIBAST policy inspired by observable repository
patterns in
[`microsoft/power-cat-skills`](https://github.com/microsoft/power-cat-skills):
public GitHub history, explicit marketplace metadata, maintainer curation,
structured issues, permissions warnings, and globally visible accepted output.
This is a governance precedent, not a shared schema, legal opinion, or guarantee
of equivalent Microsoft approval.

---

## The Portable Runtime Agent Principle

Every independently hot-loadable Python agent is **one `.py` file**. Its package
metadata lives inside that file as a `__manifest__` dict.

```
agents/@publisher/path/my_agent.py
```

A business stack may be multi-file and may contain a Copilot Studio
`manifest.json`, `.mcs.yml` source, knowledge files, and multiple portable Python
agents. The stack manifest does not replace any Python agent's `__manifest__`.

## Namespace Rules

- `@aibast-agents-library/` is the primary curated publisher
- additional publisher namespaces require maintainer approval and provenance review
- One agent per file
- Manifest slugs use kebab-case and must be unique within the publisher namespace
- `@rapp/` is reserved for official base packages
- Content is not imported automatically from the public/global RAR or forks

## Public Contribution and Review

1. Use the structured issue forms for bugs and feature proposals; blank issues
   are disabled.
2. New publishers, top-level programs, external integrations, and substantial
   stack additions require maintainer contact or a structured proposal first.
3. Every pull request requires maintainer review. `CODEOWNERS` identifies the
   current interim review owner; repository branch protection must require that
   review before the public contribution program is considered operational.
4. The public GitHub account and artifact `author` or `publisher` metadata are
   the provenance record.
5. A submission is not guaranteed merge, publication, endorsement, ranking,
   badge issuance, or continued listing.
6. Security vulnerabilities must not be filed publicly; follow `SECURITY.md`.

Before creating any public issue or pull request, remove credentials, internal
URLs, tenant IDs, customer data, proprietary code, personal cloud paths, and
unnecessary PII. Interactive agents must preview the complete public payload and
obtain confirmation before submission.

The checked-in CODEOWNERS file does not enforce itself. Repository administrators
must configure `main` to require pull requests and code-owner approval, and
should add an organization maintainer team when one is available.

## Contributor License Agreement

Most contributions to Microsoft repositories require a Contributor License
Agreement (CLA) confirming that you have the right to, and actually do, grant
the rights needed to use the contribution. When a pull request is submitted,
the [Microsoft CLA service](https://cla.opensource.microsoft.com/) may determine
whether an agreement is required and add a status or comment with instructions.

Do not merge an external contribution until every required CLA check passes.
The rights grant and downstream use are governed by the CLA, this repository's
`LICENSE`, and applicable law.

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
| `community` | Maintainer | Accepted catalog entry that passes schema validation but is not represented as AIBAST-reviewed |
| `verified` | Maintainer | Reviewed against the current repository checklist and tests; no warranty or security guarantee |
| `official` | Core team | Maintained as a first-party compatibility surface; not a support or compatibility warranty |

Accepted submissions may start at `community`. Submission alone does not add an
agent to the catalog; maintainers assign the tier during review.

## Agent Requirements

1. **Single portable file** — everything needed for one hot-loadable runtime agent is in one `.py`
2. **`__manifest__` dict** with all required fields
3. **Inherits `BasicAgent`** — the required runtime base class
4. **Returns a string** — `perform()` always returns `str`
5. **Accepts `**kwargs`** — tool calls may include unexpected arguments
6. **No secrets in code** — use `os.environ.get()` and declare in `requires_env`
7. **Fails explicitly** — handle missing configuration without success-shaped output
8. **No network calls in `__init__`** — keep import and construction safe

## Stack Bundle Requirements

An AIBAST stack may include multiple files when the deployment target requires
them. Keep each independently registered Python agent portable, and validate
stack-level `copilot_studio/manifest.json` source through the repository build.
Do not add a second Python package manifest or per-agent installer.

## AIBAST Skill Requirements Inspired by PowerCAT

If a contribution adds a `SKILL.md`, its YAML frontmatter must include:

- `name`
- `version`
- `description`
- `author`
- `user-invocable`
- `allowed-tools` as a comma-separated least-privilege list

Shared workflow logic belongs in one authoritative shared file. Per-plugin or
per-surface `SKILL.md` wrappers should contain local metadata and reference the
shared workflow rather than copying it. Skills must not contain personal
filesystem paths, OneDrive paths, credentials, tenant identifiers, or
undeclared tool usage.

Prompt-before-action is the safe default. Any skill that creates, modifies,
deletes, sends, publishes, or provisions an external resource must show the
action, target, identity, material content, and reversibility before requesting
human approval.

## Versioning

Use [semantic versioning](https://semver.org/):

- **MAJOR** (2.0.0) — breaking changes to `perform()` signature
- **MINOR** (1.1.0) — new features, new parameters (backward compatible)
- **PATCH** (1.0.1) — bug fixes, documentation

## Validation

Before submitting, run the registry builder locally:

```bash
python build_registry.py
python build_rar.py
python -m pytest tests -q
```

This validates your manifest and ensures the registry builds cleanly.

## PR Checklist

- [ ] Every registered hot-loadable agent is one readable `*_agent.py` file
- [ ] `__manifest__` dict is present with all required fields
- [ ] Agent inherits from `BasicAgent`
- [ ] `perform()` accepts `**kwargs` and returns a non-empty string
- [ ] `python build_registry.py` passes with no errors
- [ ] `python build_rar.py` reproduces the checked-in AIBAST artifacts
- [ ] No secrets, API keys, or customer data in code
- [ ] `requires_env` lists all needed environment variables
- [ ] Any stack-level Copilot Studio manifest and assets are included and valid
- [ ] Any `SKILL.md` declares author, version, and least-privilege `allowed-tools`
- [ ] Public attribution and publisher metadata are accurate
- [ ] Public issue/PR content contains no secrets, tenant data, customer data, or private paths
- [ ] I have the rights needed to submit the contribution under the repository license
- [ ] Any required Microsoft CLA check has passed
