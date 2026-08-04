# Alignment audit — kernel ↔ LTS, corpus ↔ mirrors

Snapshot date: 2026-08-04, revised after adversarial review (two independent
reviewers, findings verified against live upstream). Re-verify at any time:
`python3 scripts/corpus_sync.py --check` + the T-LOCK/T-CORPUS test sections.

## 1. Brainstem shape lock — SYNCED AND VERIFIED ✅

This tree's `rapp_brainstem/` and installers were **synced from the
enterprise stable channel (microsoft main) in this change** — the staging
tree had lagged at engine 0.6.0 and now carries the stable state exactly:

- `rapp_brainstem/VERSION`: **0.6.16** — matching both the upstream stable
  repo (kody-w/rapp-installer, `5fbde17`) and the enterprise stable channel
  (microsoft main, `682c050`).
- File shape: both stable channels carry an identical 17-entry `rapp_brainstem/` file
  list (verified — nothing present in one and absent in the other); this
  tree now mirrors it, including `requirements-dev.txt` and the `tests/`
  directory.
- Between the two stable channels, byte deltas are confined to a handful of small
  attribution/rebrand differences (~3–30 bytes in CONSTITUTION.md,
  README.md, brainstem.py, soul.md, start.\*); `install.sh` differs by 334
  bytes (0.9%). No structural fork.

The lock is executable: `rapp/BRAINSTEM-LOCK.json` records the SHA-256 of
every kernel file in this tree (brainstem tree + root installers + the
`docs/` installer copies Pages actually serves); test section T-LOCK fails
on any modification **and any added or removed file** in the locked tree.

**Kernel content intentionally untouched (fixes flow down, never patched
here):** the 0.6.16 brainstem UI ships a registry browser pinned to the
kernel's public RAR catalog, and `soul.md` links a kernel onboarding page.
Both are upstream editorial decisions; an enterprise repoint would be a
distro patch and is deliberately not carried (see SUCCESSION.md).

## 2. Protocol authority — pin current with the kernel ✅

The kernel re-pinned RAPP/1 shortly before this audit; this mirror was
bumped in the same change (a worked pin-bump):

- `rapp/spec/RAPP1_AUTHORITY.json` mirrors the kernel's **live** authority
  file (kody-w/rapp-map@main): commit `d2cd5abe`, 41,952 B, sha256
  `cea7847f…`, spec revision 5.
- `rapp/spec/RAPP1-SPEC.md` hash-matches that pin exactly, and
  `corpus_sync.py --check` verifies **authority freshness** on every run —
  if the kernel re-pins again, the check fails with "pin-bump PR needed"
  rather than passing silently.

## 3. Ecosystem-spec mirrors — quarantine understood, no contradiction ✅

The historical premise "ecosystem-spec.json mirrored at the upstream version
registry (rapp-god) + rapp-map
roots" is retired upstream: `rapp-map/ecosystem-spec.json` is a deliberate
~1 KB quarantine tombstone whose own text refuses registry authority. The
live full spec is `rapp-god/src/runtime/RAPP/specs/ecosystem-spec.json`
(60,479 B, `rapp-ecosystem-spec/1.0` v1.2.0), mirrored here at
`spec/ecosystem-spec.json` and hash-verified. Protocol authority itself has
moved to rapp-1 (§2).

## 4. License posture

| Upstream | License | Mirror handling |
|---|---|---|
| rapp-map, rapp-god, rapp-static-apis | MIT | copyright recorded in [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) |
| RAPP-Bible | BSD-3-Clause | `handbook/LICENSE` + `handbook/NOTICE` (byte-exact, attributed) |
| rapp-train, rapp-holo | Apache-2.0 | `standards/LICENSE-APACHE-2.0` + `standards/NOTICE` |
| **rapp-1** | **no LICENSE file upstream** | mirrored under the author's recorded authorization (manifest entry carries grantor/date/scope). **An upstream LICENSE on rapp-1 is a v1-GA blocker.** |
| rapp-installer | no LICENSE file upstream | not mirrored (stable engine repo; shape-locked reference only) — same upstream action applies |

Upstream trademark documents are **not** mirrored — naming posture lives in
[ATTRIBUTION.md](ATTRIBUTION.md); this distribution claims no marks.

## 5. Clean-break status (this repo)

References into the upstream maintainer's personal estate exist only where
the succession model requires them — enforced by test T-CLEAN, whose
allowlist is: the locked kernel tree (`rapp_brainstem/`), the pinned corpus
mirrors and governance docs (`rapp/`), the browser runtime's auth CORS
proxy (`vbrainstem/brainstem_web.py`, override with `VB_AUTH_WORKER`), the
audit docs, and the test suite's own guard patterns. Generated `state/` and
`api/` must carry zero. Full dispositions: `docs/CLEAN-BREAK.md`.

## 6. Corpus long tail (inventoried, deliberately not mirrored)

Beyond the canonical documents mirrored here, the kernel ecosystem carries
hundreds of additional `SPEC.md` files across its repos (`rapp-sealed/1.0`,
`rapp-eternity/1.0`, `rapp-cart/1.0`, `rapp-metrics/1.0`, …). Policy: the
LTS mirrors a spec when an enterprise surface depends on it (the pin-bump
process adds a manifest entry); it does not vendor the whole estate.
Mirroring by pin, not by clone, keeps this repo lean and auditable.

## 7. Action items

| Owner | Action |
|---|---|
| Upstream maintainer | Add a LICENSE to rapp-1 and rapp-installer (**v1-GA blocker**) |
| LTS admin | Enable Discussions + METRICS_TOKEN on the microsoft repo |
| LTS admin | Stand up an MS-owned auth CORS proxy; set `VB_AUTH_WORKER` |
| LTS admin | Create the `corpus-drift` label upstream (the corpus-check workflow also self-creates it) |
