# AIBAST Agents Library Constitution

> **Constitution version 2.0 — proposed 2026-08-15**
>
> This replacement amendment supersedes the registry-only constitution drafted
> on 2026-03-18. It becomes governing when merged.

> **Important:** This is an experimental project managed by a v-team from the
> Artificial Intelligence Business Applications Specialist Team (AIBAST). It is
> not an officially supported Microsoft product. Templates and generated
> artifacts are starting points that require human review before production use.

---

## Preamble

The original constitution correctly protected one important property: a
hot-loadable RAPP agent should remain portable, readable, and installable as one
Python file. The repository has since become more than an agent registry. It now
contains the local Brainstem kernel, a curated business agent library, Copilot
Studio stack source, Azure deployment paths, the Twin and workshop system,
installers, a separate AIBAST RAR, metrics, and Microsoft governance files.

This amendment keeps the portability principle while defining the boundaries,
authorities, and generated artifacts needed to prevent those surfaces from
silently drifting apart.

The governing principles are:

1. **Local first.** A user can begin with the Brainstem on a device they control.
2. **Engine, not lock-in.** Tiers are independently useful and adoption is
   progressive, not mandatory.
3. **Curated, not federated by default.** This library is the business-focused
   AIBAST catalog, separate from the public/global RAR.
4. **Portable where portability matters.** Every independently hot-loadable
   Python agent remains a single-file unit; stacks and deployment source may be
   multi-file.
5. **One authority per fact.** Generated files, mirrors, versions, and runtime
   behavior have named source authorities and automated drift checks.

---

## Article I — Purpose and Scope

This repository is the stable Microsoft downstream for the RAPP stack and the
canonical home of the AIBAST Agents Library. It owns:

Here, **stable downstream** describes a maintained ownership and sync boundary.
It does not imply product support, warranty, service level, or production
readiness.

- the local RAPP Brainstem kernel and browser in `rapp_brainstem/`;
- the curated AIBAST agent and industry-stack source in
  `agents/@aibast-agents-library/`;
- the AIBAST registry and RAR build chain;
- the Twin missions, playbooks, products, mutations, and workshop experience;
- the Azure and CommunityRAPP cloud paths;
- Copilot Studio and Power Platform source and release artifacts;
- the public documentation, installers, governance, and release automation.

This repository is **not**:

- a mirror of the public/global RAR;
- an automatic import of every public RAPP agent;
- a general-purpose consumer SaaS product;
- an authorization system for customer tenants or SharePoint;
- a place for secrets, customer data, or proprietary business logic.

Infrastructure, reference implementations, workshops, and governed distribution
belong here. Unrelated end-user application features do not.

---

## Article II — System Topology

The repository teaches and ships three independently useful tiers:

| Tier | Name | Purpose | Primary authority |
|---|---|---|---|
| 1 | **Brainstem** | Local Flask server, GitHub Copilot inference, agent orchestration, storage shims, and browser UI | `rapp_brainstem/` |
| 2 | **Cloud body** | Azure deployment and persistent cloud execution. The AIBAST Spinal Cord and the CommunityRAPP/Hippocampus installer are parallel paths, not dependencies of one another | `azuredeploy.json`, `deploy.*`, `rapp_ai/`, `community_rapp/` |
| 3 | **Nervous System** | Copilot Studio, Teams, and Microsoft 365 distribution | Copilot Studio stack source and `MSFTAIBASMultiAgentCopilot_*.zip` |

Rules:

1. Tier 1 must remain useful without Tier 2 or Tier 3.
2. The Brainstem and CommunityRAPP installers are separate products and must not
   cross-contaminate paths, state, or upgrade behavior.
3. Cloud and Power Platform assets may depend on Microsoft services; local core
   chat must not require a model-provider API key beyond GitHub Copilot access.
4. Anatomy names explain the architecture; file paths and APIs define the
   implementation.

---

## Article III — Artifact Classes and the Single-File Rule

### 1. Hot-loadable runtime agent

Every Python file published as an independently installable Brainstem agent must:

1. be one readable `.py` file;
2. contain one literal, module-level `__manifest__` dictionary;
3. define a `BasicAgent` subclass;
4. expose a `perform(..., **kwargs)` entry point;
5. return a string suitable for the model tool loop;
6. avoid import-time execution beyond safe declarations and initialization.

The docstring is the primary documentation for that portable Python unit.
Per-agent package installers and opaque payloads are prohibited.

### 2. Stack bundle

A business stack is not one runtime agent. It may contain:

- multiple independently registered Python agents;
- Copilot Studio `manifest.json` files;
- `.mcs.yml` behavior, action, knowledge, and orchestration source;
- knowledge documents, schemas, deployment metadata, and workshop mappings.

