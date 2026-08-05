# Constitution — AIBAST Agents Library (ms-rapp)

> The governing document for this repository. Read it before submitting an
> agent, installing one, or changing anything here.

> ⚠️ **IMPORTANT:** This is an experimental project managed by a v-team from the
> Artificial Intelligence Business Applications Specialist Team (AIBAST), not an
> officially supported Microsoft product. Agent templates are starting points
> that must be customized before production use. See [DISCLAIMER.md](DISCLAIMER.md).

**A rule that cannot be checked is a wish.** Nearly every article below names
the automated gate that enforces it. Run them with
`bash tests/test_library_frontend.sh` and `python3 -m pytest tests -q`. Where an
article states a norm no machine can check, it says so plainly.

---

## Article I — Purpose and identity

This repository is **ms-rapp**: Microsoft's pinned, gated build of the RAPP
platform, and the registry where agent templates are published, discovered,
verified, and installed.

It serves three readers, in this order of obligation:

1. **The person who runs an agent** — who must be able to read it first.
2. **The person who publishes one** — who must be able to do so in one file and
   one pull request.
3. **The autonomous agent** that consumes this catalog headlessly — which must
   be able to answer "what is this and how do I use it" in one fetch.

**One principle above all: the Single File Agent.** Every agent is one file.
The manifest lives inside it. The docstring is the documentation. There is
nothing else.

---

## Article II — The Single File Principle

Non-negotiable. It is the foundation of RAPP and the reason this ecosystem
works.

### An agent is ONE file

```
agents/@publisher/optional_stack/my_agent.py
```

Inside it: a **docstring** (the README), a **`__manifest__` dict** (the package
metadata), a **class inheriting `BasicAgent`**, and a **`perform()` method**
(the entry point).

### There is no

- `manifest.json` — the manifest is `__manifest__` inside the `.py`
- per-agent `README.md` — the docstring is the readme
- per-agent `requirements.txt` — agents use what the platform provides
- multi-file agent — if it cannot fit in one file, it is two agents

**Why.** A single file can be fetched with one HTTP GET, installed with one file
write, read by a model in one context window, and understood by a person in one
sitting. Every other rule in this document is downstream of that.

*Enforced by:* `tests/test_agent_contract.py` — every agent is imported,
instantiated, executed, and run standalone (8 checks × every agent).

---

## Article III — Namespaces and publishers

Every agent lives under a publisher namespace: `@publisher/agent-slug`.

- **Your GitHub username is your publisher handle.** `@yourname` is yours.
- `@aibast-agents-library` — the library's own publisher.
- `@rapp` — reserved for base packages.

Rules:

1. **Your namespace is yours.** No one else publishes under it.
2. **Slugs are lowercase** and match the file path.
3. **No impersonation.** A namespace implying an organization requires proof of
   membership in it.
4. **Publishing is a pull request**, never a privileged upload. The history is
   the audit trail.

*Enforced by:* `build_registry.py` manifest validation on every pull request;
gate **T1** (registry data contract). Process: [docs/PUBLISHING.md](docs/PUBLISHING.md).

---

## Article IV — The manifest

Every agent file contains a `__manifest__` dict. The registry builder extracts
it by **AST parsing — never by importing or executing the file**, so a malformed
or hostile agent cannot run at build time.

```python
__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@publisher/my-agent",
    "version": "1.0.0",
    "display_name": "My Agent",
    "description": "What this agent does, in one sentence a business reader understands.",
    "author": "Your name or team",
    "tags": ["industry", "use-case"],
    "category": "financial_services",
    "requires_env": [],
}
```

| Field | Rule |
|---|---|
| `schema` | `"rapp-agent/1.0"` |
| `name` | `@publisher/slug`, matching the file path |
| `version` | Semver `MAJOR.MINOR.PATCH` |
| `display_name` | Human-readable |
| `description` | One sentence, stating the problem solved — not the implementation |
| `author` | Name or team |
| `tags` | Lowercase keywords |
| `category` | One of the registry's industry categories |
| `requires_env` | **Every** environment variable the agent needs |

The build also derives `_file`, `_size_kb`, `_lines`, and `_sha256` — the last
so a client can verify the bytes it downloaded before executing them.

*Enforced by:* `build_registry.py`; gate **T1**.

---

## Article V — Security and trust

### An agent MUST NOT

- contain secrets, keys, tokens, signed URLs, or credentials of any kind;
- contain customer data, PII, real tenant identifiers, or internal endpoints;
- make network calls in `__init__()` — constructors stay fast;
- execute work on import — only on an explicit `perform()`;
- obfuscate, minify, or encode its logic.

