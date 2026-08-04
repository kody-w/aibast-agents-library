<!-- MIRROR · upstream of record: kody-w/rapp-commons/main/MOMENT_SPEC.md §6.1 + hologram/rappid.js -->

# RAPP Eternity Standard

> **Spec id:** `rapp-eternity/1.0` · **status:** additive · **scope:** the cross-ecosystem eternal identity + compatibility law.

A second, broader rappid namespace than the door-bound `rapp-rappid/2.0` (`rappid:v2:<kind>:@<owner>/<repo>:<32hex>@github.com/...`). The Eternity id is **not** door/owner/repo-bound.

## Canonical form
`rappid:<slug>:<64hex>` — 256-bit (real SHA-256), a PKI-free content-address; **keypair-binding is OPTIONAL** (signatures live in an add-on `sig_suite` record field, never a required PKI). The **64-hex is THE join key**.

- `slug` — the kind. Defined kinds today: `moment` (a living holographic Moment), `keeper` (a signing-key identity), `dimension` (a world/organism, e.g. the RAPP Commons).
- `<64hex>` — `sha256("<slug>:" + <eternal-source>)`. For a Moment: the source is its spacetime `pk` (`sky·<utc_ms>` or `<geohash>·<utc_ms>`), so the id is deterministic and eternal — the address regenerates the organism with zero lookup.

## Laws (MUST)
1. **The hash is the join key.** Records are joined on the 64-hex, never on a human label.
2. **Read all legacy forms forever; emit only canonical.** A bare UTC ms, a `pk`, a `|` separator all resolve to the same canonical rappid.
3. **Never version the string — add record fields instead.** Crypto-agility lives in a `sig_suite` field (e.g. `ecdsa-p256`), covered by the signature; the string never gains a version segment.
4. **Identity is never rewritten in place.** The id is immutable; ownership moves via a separate, hash-linked **deed** chain (the rappid is stable; the deed transfers).

## Relationship to the corpus
- Coexists with `rapp-rappid/2.0` as a parallel namespace (Eternity rappids do not door-resolve to GitHub URLs).
- Aligns with CONSTITUTION Article XXXIV's immutable-identity discipline; **reconciliation owed** with Article XLVI (which fixes the only rappid format) — see the grail-scan report.