Each registered Python agent inside a stack still obeys the single-file runtime
contract. A stack-level `manifest.json` is allowed and does not replace the
Python agent's `__manifest__`.

### 3. Kernel, deployment, and enablement artifacts

The Brainstem server, installers, ARM templates, Power Platform solutions,
workshops, Twin playbooks, static sites, and governance documents are not agents
and are not subject to the single-file agent rule.

The portable agent is the law **for portable agents**, not a false description
of the entire repository.

---

## Article IV — Namespace and Curation

Agent names use `@publisher/kebab-case-slug`.

- `@aibast-agents-library` is the primary curated publisher in this repository.
- `@rapp` is reserved for shared base packages when explicitly approved.
- Any additional publisher namespace requires maintainer approval and provenance
  review before it enters the AIBAST catalog.

A pull request is a proposal, not an entitlement to publication. The maintainers
decide whether an agent belongs in this business-focused library, what quality
tier it receives, and whether it is compatible with AIBAST workshops and
governance requirements.

No agent is imported merely because it exists in the public/global RAR, a fork,
or another repository. Cross-repository content is reviewed individually.

---

## Article V — Manifests, Quality, and Compatibility

The registry builder statically extracts `__manifest__` with Python AST parsing.
It must not import or execute agent code during catalog generation.

Required manifest fields are defined by `build_registry.py`. At constitution
version 2.0 they include:

| Field | Rule |
|---|---|
| `schema` | `rapp-agent/1.0` |
| `name` | `@publisher/kebab-case-slug` |
| `version` | Semantic version `MAJOR.MINOR.PATCH` |
| `display_name` | Non-empty human-readable name |
| `description` | Non-empty searchable description |
| `author` | Accountable person or team |
| `tags` | Non-empty strings |
| `category` | Non-empty catalog category |

Optional `quality_tier`, `requires_env`, and `dependencies` values must satisfy
the builder's schema. Accepted quality tiers are:

| Tier | Meaning |
|---|---|
| `community` | Schema-valid proposal; not represented as AIBAST-reviewed |
| `verified` | Reviewed and tested for this curated library |
| `official` | Maintained as a core first-party compatibility surface |

Current AIBAST catalog entries target Python 3.11+, `BasicAgent`, the local
Brainstem and/or RAPP Azure execution, and model-independent tool behavior.
Agents must not hardcode a model provider or deployment name unless that
specific integration is their declared purpose.

---

## Article VI — Source Authority and Generated Artifacts

Every operational fact has one authority:

| Concern | Authority | Derived or mirrored outputs |
|---|---|---|
| Repository scope and governance | `CONSTITUTION.md` | `README.md`, `CLAUDE.md`, contributor guidance |
| Brainstem runtime and API behavior | `rapp_brainstem/brainstem.py` plus tests | `rapp_brainstem/index.html`, API documentation |
| Brainstem release version | `rapp_brainstem/VERSION` | installer comparisons, `frontier-channel.json`, UI version |
| Agent metadata | Literal `__manifest__` in catalog Python source | `registry.json` |
| Installable AIBAST RAR catalog | `registry.json` plus source agent bytes | `rar/registry.json` |
| Copilot Studio stack names | Stack `copilot_studio/manifest.json` files | `twin/stack_names.json` |
| Frontier kernel broadcast | `rapp_brainstem/VERSION` and channel policy in `build_rar.py` | `rapp_brainstem/frontier-channel.json` |
| Ratings and discussion map | Canonical AIBAST GitHub Discussions | `rar/discussions.json`, `rar/ratings.json` |
| Download, traffic, and community metrics | GitHub APIs | `rar/downloads.json`, `rar/traffic.json`, `rar/community.json` |
| Badge completion proof, when enabled | `docs/badge-program.md`, the canonical repository fork, and the accepted course-completion GitHub issue and workflow result | generated static badge and profile progress under `docs/badges/` |
| Public contribution and support policy | Article X, `CONTRIBUTING.md`, `SECURITY.md`, and `SUPPORT.md` | CODEOWNERS, structured issue forms, pull request template, agent-created issue previews |
| Published installers | Root `install.*` files | byte-identical `docs/install.*` mirrors |

Rules:

1. Generated files are never hand-edited as the primary fix. Change their source
   or builder and regenerate them.
2. A prose document may summarize an authority but may not silently redefine it.
3. A conflict between an authority and a derived document is a defect. The
   authority describes current operational truth until the conflict is repaired;
   this does not authorize code to evade governance.
4. A pull request that creates a new top-level governed surface must update this
   table and its drift tests in the same change.

