# Succession — how RAPP flows between the kernel and the LTS

The pattern is the one that has kept Linux healthy for thirty years: an
open-source **kernel** that moves fast, and an enterprise **LTS**
distribution that adopts deliberately. Don't reinvent it; follow it.

```
  kody-w RAPP kernel                      ms-rapp LTS (this repo)
  canary → nightly → alpha → beta → GRAIL ──sync PR──▶ main (LTS)
        ▲                                                │
        └────────── issues / PRs (fixes flow UP) ────────┘
```

## The two sides

- **Kernel** — the kody-w open-source RAPP ecosystem. Development rides the
  release train (canary → nightly → alpha → beta → grail). The grail
  (`kody-w/rapp-installer`) is human-merge-only; its own rule — stated in
  the kernel's machine entry point (`standards/rapp-train-llms.txt`) — is
  **never push to the grail or to microsoft/aibast-agents-library
  directly**. The kernel ratifies RAPP/1 protocol revisions.
- **LTS** — this repository. It ships only what is pinned, gated, and
  verified. Enterprise users get stability; the standard guarantees the two
  sides stay interoperable.

## Flow DOWN (kernel → LTS): the only way changes arrive

1. The kernel cuts a grail release (tagged version).
2. A **sync PR** into this repo brings the release across. The PR must, in
   the same commit:
   - update the synced kernel content (brainstem, installers),
   - regenerate `rapp/BRAINSTEM-LOCK.json` (the lock moving IS the record
     of a sanctioned sync),
   - pass the full test suite, the link audit, and `corpus_sync.py --check`.
3. Nothing else may modify locked kernel files. A red T-LOCK test on any
   other PR is the system working — revert the change, file it upstream.

**Worked example (live today):** the local brainstem's registry browser
points at a retired upstream catalog URL. The fix is NOT patched here — it
lands in the kernel via the train, rides a grail release, and arrives in
the next sync PR. `rapp/ALIGNMENT.md` tracks it until then.

## Flow UP (LTS → kernel): fixes and proposals

Bugs found here, features the enterprise needs, protocol clarifications —
all go upstream as **issues or PRs against the kernel repos** (entering at
canary like everything else). Never as direct grail pushes, never as
downstream-only forks of kernel behavior. A divergence the kernel refuses
becomes a documented distro patch in `ALIGNMENT.md` — enumerated, minimal,
and re-proposed upstream at each sync.

## Protocol adoption: the pin bump

RAPP/1 revisions are ratified in the kernel (`kody-w/rapp-1`). The LTS
adopts a revision by a **pin-bump PR**:

1. Edit `rapp/MIRROR-MANIFEST.json`: move the pinned commit(s).
2. Update `rapp/spec/RAPP1_AUTHORITY.json` to the kernel's new authority
   pin — the LTS never pins a revision the kernel's own authority file does
   not cite.
3. Run `scripts/corpus_sync.py --fetch`; commit files + manifest together.
4. The T-CORPUS gate proves every mirror hash-matches before merge.

A pin bump is always a reviewed human PR. `corpus_sync.py` can detect drift;
it is not allowed to chase it.

## Version policy

- `rapp_brainstem/VERSION` — the kernel engine version (locked; moves only
  by sync PR). Both grails read `0.6.16` today.
- RAPP/1 revision — from `rapp/spec/RAPP1_AUTHORITY.json` (rev-5 today).
- Library releases (gallery, metrics, API surface) — tagged here per
  `rapp/ALM.md`; they never imply a protocol or engine change.