### An agent MUST

- declare every environment variable in `requires_env`;
- read configuration with `os.environ.get()` — never a hardcoded endpoint;
- degrade gracefully when configuration is missing (return an error, don't crash);
- be **fully readable**. Readability is the security model: the single-file rule
  exists so that reading an agent before running it is cheap enough that people
  actually do it.

*Enforced by:* gate **T-SECRETS** (signed trigger URLs, storage keys, tokens,
private keys, real tenant endpoints) across every shippable file; secret
scanning and push protection on the repository; CodeQL on every pull request.

---

## Article VI — The kernel boundary

RAPP is developed in an upstream open-source **kernel**. This repository is a
**distribution** of it. The relationship is the Linux one: the kernel moves
fast, the distribution adopts deliberately, and **RAPP/1 is the standard both
implement**.

1. **Kernel content in this repository is locked.** `rapp_brainstem/**` and the
   installers are recorded by SHA-256. Changing one — including *adding* a file
   to that tree — fails the build.
2. **Fixes flow up, releases flow down.** A defect in kernel content is fixed
   upstream and arrives in a sync pull request. It is never patched here, even
   when patching would be easy. Easy downstream patches are how a distribution
   becomes a fork.
3. **A sync is one commit** that brings the release across, regenerates the
   lock, and passes every gate. The lock moving *is* the record of a sanctioned
   sync.
4. **A red gate is the system working.** Fix the cause; never bypass the gate.

*Enforced by:* gate **T-LOCK** (`rapp/BRAINSTEM-LOCK.json`, two-way —
modification *and* addition both fail). Process: [rapp/SUCCESSION.md](rapp/SUCCESSION.md).

---

## Article VII — The corpus

`rapp/` holds byte-exact mirrors of the canonical RAPP documents at **pinned
commits**: the RAPP/1 specification, the ecosystem specification, the handbook,
and the companion standards.

1. **Provenance is recorded** for every mirrored file — upstream repository,
   pinned commit, SHA-256, license.
2. **Pins never move on their own.** Advancing one is a reviewed pull request.
3. **Freshness is checked, not assumed.** The check verifies local hashes,
   verifies upstream still serves those bytes at the pin, and verifies the
   kernel's own authority file still cites the revision we pin. If the kernel
   re-pins, the check fails asking for a pin bump rather than passing quietly.
4. **Mirrors are never edited.** A mirrored document's vocabulary, claims, and
   errors are upstream's to change.

*Enforced by:* gate **T-CORPUS** and `scripts/corpus_sync.py --check`.
Record: [rapp/ALIGNMENT.md](rapp/ALIGNMENT.md).

---

## Article VIII — Extensions

Capability this distribution originates lives in `rapp/ext/<protocol>-<version>/`
and nowhere else.

1. **Discovery, not registration.** The core discovers extensions; **no core
   file names one** — not in code, not in a docstring, not in generated text.
2. **Namespaced output.** An extension declares the paths it may write and can
   write nowhere else.
3. **Contained failure.** A broken extension is skipped; the core still builds.
4. **Complete uninstall.** Deleting the directory removes its endpoints.
5. **Extensions never touch kernel content or pinned mirrors.**
6. **An extension extends; it never redefines.** If a change belongs in RAPP/1,
   it goes upstream as a protocol proposal instead.
7. **Independently versioned, and offered upstream** once proven here.

The point is not care during merges. The point is that the intersection between
a kernel sync and distribution work is **empty by construction**.

*Enforced by:* gate **T-EXT-ISOLATION** — every extension is moved aside and the
core endpoints must be byte-identical, a hostile extension must not crash the
build, and a namespace escape must be refused. Pattern:
[rapp/ext/PATTERN.md](rapp/ext/PATTERN.md).

Current extensions: `ms-rapp-badge/1.0` (verifiable achievement badges),
`ms-rapp-brain/1.0` (the documentation vault).

---

## Article IX — The static API

Every machine-readable surface is a static JSON file generated into the
repository under `api/v1/`, following `rapp-static-api/1.0`.

1. **One build step** regenerates everything; nothing generated is hand-edited.
2. **Stable-write.** A rebuild with no input change produces no diff — so a
   scheduled build never commits noise, and "artifacts are current" can be a
   gate.
3. **Versioned and frozen.** `api/v1/` keeps its shape. A breaking change opens
   `api/v2/` and v1 keeps serving; static files cost nothing to keep.
4. **Public and read-only.** No key, no quota, CORS-open. Never send it a secret.
5. **Pinnable.** A raw URL with a commit SHA is immutable forever.

*Enforced by:* gate **T-API** (contract, stable-write) and the CI freshness
check. Reference: [docs/API.md](docs/API.md).

---

## Article X — Agent-first access

An autonomous reader is a first-class user of this repository, not an
afterthought.

1. **One fetch answers the basics.** `api/v1/agent.json` states what this is,
   the conventions, task recipes, and the rules of the road.
2. **`llms.txt` follows the convention** and every link it makes must resolve;
   `llms-full.txt` inlines the documentation for a reader that would rather pay
   one fetch than forty.
3. **A negative answer is an answer.** A `404` from a verification endpoint
   means *not certified* — never an error to retry. Documents say so explicitly.
4. **Unknown fields are ignorable.** Documents gain fields without a major
   version bump; a reader must not refuse on an unrecognized member. (RAPP/1 §8's
   rule, applied to every surface here.)
5. **`AGENTS.md`** tells an agent working *on* this repository what will fail
   the build.

*Enforced by:* gate **T-AGENTFIRST** — including that every link in `llms.txt`
points at a file that exists.

---

## Article XI — Verification and certification

Publishers who ship reviewed work earn badges that **anyone can verify from the
static API**, with no login.

1. **Two hand-edited inputs** — the badge catalog and the roster. Everything
   else is derived.
2. **An award is public.** Each carries the discussion thread where it was
   granted, so it can be congratulated or contested in the open.
3. **Revocation retains the entry.** A withdrawn badge sets status to revoked;
   the record is **never deleted**, so the endpoint keeps resolving and answers
   `certified: false`. A `404` cannot be told apart from an outage — a
   verification system whose *no* is indistinguishable from its *unreachable*
   verifies nothing.
4. **An award naming an unknown badge is ignored**, never rendered from guessed
   metadata.
5. **Certification is not endorsement.** It states that a submission met this
   library's review bar — nothing about the person, their employer, or their
   other work.

*Enforced by:* gates **T-CERT** and **T-WALL**, which probe the revocation path
end to end. Process: [docs/CERTIFICATION.md](docs/CERTIFICATION.md).

---

## Article XII — Aggregation of outside work

The library indexes skills from other libraries so that duplicate solutions can
be compared and the best surfaced.

1. **Index, never mirror.** The crawler stores catalog metadata and a link to
   the origin. Content is not copied.
2. **License first.** An unverified upstream license means index-and-link only.
   Conversion requires a compatible license or the author's permission,
   recorded in the pull request.
3. **Conversion is a normal publisher pull request**, carrying attribution.
4. **Gates decide prominence** — quality, usability, and effectiveness for the
   stated use case. A gated, converted entry outranks a merely popular one by
   construction.

*Enforced by:* gate **T3** (index-only; the crawler's output is checked for the
absence of content fields). Design: [docs/AGGREGATION.md](docs/AGGREGATION.md).

---

## Article XIII — Documentation

1. **Documentation is plain Markdown in `brain/`**, with frontmatter and
   wikilinks. The same folder opens in a notes client and reads in a browser.
2. **Indexes are derived, never hand-maintained.** A hand-written index drifts,
   and a drifted index is worse than none. A note does not know who links to it;
   the build computes that.
3. **Dangling links are reported, never invented, never fatal.**
4. **Claims in documentation are gated** where a gate is possible — a document
   that asserts something the repository does not do is a failing test, not a
   style problem.

*Enforced by:* gates **T-BRAIN**, **T-DOCS2**, **T-DISCLAIMER**, **T-TERMS**.

---

## Article XIV — Telemetry and privacy

1. **Public metrics are anonymous aggregates** from public APIs, with the
   methodology and its distortions stated on the page.
2. **The internal event contract carries role, never person** — and prompts,
   responses, customer data, document contents, and individual identity are
   **structurally impossible** in the payload, not merely discouraged.
3. **The two pipelines are disjoint.** Business identifiers never enter this
   repository or the public dashboard.
4. **Nothing a user runs is sent here.** Local execution stays local; the one
   disclosed exception is the browser sign-in proxy, named in the disclaimer.

*Enforced by:* gate **T-TELEMETRY** (closed contract, prohibited-field
denylist). Contract: [docs/TELEMETRY.md](docs/TELEMETRY.md).

---

## Article XV — RAPP data exhaust

Building this platform produces a by-product: the **shape** of how the work
actually went. Which review found the real defect and which found noise. Which
instruction had to be repeated. Which rename broke an installer. Which question
a newcomer asks first. We call this **rapp data exhaust**, and treating it as
waste is the most expensive habit available to us.

**The premise.** Exhaust is a **negative of the shape that emitted it**. The
thing most worth modelling — actual intent, the real constraint, the boundary
between fine and absolutely not — is rarely written down, because to whoever
holds it, it is obvious. But it presses an impression into everything it
produces: a correction is a cast of the boundary that was crossed, a gate is a
cast of a defect that once got through, a repeated instruction is a cast of
something the system keeps failing to infer. Read the negative and the positive
is recoverable — at higher fidelity than a description, because a description is
what someone remembered to say and a negative is what actually happened.

A maintainer should therefore not have to specify what the exhaust already
carries. Reading it is how ms-rapp improves without being told.

**Use it or lose it.** Much of the richest exhaust is perishable. A session
transcript is discarded, a rationale evaporates when the pull request merges,
the reason a gate exists is obvious for a week and mysterious for a year. What
is not captured while it is warm is not recoverable later.

Therefore:

1. **A lesson becomes an artifact.** When exhaust teaches something, it lands as
   a durable thing — a gate, a note in `brain/decisions/`, a rule in this
   document — not as a remembered preference. A defect that produced a gate
   cannot recur silently.
2. **Prefer the gate to the reminder.** If a lesson can be machine-checked,
   checking it is the correct way to remember it.
3. **Record the why, not only the what.** A decision note states what was
   rejected and why; that is the part which stops the question being reopened.
4. **The boundary is absolute.** Exhaust is mined for *shape and lesson*. Raw
   transcripts, customer content, private-estate detail, and personal data
   **never** become public artifacts — only the generalized lesson does. The
   two-worlds rule (Article XIV) governs; when in doubt, the lesson ships and
   the source does not.
5. **Exhaust flows to whoever it teaches.** A lesson about the protocol goes
   upstream to the kernel; a lesson about this build stays here.

*Enforced by:* the practice of Article XVII — an amendment that adds a rule adds
its gate in the same change. Definition: [`brain/concepts/rapp-data-exhaust`](brain/concepts/rapp-data-exhaust.md).

---

## Article XVI — Language, licensing, and honesty

1. **Say what a thing does, not what it evokes.** Internal vocabulary from
   upstream does not ship on this distribution's own surfaces.
2. **No overclaims.** "Production-ready", "guaranteed", and "enterprise-grade"
   are not available to a public preview provided as is. Where this repository
   once promised guarantees, it now describes behavior.
3. **MIT, with the third-party carve-out stated.** Mirrored corpus files ship
   under their upstream licenses, recorded in
   [rapp/THIRD-PARTY-NOTICES.md](rapp/THIRD-PARTY-NOTICES.md).
4. **The marks belong upstream.** This distribution claims none
   ([rapp/ATTRIBUTION.md](rapp/ATTRIBUTION.md)).
5. **Confident, never defensive.** The register is a host explaining their
   house — not an apology, and not a sales pitch.

*Enforced by:* gates **T-TERMS**, **T-DISCLAIMER**, **T-CAT** (Microsoft
open-source compliance set), **T-IDENT** (a display-name substitution must never
corrupt an identifier — the gate that exists because a rename once broke the
Windows installer).

---

## Article XVII — Release engineering and amendment

1. **`main` is production.** The install one-liners read from it, so it is
   always in a working state.
2. **Every change passes the gates** before promotion: contract tests, the
   release-gate suite, corpus integrity, artifact freshness, and a headless
   render of the pages.
3. **Verification is exercise, not inference.** "It works" means the live
   artifact was driven and the result observed — a green build is not evidence.
4. **Generated artifacts are committed**, and stale ones fail CI.
5. **Rollback is a revert.** Every ring is a git ref and a static deploy.

Amend this document by pull request. An amendment that adds a rule **should add
the gate that enforces it in the same change**; an amendment that removes one
should say why it stopped being true. If this document and the repository ever
disagree, **the repository is the fact and this document is the bug** — fix it
here in the same pull request.

The spirit of this document is **simplicity**: single file, single source of
truth, and no claim that cannot be checked.

Detail: [rapp/ALM.md](rapp/ALM.md).

---

*Originally ratified at repository creation on the Single File Principle.
Amended for the v1 public preview to cover the kernel boundary, the pinned
corpus, extensions, the static API, agent-first access, verification,
aggregation, documentation, telemetry, data exhaust, and the gates that enforce
all of it. The single file is still the law.*