---

## Article VII — The AIBAST RAR

The AIBAST RAR is a curated registry hosted by this repository for AIBAST
business, industry, workshop, and deployment requirements. It is completely
separate from the public/global RAR.

The following invariants are constitutional:

1. `rar/registry.json` identifies `microsoft/aibast-agents-library` and the
   `AIBAST RAR` instance.
2. `build_rar.py` derives it only from this repository's validated
   `registry.json` and agent bytes.
3. The Brainstem browser uses an immutable `RAR_REVISION` from this repository;
   it has no fallback to a public/global RAR.
4. Every downloadable Python file carries a SHA-256 digest and a
   collision-safe `_install_filename`; the browser and server verify integrity.
5. Live ratings, discussions, and download metrics may move independently of
   the immutable code pin, but they remain hosted by the AIBAST repository.
6. Upvotes use canonical AIBAST GitHub Discussions. They do not create a second
   private scoring system.

Publishing a new immutable catalog requires rebuilding, committing the generated
artifacts, and updating the Brainstem RAR revision through normal review.

---

## Article VIII — Downstream Sync, Forks, and Ownership

This repository is a downstream, not a wholesale mirror. Shared Brainstem work
may flow from an upstream RAPP source, but syncs must preserve AIBAST-owned
surfaces, including:

- `agents/@aibast-agents-library/`, `registry.json`, and the builders;
- `rar/`, `twin/`, `rapp_ai/`, and the workshop;
- root and `docs/` sites, installers, governance, workflows, and release assets;
- the AIBAST RAR identity and pinning inside the Brainstem.

Only repository-identity URLs may be rewritten mechanically. Content repository
references, including CommunityRAPP dependencies, require individual review.
No global search-and-replace may convert one ecosystem into another.

Forks may create independent distros. A fork may:

- follow the canonical frontier Brainstem channel;
- pin an immutable channel or release;
- disable the channel and diverge.

A fork that changes catalog identity, governance, or curated content must not
represent itself as the canonical AIBAST library. Forks are distribution and
contribution mechanisms. For the badge program defined in
`docs/badge-program.md`, forking the canonical
`microsoft/aibast-agents-library` repository is the explicit first-gate opt-in
and public account-linkage proof. It consents to badge-program submission and
eligibility review, not to publication of course results. Public badge or
progress display still requires the later exact-payload confirmation in Article
IX. The fork proves account-level submission, not course completion, badge
eligibility, legal identity beyond GitHub, leaderboard placement, ranking, or
continued display. A generic star, subscription, or fork of another repository
does not authorize certification, SharePoint access, or any customer tenant
action.

---

## Article IX — Security, Privacy, and Human Approval

Agents and repository artifacts must not:

- contain secrets, tokens, credentials, customer data, or unnecessary PII;
- execute arbitrary or obfuscated payloads on import;
- make hidden network calls during construction;
- return success-shaped responses after a failed operation;
- silently install, upload, publish, or grant tenant access.

Agents must:

- declare required environment variables and dependencies truthfully;
- handle missing configuration explicitly;
- use bounded network timeouts and surface failures;
- keep code readable and reviewable;
- perform external side effects only through an explicit user or agent action.

Users must review Python before local execution. Verified catalog status reduces
risk; it does not make arbitrary code safe or production-ready.

If course enrollment, public badges, or leaderboards are added:

1. participation and GitHub linkage must be explicit opt-in;
2. under `docs/badge-program.md`, the public fork of
   `microsoft/aibast-agents-library` is the participant's consent to enter the
   badge submission and eligibility-review process;
3. the fork owner and public fork relationship are the public evidence linking
   the submission to that GitHub account;
4. the fork is only the first gate: maintainers may approve, reject, suspend, or
   remove badge and leaderboard entries under `docs/badge-program.md`;
5. leaderboard inclusion and retention are not rights created by the fork;
6. final agreement/signoff status may be automated into the roster and remains
   required before final official badge linkage;
7. the badge-enrollment fork does not authorize tenant or SharePoint access;
8. SharePoint library access remains a manual maintainer decision;
9. the UI must not claim Credly issuance unless an authorized Credly issuer
   actually issued the credential.

### Badge completion gate

The badge flow follows the public interaction policy in Article X. In the
PowerCAT reference the public artifact is a curated `SKILL.md` inside an
organization-attributed plugin marketplace. AIBAST additionally requires
consistent contributor provenance; its public artifact is the accepted
course-completion record and generated badge-progress profile linked to the
fork owner's GitHub account.

The public badge program may use this learning-oriented completion flow:

