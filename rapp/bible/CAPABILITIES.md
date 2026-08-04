# Capabilities — what the ecosystem can do, honestly

> *Renders the `capability_domains` of [`ecosystem-spec.json`](https://raw.githubusercontent.com/kody-w/rapp-god/main/api/v1/ecosystem-spec.json) v1.2.0 for a human reader.*

This page is the honest coverage map. Every capability in the RAPP ecosystem falls into one of three buckets:

- **Native** — the one agent (`@rapp/rapp`) does it directly through an action.
- **Install-routed** — the one agent reaches it by `install`-ing a specialist agent on demand.
- **Specialist-owned** — the capability lives in its own dedicated agent or surface; the god agent routes you there but does not perform it.

Where the spec marks a capability `to_close`, it is a **known gap** — the action is planned but not yet live in the agent's enum. We list those plainly; honesty about gaps is the contract (no half-released shims, ANTIPATTERNS §3).

The domains below are grouped for reading. Each row names the operator-facing capability and the action (or specialist) that delivers it.

---

## Platform Installation & Bootstrap

| Capability | Coverage | Action / owner |
|---|---|---|
| Install the kernel | specialist | `installer/install.sh` + `installer/plant.sh` (the one-liner) |
| Fetch kernel code | native | `refresh`, `ecosystem`, `find` |
| Orient in the ecosystem | native | `ecosystem`, `find`, `spec` |
| Read my identity | native (partial) | `whoami` (reads; does not mint) |
| Mint a rappid at first plant | native *(to_close)* | `mint` |
| Scaffold a fresh organism | native *(to_close)* | `plant` / `bootstrap` |
| Write initial memory | native *(to_close)* | `memory` (init `.brainstem_data/memory.json`) |
| Scaffold the agents directory | install-routed *(to_close)* | `scaffold` (fetch the kernel seed agents) |

---

## Rappid & Identity (the global address layer)

| Capability | Coverage | Action / owner |
|---|---|---|
| Encode a rappid | native | `door` |
| Derive the 9 door URLs | native | `door` |
| Walk the lineage chain | native *(to_close)* | `lineage` (fetch `parent_rappid`, walk to species root) |
| Verify a rappid is valid | native *(to_close)* | `door rappid=… validate=true` |
| Record a bond event | native *(to_close)* | `bond` (append to `bonds.json`) |

---

## Estate & Door Addressing

| Capability | Coverage | Action / owner |
|---|---|---|
| Local estate catalog | native | `estate` |
| View a door by rappid | native | `door` |
| Estate overview | native | `whoami` |
| Find a part in the ecosystem | native | `find` |
| Refresh the grail registry | native | `refresh` |
| Add a door to my estate | native *(to_close)* | `estate_add` |
| Publish estate (public) | native *(to_close)* | `estate_publish` |
| Public/private split | native *(to_close)* | `estate_privacy` (HMAC commitment) |
| Disaster recovery of estate | native *(to_close)* | `estate_recover` (walk public GitHub data) |
| Set private-door commitment | native *(to_close)* | `estate_commit` (Bitcoin-style commitment) |

---

## Neighborhood & Gate Structure

| Capability | Coverage | Action / owner |
|---|---|---|
| Neighborhood roster | native | `browse` |
| Neighborhood shared agents | native | `super_rar where=neighborhood`, `load` |
| Neighborhood memory tiers | native | `stash`, `browse`, `show_and_tell`, `sync` |
| Neighborhood identity (rappid + meta) | native *(to_close)* | `neighborhood_info` |
| Neighborhood constitution | native *(to_close)* | `neighborhood_constitution` |
| Private companion repo | native *(to_close)* | `neighborhood_private` |

---

## Cubbies & Dark Doors (private neighborhoods)

| Capability | Coverage | Action / owner |
|---|---|---|
| Invite-only dark door | native | `invite` + `join` |
| V-neighborhood front door | native | `enter` + `qr` |
| Portable, offline cubby | native | `cubby_egg` + `cubby_import` |
| Pack all cubbies in a neighborhood | native *(to_close)* | `neighborhood_egg` |
| Cubby encryption | specialist | the doorman / sealed codec |

---

## Eggs & Cartridges (organism portability)

| Capability | Coverage | Action / owner |
|---|---|---|
| Export an organism egg | native | `cubby_egg` |
| Hatch an organism egg | native | `cubby_import` |
| Hatch a session egg | native | `hatch` |
| Multi-scale hatcher | native | `hatch` |
| Export an ascended egg | native *(to_close)* | `cubby_egg tier=ascended` |
| Export a neighborhood egg | native *(to_close)* | `neighborhood_egg` |
| Export an estate egg | native *(to_close)* | `estate_egg` |
| Verify egg integrity | native *(to_close)* | `verify_egg` |
| Export / hatch a rapplication egg | native / install-routed *(to_close)* | `rapplication_egg` / extend `hatch` |
| Export a session egg | specialist | `pages/vbrainstem.html` exporter |

---

## RAR (agent registry) & Agent Installation

| Capability | Coverage | Action / owner |
|---|---|---|
| RAR index per seed | native | `ecosystem` / `find` |
| Install an agent from RAR | native | `load` |
| Federated RAR load | native | `super_rar where=neighborhood` |
| Author an agent locally | native | `cubby_new` / `stash` |
| Publish an agent to a neighborhood | native | `stash` / `join` / `mount` |
| Load from a downstream RAR | install-routed *(to_close)* | `load source=<rar-url>` |
| SHA-256 pin on install | install-routed *(to_close)* | `load --verify` |
| Agent-proposal PR | specialist | open a PR against the registry |

---

## Stores (Rapplications & Senses)

| Capability | Coverage | Action / owner |
|---|---|---|
| Rapplication catalog | native | `super_rar where=neighborhood query=<q>` |
| Sense store | native / specialist | `super_rar query=<q>` |
| Store catalog browse | install-routed *(to_close)* | `store_catalog` |
| Install a rapplication | install-routed *(to_close)* | `install_rapplication` |
| Rapplication source editing | specialist | a source-editor agent / Copilot Studio (Tier 3) |

---

## Memory & Recall (three-tier model)

| Capability | Coverage | Action / owner |
|---|---|---|
| Device-local memory | install-routed *(to_close)* | `memory_store` / `memory_read` |
| Public memory read | native *(to_close)* | `memory_list` / `memory_read` |
| Public memory write | native *(to_close)* | `memory_save` |
| Per-user private memory | native *(to_close)* | `memory_private_save` / `memory_private_list` (GitHub Issues) |
| Memory in the system prompt | install-routed *(to_close)* | extend `system_context()` |
| Ascended-egg memory export | native *(to_close)* | `memory_egg export_private=true` |

The deep memory tier lives in `manage_memory_agent.py` / `context_memory_agent.py` — install them; the god agent natively does the local tier.

---

## Twin Lifecycle (active / archived / purged)

Entirely **specialist-owned** by `@rapp/twin_agent` — `install @rapp/twin_agent`:

`list_active_twins`, `boot_twin`, `stop_twin`, `archive_twin`, `unarchive_twin`, `purge_twin`, `bulk_archive_filter`, `list_archived_twins`, `list_purged_twins`.

---

## Bonding & Lineage (cross-device mutation sharing)

| Capability | Owner agent | Reach |
|---|---|---|
| Graft a neighborhood (additive overlay) | `graft_neighborhood_agent.py` | install from the species grail |
| Launch to public (LOCAL → GLOBAL) | `launch_to_public_agent.py` | install from the species grail |
| Dock registry merge | `dock_agent.py` | install from the species grail |
| Bond-rhythm pulse | `bond_rhythm_agent.py` | install from the species grail |
| Lineage roll-up stats | `lineage_rollup_agent.py` | install from the species grail |

These are install-routed: the five agents must exist in `agents/`; the god agent records the lineage frames natively and reaches the rest.

---

## Twin Chat & Cross-Organism Communication

| Capability | Coverage | Action / owner |
|---|---|---|
| Twin-chat envelope | specialist | `@rapp/twin_agent` |
| Say / share-fact / share-egg / request-fact / ack | specialist | `@rapp/twin_agent` (god agent does indirect `show_and_tell` / one-way `hatch`) |
| Facet gating | native *(to_close)* | read `facets.json`, filter by scope |

---

## WebRTC Tether & Pairing

| Capability | Coverage | Action / owner |
|---|---|---|
| QR pair | native | `qr` |
| Broker drops after handshake | native | `enter` |
| Tether egg stream | native (partial) | `cubby_egg` + `hatch` |
| Safety code / live chat / live chunked egg stream / multi-participant session | specialist | `pages/vbrainstem.html` + the doorman |

---

## Dream Catcher (parallel-dimension reassimilation)

| Capability | Coverage | Action / owner |
|---|---|---|
| Content-addressed frame log | native *(to_close)* | frame-logging action / `rapp-frame/1.0` chain |
| Dream-catcher diff | specialist | the dream-catcher specialist |
| Shared / parallel-only frame classification | specialist | the dream-catcher specialist |
| Contradiction detection | native *(to_close)* | `contradiction_check` |
| Reassimilation PR | native *(to_close)* | `reassimilation_pr` |
| Cross-species check | native *(to_close)* | lineage check in `hatch` |

---

## MMR & Leaderboard (global rating & tier ladder)

Entirely **specialist-owned** (install the specialists; god agent computes single-door MMR via `mmr`):

`compute_mmr_local`, `mmr_calibration`, `mmr_activity_decay`, `lineage_gift_snapshot`, `lineage_gift_immortal`, `species_leaderboard`, `lineage_rollup`, `tier_ladder`.

---

## Resurrection Ceremony (stasis recovery)

| Capability | Coverage | Action / owner |
|---|---|---|
| Run the ceremony on a stale organism | native *(to_close)* | `resurrection_ceremony` |
| Emit a resurrection frame | native *(to_close)* | `bond` kind=`resurrection` |
| Lift the activity multiplier 0.45 → 1.0 | native *(to_close)* | within `resurrection_ceremony` |

---

## Proximity Discovery (location-based swarm — the Pizza Place layer)

| Capability | Coverage | Action / owner |
|---|---|---|
| Location-tied planting | specialist | the planting specialist |
| Proximity discovery (geohash) | native *(to_close)* | `discover_proximity` |
| Public-facets consent | native *(to_close)* | `facets_declare` / `card_set` |

---

## Governance & Drift Detection

| Capability | Coverage | Action / owner |
|---|---|---|
| Ecosystem contract | native | `refresh`, `ecosystem` |
| Per-kind file contracts | native *(to_close)* | `contracts` |
| Drift classification | native *(to_close)* | `drift_types` |
| Drift directionality (push / pull / informational) | native *(to_close)* | `classify_drift` |
| Full ecosystem audit | specialist | `tools/ecosystem_audit.py` |
| Offline audit | specialist | `--offline` fixture mode |

---

## Network Protocol & Discovery (Articles XLVI–XLVIII)

| Capability | Coverage | Action / owner |
|---|---|---|
| Rappid resolution → canonical URLs | native | `door` |
| Consume grail specs | native | `spec` / `ecosystem` / `find` / `refresh` |
| Network seed bootstrap | native *(to_close)* | `sniff` / `network_seed` |
| Decentralized BFS discovery | native *(to_close)* | `sniff` |
| Multi-substrate federation | native *(to_close)* | `sniff_lan` / `sniff_seed` |
| LAN Bonjour advertise | native *(to_close)* | `advertise_lan` |
| Sneakernet egg import | native *(to_close)* | `import_peer_egg` |
| Estate beacon publish | specialist | `estate publish` / `beacon` |

---

## MCP Integration (Model Context Protocol transport)

Entirely **specialist-owned** by [rapp-mcp](https://github.com/kody-w/rapp-mcp). MCP is *transport, not a new taxonomy* — an MCP host is a Layer-2 caller of `/chat`:

`agents_as_mcp_tools`, `brainstem_over_mcp`, `static_mcp_profile`.

---

## Agent-Built Web (Rio & RioNet)

| Capability | Coverage | Action / owner |
|---|---|---|
| Agent emits HTML | native *(to_close)* | a `rio_ui_agent` (`ui_build` / `ui_render`) |
| Rio agent framework | specialist | [rio](https://github.com/kody-w/rio) |
| RioNet federation | specialist | [rionet](https://github.com/kody-w/rionet) |

---

## Ant Farm (collective intelligence)

| Capability | Coverage | Action / owner |
|---|---|---|
| Drop a pheromone | native *(to_close)* | `ant_pheromone` |
| Observe the colony | native *(to_close)* | `colony_observer` |
| Spawn ant-farm offspring | install-routed *(to_close)* | `cubby_new kind=ant-farm` |
| Ant tick | specialist | `ant_agent.py` |

---

## Metropolis Tracker (emergent city)

| Capability | Coverage | Action / owner |
|---|---|---|
| Estate overview (my neighborhoods) | native | `estate` |
| Neighborhood discovery by door | native | `door rappid=…` |
| Search the parts database | native | `find query=…` |
| Mount + join one neighborhood | native | `mount` / `join` |
| Browse the metropolis index | native *(to_close)* | `metropolis_browse` |
| Inspect a tracked entry | native *(to_close)* | `metropolis_browse query=…` |
| Tracker federation | native *(to_close)* | `metropolis_federation` |
| Town → city growth | specialist | `graft` auto-nesting |

---

## Registry Observatory (rapp-god & rapp-map)

| Capability | Coverage | Action / owner |
|---|---|---|
| rapp-god specs | native | `spec`, `refresh` |
| rapp-map neurons | native (partial) | `ecosystem`, `find` |
| Schema drift watch | native (partial → `to_close`) | `ecosystem` → dedicated `drift_check` |
| Complete neuron-mesh view | native *(to_close)* | `neurons` |
| Ecosystem-wide verify/audit | specialist | the `verify` action / `ecosystem-sync` swarm |

---

## Tier 2: Cloud Brainstem (Azure Functions)

| Capability | Coverage | Action / owner |
|---|---|---|
| Vendored agents run unmodified | native | `load` (same `*_agent.py` as Tier 1) |
| Deploy to Azure Functions | specialist | `rapp_swarm/function_app.py` |
| ARM one-click deploy | specialist | `installer/azuredeploy.json` |
| Path-prefix routing under `/api/*` | specialist | (same `/chat` envelope) |
| Entra ID managed identity + RBAC | specialist | (no API keys in code) |

---

## Tier 3: Copilot Studio Enterprise

| Capability | Coverage | Action / owner |
|---|---|---|
| Agent contract (`__manifest__` + `perform()`) | native | the same single-file contract |
| Import the solution bundle | native *(to_close)* | `import_bundle` |
| Configure Studio surfaces (Teams / M365 / web) | native *(to_close)* | `studio_config` |
| Wire to a function app | install-routed *(to_close)* | `set_function_app` |

---

## Delimited Slots & Output Routing (Voice & Twin)

| Capability | Coverage | Action / owner |
|---|---|---|
| `\|\|\|VOICE\|\|\|` slot | system infrastructure | brainstem.py (not an agent's job) |
| `\|\|\|TWIN\|\|\|` slot | system infrastructure | brainstem.py |
| Twin inner tags | system infrastructure | brainstem.py |
| Time-travel-safe slots | constitution | Art. II.3 (backward compat) |
| Slot mechanism in kernel | constitution | Art. II.2 + Art. I (kernel forever) |

---

## How to read the gaps

A `to_close` tag is not a broken promise — it is the spec being honest about which actions are planned vs. live. The four-leg drift triangle exists precisely so that when an action *does* ship, `action=verify` confirms the agent's enum now matches the spec, and the gap closes for real. See [`DRIFT_TRIANGLE.md`](DRIFT_TRIANGLE.md).

*Authority: `ecosystem-spec.json` v1.2.0 `capability_domains`. This page is the human rendering; the JSON is canonical.*
