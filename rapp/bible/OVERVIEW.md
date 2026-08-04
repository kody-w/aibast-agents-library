# The RAPP Ecosystem — the whole thing in one read

> *If you only read one file in this Bible, read this one.*
>
> **This document renders [`ecosystem-spec.json`](https://raw.githubusercontent.com/kody-w/rapp-god/main/api/v1/ecosystem-spec.json) v1.2.0** (the single canonical machine description, mirrored byte-identical in [rapp-god](https://github.com/kody-w/rapp-god) and [rapp-map](https://github.com/kody-w/rapp-map)) for a human reader. Where this prose and that JSON disagree, the JSON wins and this file is wrong — fix this file.

RAPP — the **Rapid Agent Prototype Platform** — is a way to grow AI organisms that own their own identity, carry their own memory, talk to each other, and run on hardware nobody had to buy. It is "engine, not experience": infrastructure only, no opinionated UI, no workflow you have to adopt.

This page walks the entire ecosystem top to bottom. Every concept here has a deeper page in this Bible; the links point you there.

---

## §1 — The first principle

> **Use everyone else's hardware to run the network.**

Every architectural decision is a corollary of that one sentence ([`MASTER_PLAN.md`](https://github.com/kody-w/RAPP/blob/main/MASTER_PLAN.md)). GitHub already paid for the global CDN (`raw.githubusercontent.com`), the auth system (`gh auth`), the durable async mailbox (Issues), the consent gate (Pull Requests), and the edge endpoints (`<owner>.github.io/<repo>/`). RAPP does not build a network — it uses the one already running. Operators run brainstems on their own machines; the network is the union of those machines plus the free public substrate they all share.

That is why there is no central server, no marketplace backend, no PKI, no registry database. There is only:

- **GitHub** as the substrate (storage, identity, mailbox, consent gate, CDN).
- **A small frozen kernel** that runs locally and serves one HTTP surface.
- **Single-file agents** as the only unit of extension.
- **Content-addressed identity** (the rappid) so nothing needs to be registered with anyone who could shut it down.

---

## §2 — Fractal scales: same five primitives, all the way up

RAPP is **fractal**. The same five primitives — **rappid + door + card + tether + trust scope** — describe a single agent, a whole organism, a neighborhood, an operator's estate, and an entire metropolis. The protocol does not change as you zoom out; only the scope does.

| Scale | What it is | Identity | Example |
|---|---|---|---|
| **agent** | one `*_agent.py` — single file, single class, single `perform()`, single `metadata` dict | inherits its parent twin's rappid | `learn_new_agent.py` |
| **twin / organism** | one planted seed (one repo) with a front door + doorman | its own Eternity rappid, minted once | `kody-w/heimdall` |
| **neighborhood** | a community-with-a-purpose; a GitHub repo is the gate. Public or PRIVATE (collaborator-gated). Has members + per-member cubbies | `neighborhood_rappid` | `kody-w/rapp-commons` |
| **estate** | ONE operator's union of everything they planted + joined; two-tier (public discovery + private bones) | the operator's personal Eternity rappid — the global passport | `~/.brainstem/estate.json` |
| **metropolis** | an emergent mesh of estates through shared neighborhoods; federations of metropolises emerge at planet scale | each operator's rappid, meshed | `kody-w.github.io/RAPP/metropolis/` |

The deeper you go, the more these compose without new machinery. An agent inherits its twin's identity; a twin lives in an estate; an estate meshes into a metropolis. You learn the primitives once.

---

## §3 — The five universal primitives

| Primitive | What it is | Schema |
|---|---|---|
| **rappid** | The global identity + address. From any rappid, with zero auth, every canonical URL is computable by string-parsing. | `rapp-rappid/2.0` |
| **door** | The public surface URL where a thing is reachable. Nine canonical URLs derive from the rappid. PRIVATE doors 404 to outsiders (the guard). A "dark door" has no public front door at all. | `rapp-door/1.0` (derived, never stored) |
| **card** | The trade-card / introduction view + granular published permissions. | `rapp-card/1.0` + `rapp-public-facets/1.0` |
| **tether** | The four channel types — WebRTC, Issues, PRs, raw fetch — carrying the twin-chat envelope. | `rapp-twin-chat/1.0` |
| **trust scope** | Personal / neighborhood / public swarm, gated by facets. | `rapp-public-facets/1.0` |

See [`SCHEMAS.md`](SCHEMAS.md) for the full ~80-schema registry.

---

## §4 — The seven OSI layers

The ecosystem is layered like a network stack ([`OSI.md`](https://github.com/kody-w/RAPP/blob/main/OSI.md)). Every feature belongs to exactly one layer:

| L | Layer | What lives here |
|---|---|---|
| 1 | **Substrate** | The physical layer — GitHub Pages + `raw.githubusercontent.com`, LAN, `file://`, sneakernet eggs. |
| 2 | **Identity** | The rappid layer — Eternity address, minted once, read forever. |
| 3 | **Discovery** | Lineage + catalog — `parent_rappid` chain, `estate.json`, RAR, rapp-god / rapp-map. |
| 4 | **Channels** | Transport — WebRTC tether, Issues, PRs, raw fetch. |
| 5 | **Trust scope** | Session / auth — personal / neighborhood / public, collaborator-gated private doors, the sealed channel (AES-256-GCM). |
| 6 | **Envelope** | Presentation — the egg cartridge family, the twin-chat envelope, the `\|\|\|VOICE\|\|\|` / `\|\|\|TWIN\|\|\|` slots. |
| 7 | **Application** | The agent + `/chat` layer — single-file agents, organs, the agent-built web (rionet / rio). |

---

## §5 — Identity: the Eternity rappid

Every organism has one global identity, the **rappid**. The current canonical form is the **Eternity rappid** (CONSTITUTION Art. XXXIV.1, locked 2026-06-03):

```
rappid:@<owner>/<slug>:<64hex>
```

- `<64hex>` is a **keyless identity hash** — the SHA-256 of the master public key for keyed organisms, or a stable UUID/commit-derived hash for keyless ones — computed **independent of the slug** (it is the join key, **never** the SHA-256 of `<owner>/<slug>`).
- The `@<owner>/<slug>` segment is **self-locating** — it points directly at `github.com/<owner>/<slug>`.
- The **kind** (`twin`, `neighborhood`, `operator`, …) lives in the `rappid.json` record, **not** in the string.

Example:

```
rappid:@kody-w/heimdall:5f3c...e21a
```

Mint a rappid in Python (keyless organism — the hash is independent of the slug):

```python
import hashlib, uuid
owner_repo = "kody-w/heimdall"                        # location sugar only
hex64 = hashlib.sha256(uuid.uuid4().bytes).hexdigest()  # keyless: stable UUID-derived;
                                                        # keyed: sha256(master_pubkey_SPKI)
rappid = f"rappid:@{owner_repo}:{hex64}"              # minted once, preserved on every re-hatch
```

Legacy `rappid:v2:…` strings are **read forever and canonicalized on read** (`tools/door_address.py::canonicalize_rappid`) — never re-minted. There is exactly **one** parser (`door_from_rappid`); per-consumer parsers are forbidden (Article XLVI). Invalid rappids raise an error and are reissued, never patched.

From a rappid you can reach nine canonical URLs with no auth:

```
https://raw.githubusercontent.com/<owner>/<slug>/main/rappid.json
                                              .../card.json
                                              .../holo.md
                                              .../holo.svg
                                              .../holo-qr.svg
                                              .../members.json
                                              .../facets.json
                                              .../soul.md
https://<owner>.github.io/<slug>/              (the front door)
```

That property — *the address computes the location* — is what makes the network un-censorable. Nobody has to register you; nobody can de-register you.

---

## §6 — The two surfaces: agent and door

Every organism has exactly two faces, and they never overlap:

- **The agent / `/chat` surface** — what the LLM uses. Single-file agents serve the LLM through the brainstem's `POST /chat` endpoint. **Agent-first rule: every rapplication MUST work fully through the agent alone.**
- **The door / organ surface** — what humans and HTTP clients see. Organs (`*_organ.py`, dispatched via `/api/<name>/<path>`) serve UIs. The front door is a static page anyone can open; the doorman is the chat view behind it.

The door is always **optional** — it is a view, not the application. An organism with no front door at all is a *dark door*; it is still fully usable through its agent.

---

## §7 — Eggs: the universal cartridge

An **`.egg`** is a self-describing, SHA-256-sealed cartridge of an organism (or a piece of one). It is the single sneakernet primitive across the whole ecosystem — same extension, same Pokédex shelf, trade it via QR scan, WebRTC tether, USB, a PR, a dropped Issue, or the public egg-hub. It hatches identically on any kernel that supports the schema. **Two phones in the woods with no internet can trade one.** That is a contract, not a feature.

The cartridge family (all `brainstem-egg/*` or `rapp-egg/*`):

| Schema | Carries |
|---|---|
| `brainstem-egg/2.2-organism` | full instance cartridge (rappid + soul + .env + agents + organs + senses + services + .brainstem_data) |
| `brainstem-egg/2.2-rapplication` | single-rapp cartridge (rappid + agent + UI + per-rapp state) |
| `brainstem-egg/2.3-session` | a live multi-participant tether, made portable |
| `brainstem-egg/2.3-neighborhood` *(planned)* | a neighborhood gate, made portable |
| `brainstem-egg/2.3-estate` *(planned)* | an operator's whole multi-tier identity, portable across substrates |
| `brainstem-egg/2.3-cubby` | a member's private estate slice / cubby, portable + offline (per §8) |

One universal hatcher (`@rapp/egg_hatcher`) introspects the manifest and routes by kind; it **refuses** on unknown kinds rather than guessing.

---

## §8 — Private cubbies & dark doors

Most of the public model is open by default. But real work involves people and PII, so RAPP ships the inverse from minute one:

- **Two-tier estate (mandatory, Article XLVIII):** every operator gets BOTH a public estate (`<handle>/rapp-estate`, the discovery surface) AND a private estate (`<handle>/rapp-estate-private`, a PRIVATE repo, the substance surface) on first publish. A public-only estate is a "toy"; the two-tier model is the substrate for doctors-and-patients, families-with-PII, professional networks.
- **URL opacity (Article XLVIII.6):** every path inside the private repo is HMAC'd opaque. The operator's HMAC secret lives at `~/.brainstem/private-estate-secret` (mode 0600) and **never leaves the box**.
- **Private (dark-door) neighborhoods:** a neighborhood repo can be PRIVATE — collaborator-gated, with no public front door. Members reach it via invite + join; a private neighborhood with no front door at all uses a "payphone dialer" rather than a public summon. Each member gets a **cubby** — their own full estate slice inside the gate — and cubbies are portable as eggs and work offline.

The trust anchor throughout is **GitHub collaborator status**. There is no separate PKI: who can read the private repo is who you added as a collaborator.

---

## §9 — Governance & drift: how the truth stays one truth

The ecosystem is described in many places at once, on purpose, so that any divergence is *detectable*. The authority order when two docs disagree:

1. `MASTER_PLAN.md` — the first-principles north star.
2. `CONSTITUTION.md` — repo governance (40+ articles).
3. The spec docs (`SPEC` / `skill` / `ECOSYSTEM` / `NEIGHBORHOOD_PROTOCOL` / `OSI` / `ESTATE_SPEC`).
4. The vault (`Decisions/` + `Architecture/` essays — the *why*).
5. Code — last, because code rots and the spec is canonical.

Four independent representations of the same truth form the **drift triangle** (see [`DRIFT_TRIANGLE.md`](DRIFT_TRIANGLE.md)): the one agent's action enum, rapp-god's spec, rapp-map's byte-identical mirror, and this Bible. The agent's `action=verify` self-checks all four legs; the `ecosystem-sync` swarm re-derives the whole spec from the live ecosystem and reconciles any drift. No single point can silently rot.

---

## §10 — The one agent

The entire ecosystem is reachable through **one single-file agent**: `rapp_agent.py`, published as `@rapp/rapp` in [RAR](https://github.com/kody-w/RAR). Drop that ONE file into a brainstem's `agents/` directory and an operator can, through natural language alone, use the entire ecosystem end-to-end.

Its model is **navigator + bootstrapper + core-operator + universal-installer**. It does not reimplement all ~30 specialists — the ecosystem is built FROM single-file agents, so the god agent *reaches* them. Its superpower is `install`: pull any agent from RAR / the stores / a neighborhood's RAR on demand. It is airdroppable and offline-safe — it embeds a baseline of the whole map so it works in the woods, and `refresh` re-syncs from the global grail when online.

Read [`THE_ONE_AGENT.md`](THE_ONE_AGENT.md) for the full 41-action surface, grouped, with the operator journeys.

---

## §11 — The metropolis vision (where this is going)

Operators subscribe to many neighborhoods; the union is their estate. Estates mesh through shared neighborhoods; the mesh is the **metropolis**. Just as a city's zoning is not declared top-down — it emerges from which communities which people join for which purposes — the AI metropolis emerges from which neighborhoods which operators subscribe to for which outcomes. RAPP does not plan the city; it gives the substrate and the shape so the city builds itself.

The user is in the loop **async, not synchronous**. Agents do work in zones across the metropolis on behalf of their operator; work products attribute back to the operator's rappid; results land in the estate inbox; the user checks back when they want to. The network does not stop because someone went to bed.

> **The network is the engine. Once it has enough nodes, it builds itself out.**

---

## Where to go next

- [`THE_ONE_AGENT.md`](THE_ONE_AGENT.md) — the agent that makes all of this reachable through natural language.
- [`CAPABILITIES.md`](CAPABILITIES.md) — every capability domain, honestly: native vs install-routed vs specialist-owned.
- [`SCHEMAS.md`](SCHEMAS.md) — the full schema registry.
- [`DRIFT_TRIANGLE.md`](DRIFT_TRIANGLE.md) — how the four legs stay in sync.
- [`SPEC/_index.md`](SPEC/_index.md) — the mirrored canonical specs.
- [`repos/_index.md`](repos/_index.md) — one page per repo.
- [`quickstart/install.md`](quickstart/install.md) — zero → running → planting → joining → sharing.