1. The participant submits their course achievements at the end of the course.
2. The submission includes a three-question knowledge check. It is intentionally
   open-book: participants may revisit course material, verify answers, and retry.
   The goal is learning and demonstrated comprehension, not closed-book recall.
3. The initiating course UI evaluates the knowledge check and prepares a
   structured public completion payload containing only the result and approved
   evidence summary, never the raw answers.
4. The participant previews and explicitly confirms that exact public payload.
5. A background GitHub issue API validates and creates or updates the structured
   completion issue for the linked GitHub account and course.
6. The issue event triggers the governed badge workflow.
7. The workflow validates the fork linkage, required achievement evidence,
   agreement status, and knowledge-check result.
8. An accepted workflow result records that the participant passed the course
   completion gate. Raw quiz answers and unnecessary personal data must not be
   published in the issue, workflow artifact, or badge metadata.
9. The event-driven profile job regenerates that participant's static GitHub
   Pages profile, badge counts, course progress, and approved public badges on
   the global AIBAST badge site as close to real time as practical.
10. A nightly scheduled reconciliation, also available through manual workflow
   dispatch, recomputes every public badge profile from the authoritative fork,
   issue, agreement, and completion records.
11. The nightly true-up is idempotent and repairs missed, delayed, or failed
   individual profile updates so badge progress remains whole and current.
12. Generated badge pages are derived views, not the completion authority. They
   may be rebuilt or removed under the program's published moderation rules.

---

## Article X — PowerCAT-Aligned Public Interaction Policy

