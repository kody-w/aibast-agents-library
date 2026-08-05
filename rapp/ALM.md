# ALM — application lifecycle for a worldwide-stable ms-rapp/1

The kernel already proved the ring model (canary → nightly → alpha → beta →
stable). The LTS runs a smaller train with harder gates. This is the full
blueprint: what runs today, what the admin turns on, and the planned
topology.

## 1. Ring topology

```
kernel stable (kody-w) ──weekly sync PR──▶ LTS canary ──▶ LTS nightly ──▶ LTS main (public)
                                          (branch/repo)   (scheduled)      microsoft.github.io
```

| Ring | Where | Cadence | Audience |
|------|-------|---------|----------|
| **canary** | planned: `microsoft/aibast-canary` repo (preferred — own Pages, own Discussions sandbox, blast-radius isolation) or a `canary` branch here with fork-Pages preview | on every merge | maintainers |
| **nightly** | `nightly` branch, rebuilt from canary by scheduled workflow; prerelease tag `vX.Y.Z-nightly.N` | daily | early adopters |
| **LTS (main)** | this repo, `main` | promoted only when all gates green | the world |

Staging today: the kody-w fork (`kody-w/aibast-agents-library`) + its Pages
serves as the de-facto canary until the canary repo decision lands.

## 2. Promotion gates (every ring hop, no exceptions)

1. **Full test suite** — `tests/test_library_frontend.sh` (local mode): data
   contracts, scripts, pages, headless render, T-CLEAN, T-LOCK, T-CORPUS,
   T-DOCS2. Red = no promotion.
2. **Link audit** — the full-repo dead-link/outside-link scan; the
   clean-break allowlist is the only tolerance.
3. **Corpus integrity** — `python3 scripts/corpus_sync.py --check`
   (upstream mode): every mirror hash-matches its pin AND upstream still
   serves those bytes.
4. **Stable-write builds** — `build_registry.py`, `scripts/build_api.py`
   twice in a row must produce zero diffs the second time.
5. **Live verification after deploy** — the suite's `live` mode against the
   ring's Pages URL + headless drive of gallery and metrics.
6. **Brainstem lock** — T-LOCK green, or the PR is a sanctioned kernel sync
   that regenerates `BRAINSTEM-LOCK.json` in the same commit.

## 3. Scheduled automation (CI)

| Workflow | Trigger | Job |
|----------|---------|-----|
| `build-registry.yml` (live) | push touching agents | registry + static API rebuild, stable-write commit |
| `metrics.yml` (live) | daily 05:40 UTC + dispatch | skill-source crawl, Discussions seed/tally/fetch, metrics snapshot, API mirror |
| `corpus-check.yml` (live) | weekly + dispatch + corpus PRs | `corpus_sync.py --check`: local integrity, upstream pin immutability (404/410/451 = failure), and authority freshness (kernel re-pin = failure, "pin-bump PR needed"); scheduled failures open a `corpus-drift` issue — observe, never auto-bump |
| upstream sync (add, admin) | weekly | diff the kernel stable release tag vs LTS; open the upstream sync PR skeleton for human review |

## 4. Repository protections (admin, microsoft repo)

- **Branch protection on `main`**: PRs only, required checks = the gate
  workflows, no force-push, linear history.
- **CODEOWNERS**: `rapp_brainstem/**`, `install.*`, `rapp/**` require the
  LTS maintainer + (for kernel files) sign-off tied to a sync PR.
- **Secret scanning + push protection: ON** — required on every ring.
- **Actions permissions**: default `GITHUB_TOKEN` read-only except the two
  workflows that commit (registry, metrics); `METRICS_TOKEN` fine-grained,
  single-repo, Administration:read only.
- Dependabot/security updates for Actions pins.

## 5. Versioning & releases

- Library releases: SemVer tags (`v1.0.0` = public preview GA of the
  gallery/metrics/API/corpus surface). GitHub Release notes enumerate: RAPP/1
  revision pinned, brainstem VERSION, corpus manifest hash.
- The engine (`rapp_brainstem/VERSION`) and RAPP/1 revision only move via
  sync/pin-bump PRs (see SUCCESSION.md) — a library release never bumps
  them implicitly.
- Extension specs (`rapp/ext/`) are versioned in their directory name. A
  breaking change opens a new directory; the old major keeps its spec and its
  endpoints, because someone's README renders them.
- API stability: `api/v1/` is frozen shape; breaking changes open `api/v2/`
  and keep v1 serving (static files cost nothing — the rapp-static-api rule).

## 5b. Usage telemetry (business KPIs, separate from public metrics)

Every AIBAST TA tool emits the `aibast.tooling.v1` **ToolInteractionEvent**
(schema in `schemas/`, emitter in `scripts/telemetry.py`, contract in
`docs/TELEMETRY.md`): six uniform verbs, correlation ID as the engagement
spine, MSX opportunity ID mandatory for L3/L4 credit, role-never-person.
Events flow only to the internal collector (`AIBAST_TELEMETRY_ENDPOINT`);
prompts/responses/customer data/document contents/user identity are
structurally impossible in the payload, and business identifiers never land
in this repo or the public dashboard. Public `state/metrics.json` remains
anonymous aggregate only — the two pipelines are disjoint by design.

## 6. Security & supply-chain posture

- No secrets in the repo, ever — config via `requires_env`, enforced in the
  publisher ground rules and reviewable in every one-file PR.
- Aggregator is index-only by construction; conversion PRs carry license +
  attribution (docs/AGGREGATION.md gates).
- Replace the personal auth CORS proxy with an MS-owned worker; set
  `VB_AUTH_WORKER` (tracked in ALIGNMENT.md actions).
- Complete upstream licensing (rapp-1, rapp-installer) before v1 GA.

## 7. Rollback

Every ring is a git ref + static Pages deploy: rollback = revert merge on
the ring branch; Pages redeploys in minutes. State snapshots (`state/`,
`api/`) are committed, so data rolls back with code. The corpus never needs
rollback — pins are immutable; a bad bump is a one-line manifest revert.
