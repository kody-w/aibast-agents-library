# ms-rapp/1 — the enterprise distribution of RAPP/1

This directory makes the repository self-contained as the reference for
**ms-rapp/1**: Microsoft's long-term-support distribution of the RAPP/1
protocol and platform. The relationship is deliberate and familiar:

| | Upstream ("the kernel") | This repo ("the LTS distro") |
|---|---|---|
| Analogy | Linux mainline / ECMAScript | Enterprise Linux / JavaScript engine |
| Who | kody-w open-source RAPP ecosystem | AIBAST Agents Library (ms-rapp) |
| Moves | fast — canary → nightly → alpha → beta → stable | deliberately — pinned, gated, verified |
| Protocol | ratifies RAPP/1 revisions | adopts ratified revisions by pin bump |

**RAPP/1 is the standard; both sides implement it.** Neither renames it,
both comply with it, and the corpus is verifiable from the documents in
this directory alone — no external repo required.

## What's here

| Path | Contents |
|------|----------|
| [`spec/RAPP1-SPEC.md`](spec/RAPP1-SPEC.md) | The RAPP/1 protocol suite (rev-5), byte-exact at the ecosystem's authority pin |
| [`spec/RAPP1_AUTHORITY.json`](spec/RAPP1_AUTHORITY.json) | The pin: upstream commit + SHA-256 the whole ecosystem cites |
| [`spec/ecosystem-spec.json`](spec/ecosystem-spec.json) | The full ecosystem specification (`rapp-ecosystem-spec/1.0`) |
| [`handbook/`](handbook/) | The RAPP Handbook (mirrored from the upstream RAPP-Bible project): end-to-end explanation of the ecosystem + 9 sub-specs (BSD-3-Clause, see NOTICE) |
| [`standards/`](standards/) | Companion standards: `rapp-holo/1.0`, `rapp-static-api/1.0`, the ring PLAYBOOK, machine entry points |
| [`ATTRIBUTION.md`](ATTRIBUTION.md) | Naming posture — the marks belong upstream; this distribution claims none |
| [`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md) | License map for every mirrored file (mirrors ship under their upstream licenses) |
| [`MIRROR-MANIFEST.json`](MIRROR-MANIFEST.json) | Provenance for every mirrored file: repo, pinned commit, SHA-256, license |
| [`BRAINSTEM-LOCK.json`](BRAINSTEM-LOCK.json) | SHA-256 lock on the stable brainstem + installers — the fork point, executable |
| [`SUCCESSION.md`](SUCCESSION.md) | How changes flow: kernel → LTS down, fixes → kernel up |
| [`ALM.md`](ALM.md) | Release engineering: rings, builds, gates, cadence |
| [`ALIGNMENT.md`](ALIGNMENT.md) | The audit: mirror agreement, drift findings, license gaps, shape-lock verification |

## Verifying this corpus

```bash
python3 scripts/corpus_sync.py --check --local-only   # every mirror hash-matches its manifest pin
python3 scripts/corpus_sync.py --check                # + upstream still serves identical bytes at each pin
bash tests/test_library_frontend.sh                   # full suite incl. T-CORPUS and T-LOCK
```

A mirror never advances silently: `corpus_sync.py` only verifies; moving a
pin is a human pull request (see SUCCESSION.md).