This article makes AIBAST's approved policy by adapting observable public
repository interaction patterns from
[`microsoft/power-cat-skills`](https://github.com/microsoft/power-cat-skills),
reviewed at commit `33bc38456abb83f27daad968b748c8085f2a78ef` on 2026-08-15.
The reference is a governance precedent, not a runtime dependency, schema
dependency, legal opinion, or guarantee of equivalent Microsoft approval.

The verified reference patterns include organization-owned marketplace and
plugin metadata, public GitHub history, team review through CODEOWNERS,
structured issue forms, explicit permission warnings, and shared workflow
templates. Individual `author` metadata exists in some reference skills but is
not consistent; AIBAST therefore treats consistent contributor provenance as a
stricter local requirement.

The AIBAST interaction shape is:

1. a contributor acts through a public GitHub account;
2. the submitted artifact carries explicit author or publisher attribution;
3. maintainers curate and approve publication;
4. accepted artifacts are globally visible and remain attributable;
5. maintainers retain correction, suspension, deprecation, and removal authority.

### Public contribution lifecycle

1. Public contributions are proposals. Submission creates no right to merge,
   publication, endorsement, badge issuance, ranking, or continued listing.
2. New publishers, top-level programs, external integrations, and substantial
   stack additions require maintainer contact or a structured proposal before
   implementation.
3. Every contribution records the public GitHub identity and the artifact's
   accountable `author` or `publisher`. Repository ownership may remain AIBAST
   while individual provenance remains visible.
4. Published marketplace or registry entries explicitly enumerate their name,
   version, description, source, repository, license, category, tags, and
   included artifacts. Files are not published merely because they exist.
5. Every path requires maintainer review through CODEOWNERS or equivalent
   required-review branch protection before the public contribution program is
   treated as operational.
6. Contributors must have the rights needed to submit their work and complete
   any Microsoft Contributor License Agreement check required by the canonical
   repository before merge.
7. Rights grants and liability are governed by the applicable CLA, `LICENSE`,
   and applicable law. Merge does not imply Microsoft endorsement of the
   contributor or downstream use.

### Public issue and API lifecycle

Public issue creation, whether initiated by a person, agent, browser, or
background API, follows this sequence:

1. warn that the destination is public and prohibit credentials, internal URLs,
   tenant IDs, customer data, proprietary code, and unnecessary personal data;
2. identify the affected component and version from authoritative metadata when
   possible;
3. gather only structured fields needed to reproduce, review, or validate the
   request;
4. show the complete proposed public payload and obtain explicit confirmation
   before an interactive agent creates it;
5. create the issue through an authenticated GitHub API or `gh` operation;
6. return the issue URL and preserve it as the workflow event or audit record.

Blank public issues may be disabled. Bug reports and feature requests use
structured issue forms. Security vulnerabilities never use public issues and
follow `SECURITY.md`.

For a background issue API, the initiating UI or agent still presents the exact
public payload and obtains confirmation before the first issue is created or a
material public update is submitted. The server validates the schema and
prohibited-data rules again. Scheduled reconciliation may update derived state
within the previously approved scope without repeating consent.

### Permissions and approval prompts

1. Prompt-before-action is the safe default for file writes, shell execution,
   network calls, external resource changes, and publication.
2. PowerCAT-inspired `SKILL.md` contributions declare `allowed-tools` as a
   comma-separated least-privilege list. Undeclared tool use is a blocking
   defect.
3. Narrow allowlists are preferred over broad auto-approval. Granting full
   auto-approval gives an agent the effective access of the running user and
   must be described as such.
4. Actions that create, modify, delete, send, publish, or provision external
   resources require a human-readable preview containing the action, target,
   identity, material content, and reversibility before execution.
5. Environment or diagnostic collection requires explicit user approval and
   must be scrubbed before public submission.

### Shared workflows and generated wrappers

Shared interaction logic is written once in an authoritative workflow or
template. Per-surface wrappers contain only their local metadata and reference
the shared source. Generated wrappers are regenerated with their template in the
same change. Duplicated workflow logic that can drift is prohibited.

### Public safety, support, and liability boundaries

1. Public artifacts must not contain personal filesystem paths, personal cloud
   storage paths, credentials, tenant identifiers, internal-only links, or
   customer-confidential content.
2. Public output must distinguish customer-shareable content from restricted or
   internal-only content; outbound sends require recipient and content preview.
3. The repository uses the MIT license in `LICENSE`, including its "as is"
   warranty and liability terms. Required copyright and permission notices stay
   with copies or substantial portions.
4. Microsoft names, logos, and trademarks follow Microsoft's Trademark & Brand
   Guidelines. Modified forks must not imply sponsorship or canonical status.
5. Public conduct follows the Microsoft Open Source Code of Conduct. Support,
   bugs, feature requests, and security reports have explicit, non-conflicting
   routes.

### AIBAST enforcement exceeds the reference where needed

The PowerCAT shape is a floor, not permission to copy known gaps. AIBAST
requires:

- automated validation and drift checks in addition to human review;
- complete support guidance rather than placeholder text;
- consistent attribution, version, license, and tool-permission metadata;
- issue forms that reference only current authoritative components;
- no developer-local paths or personal storage references;
- PR checklists and source-authority updates for topology changes;
- idempotent recovery workflows for generated public state.

The checked-in CODEOWNERS entry is an interim review principal. The public
contribution and badge programs are not technically review-enforced until a
repository administrator configures a `main` ruleset or branch protection that
requires pull requests and code-owner approval. An organization team should
replace or join the personal owner when the canonical repository grants that
team access.

---

## Article XI — Release and Change Control

1. `main` is production because the public installers consume it.
2. Development occurs on reviewed feature or fix branches.
3. Brainstem releases update `rapp_brainstem/VERSION`.
4. Root installers are sacred distribution surfaces. Changes require syntax,
   rollback, upgrade, and fresh-install verification; their `docs/` mirrors must
   remain byte-identical.
5. The Brainstem and CommunityRAPP installer paths remain independent.
6. Generated registry and metrics bot commits are allowed only for their
   declared files and workflows.
7. Security reports follow `SECURITY.md`, not public issues.

---

## Article XII — Amendments and Drift Control

An amendment requires a pull request that:

1. states the observed drift or new requirement;
2. identifies affected authority rows and invariants;
3. updates directly conflicting documentation;
4. adds or updates an automated check where the invariant is machine-testable;
5. records the constitution version and amendment date.

The constitution must be reviewed whenever a change:

- adds or removes a top-level product surface;
- changes tier boundaries or installer ownership;
- changes registry, RAR, Twin, or generated-artifact authority;
- changes fork/channel behavior;
- introduces enrollment, certification, or external-access automation.

At minimum, CI must continue to prove:

- registry and RAR outputs match their sources;
- generated install filenames and digests are valid;
- installer mirrors are byte-identical;
- the Brainstem remains pinned to the AIBAST RAR;
- governance documents retain the current topology and scoped single-file rule.

---

## Amendment Record

### Version 2.0 — Scope and Authority Amendment (proposed 2026-08-15)

- Replaced the obsolete claim that the repository is only an agent registry.
- Scoped the single-file rule to independently hot-loadable Python agents.
- Recognized multi-file Copilot Studio stacks, Twin/workshop assets, cloud tiers,
  installers, metrics, and governance.
- Declared the AIBAST RAR independent from the public/global RAR.
- Added source-authority, generated-artifact, downstream-sync, fork-channel, and
  human-approval invariants.
- Adopted the PowerCAT-aligned public contribution, issue, attribution,
  permission, support, and liability interaction policy.
- Required machine-testable drift controls for future topology changes.

---

*Local first. Curated by design. One authority per fact.*
