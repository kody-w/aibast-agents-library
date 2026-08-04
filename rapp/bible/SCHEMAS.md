# Schema registry

> *Renders the schema families referenced in [`ecosystem-spec.json`](https://raw.githubusercontent.com/kody-w/rapp-god/main/api/v1/ecosystem-spec.json) v1.2.0 (`schemas_ref` + `primitives`) and the full ~80-schema table in [`ECOSYSTEM_MAP.md`](https://github.com/kody-w/RAPP/blob/main/ECOSYSTEM_MAP.md) §5.*

Every payload in RAPP carries a `schema` string of the form `rapp-*/N.M` (or `brainstem-egg/*`). The rule (ANTIPATTERNS §3): **search this registry before defining a new schema.** If a schema changes, bump the version string and migrate cleanly — no backward-compat shims for half-released features.

The canonical full table is `ECOSYSTEM_MAP.md` §5 in the species root; this page groups the families for a reader. One-line purpose each.

---

## Identity (the global address layer)

| Schema | Purpose |
|---|---|
| `rapp-rappid/2.0` | Organism birth certificate + kernel + bonds. The Eternity rappid record (kind lives here, not in the string). |
| `rapp-rappid/1.1` | Legacy birth-certificate schema (read forever; pre-2026-04-30 seeds keep their UUID form, never regenerated). |
| `rapp-door/1.0` | Derived door object — owner, repo, kind, door_type, all 9 canonical URLs. Pure derivation; never stored. |
| `rapp-card/1.0` | Trade-card / introduction view override. |
| `rapp-facets/1.0` | Per-door published-capability declaration at `facets.json`. |
| `rapp-public-facets/1.0` | Granular permission gate (name + scope + description) — the trust-scope primitive. |
| `rapp-twin-spec/1.0` | The soul Identity block contract (the "read this every turn" block). |

---

## Estate & discovery (Articles XLVI–XLVIII)

| Schema | Purpose |
|---|---|
| `rapp-estate/1.1` | Local-first estate FILE — the door catalog. Each entry stores ONLY `{rappid, added_at, via}`. |
| `rapp-estate/1.0` | Estate top-level (organ-aggregated server-side view). |
| `rapp-private-estate/1.0` | The PRIVATE tier of every Article-XLVIII estate (opaque paths, collaborator-gated). |
| `rapp-rappid-estate-view/1.0` | Estate-by-rappid lookup — the global passport. |
| `rapp-network-beacon/1.1` | Per-operator discovery beacon (`.well-known/rapp-network.json`) with private-estate pointer + commitment. |
| `rapp-network-seed/1.0` | The DNS-root analog — the BFS starting set of known operators. |
| `rapp-network-sniff/1.0` | Decentralized-discovery walk result. |
| `rapp-import-egg-result/1.0` | Sneakernet egg-import result. |

---

## Cartridges (the egg family)

| Schema | Purpose |
|---|---|
| `brainstem-egg/2.2-organism` | Full instance cartridge — rappid + soul + .env + agents + organs + senses + services + `.brainstem_data`. |
| `brainstem-egg/2.2-rapplication` | Single-rapp cartridge — rappid + agent + UI + per-rapp state. |
| `brainstem-egg/2.3-session` | Live multi-participant tether, made portable (sha256-pinned runtime + transcript + participants). |
| `brainstem-egg/2.3-neighborhood` *(planned)* | A neighborhood gate, made portable. |
| `brainstem-egg/2.3-estate` *(planned)* | An operator's whole multi-tier identity, portable across substrates. |
| `brainstem-egg/2.1` | Variant repo cartridge (templated brainstem clone). |
| `rapp-egg-provenance/1.0` | SHA-256 file hashes + manifest hash + origin commit SHA (the seal). |
| `rapp-organism-state/1.0` | `state_at_seal` snapshot (mem_count, mut_count, MMR, …). |
| `rapp-frame/1.0` | A mutation event — content-addressed sha256 with a `prev_hash` chain. The Dream Catcher reads these. |

---

## Agents & rapplications

| Schema | Purpose |
|---|---|
| `rapp-agent/1.0` | Agent module manifest (the function-calling shape) — every `*_agent.py` metadata dict. |
| `rapp-application/1.0` | Rapplication manifest (RAPP_Store entries). |
| `rapp-memory/1.0` | A memory record. |
| `rapp-user-memories/1.0` | Per-user issue memories (ascended-tier export). |

---

## Neighborhoods & gates

| Schema | Purpose |
|---|---|
| `rapp-neighborhood/1.0` | Neighborhood metadata (gate repo `neighborhood.json`). |
| `rapp-neighborhood-members/1.0` | The roster (gate repo `members.json`). |
| `rapp-neighborhood-protocol/1.0` | Wire-protocol meta. |
| `rapp-neighborhood-subscription/1.0` | One subscription record. |
| `rapp-neighborhoods-cache/1.0` | Local subscription cache. |

---

## Private cubbies & dark doors

| Schema | Purpose |
|---|---|
| `rapp-cubby/1.0` | A cubby — a private estate slice inside a gate. |
| `rapp-super-rar/1.0` | Federated RAR search across local + neighborhood indexes. |
| `rapp-payphone-dial/1.0` | The dialer for a dark door with no public front. |

---

## Federation (the wire)

| Schema | Purpose |
|---|---|
| `rapp-twin-chat/1.0` | The inter-twin message envelope — the federation wire. |
| `rapp-twin-chat-response/1.0` | Twin-chat reply wrapper. |
| `rapp-tether/1.0` | WebRTC tether envelope. |
| `rapp-twin/1.0` | Mobile-side twin egg bundle (canonical client schema). |
| `rapp-twin-identity/1.0` | Twin identity envelope (onboard surface). |

---

## RAR registry & participation kit

| Schema | Purpose |
|---|---|
| `rapp-rar-index/1.0` | Per-neighborhood RAR registry — the required participation kit at `rar/index.json`. |
| `rapp-rar-manifest/1.0` | The sha256 verification block inside `rar/index.json`. |
| `rapp-rar-loadout/1.0` | What the RarLoader installed / skipped / errored. |
| `rapp-registry/1.0` | The RAR registry (the agent Pokédex). |
| `rapp-store/1.0` | Store catalog meta. |
| `rapp-egg-hub-entry/1.0` | Egg-hub catalog entry. |

---

## Bond techniques (lineage actuators)

| Schema | Purpose |
|---|---|
| `rapp-graft-result/1.0` | Additive-overlay graft result (files added/skipped/restored + bond event). |
| `rapp-launch-result/1.0` | LOCAL → GLOBAL launch result (egg sha256 + continuation URL + fork lineage). |
| `rapp-launch-continuation/1.0` | The `LAUNCH_CONTINUATION.md` instructions left in the target repo. |
| `rapp-launch-fingerprint/1.0` | Compact fingerprint block embedded in the launch result. |
| `rapp-dock-result/1.0` | Universal additive-merge result (works on any rar-shaped JSON). |
| `rapp-rhythm-pulse/1.0` | Bond Pulse heartbeat — drift summary + suggested actions (operator-mediated; never auto-executes). |
| `rapp-lineage-rollup/1.0` | Lineage-tree aggregation (avg / median / min / max MMR). |

---

## Governance & drift

| Schema | Purpose |
|---|---|
| `rapp-ecosystem-map/1.0` | The ecosystem map document schema (the §5 table itself). |
| `rapp-ecosystem-spec/1.0` | This ecosystem spec — the four-leg drift source. |
| `rapp-ecosystem-audit/1.0` | Drift detector — per-offspring drift entries + by-kind counts + suggested actions. |
| `rapp-protocol/1.0` | The bundled-with-every-planting god spec + skill runbook. |

---

## MMR, leaderboard & ceremonies

| Schema | Purpose |
|---|---|
| `rapp-species-leaderboard/1.0` | Global Herald → Immortal tier ladder. |
| `rapp-proximity-match/1.0` | Geohash-prefix match result (the Pizza Place layer). |
| `rapp-resurrection-assessment/1.0` | Stasis-state diagnosis. |
| `rapp-resurrection-ceremony/1.0` | Resurrection frame + next-step commit template. |

---

## Neuron mesh & metropolis

| Schema | Purpose |
|---|---|
| `rapp-neuron/1.0` | One neuron — a file-specialist node in the rapp-map mesh. |
| `rapp-neuron-mesh/1.0` | The full neuron mesh (`rapp-map/neurons.json`). |
| `rapp-metropolis-index/1.0` | Metropolis tracker top-level. |
| `rapp-metropolis-entry/1.0` | One neighborhood entry in a tracker. |

---

## Ant farm (collective intelligence)

| Schema | Purpose |
|---|---|
| `rapp-pheromone/1.0` | Ant-farm pheromone (content-addressed, prev_hash chained, dropped via labeled Issues). |
| `rapp-colony-observation/1.0` | Ant-farm collective-state synthesis. |
| `rapp-ant-tick/1.0` | Ant-agent tick result envelope. |

---

## Signing & kernel

| Schema | Purpose |
|---|---|
| `rapp-release-key/1.0` | ed25519 keypair generation envelope. |
| `rapp-release-signature/1.0` | ed25519 detached signature sidecar. |
| `rapp-kernel/1.1` | Kernel release manifest. |
| `rapp-version/1.1` | Signed kernel version pin. |

---

*This is a reading aid. The authoritative, append-only, ~80-row table — with every "Defined in" and "Emitted by" reference — is `ECOSYSTEM_MAP.md` §5 in [`kody-w/RAPP`](https://github.com/kody-w/RAPP/blob/main/ECOSYSTEM_MAP.md). If this page and that table disagree, that table wins.*
