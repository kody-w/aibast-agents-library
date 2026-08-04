# The drift triangle — how four representations stay one truth

> *Renders the `drift_triangle` and `mirrors` sections of [`ecosystem-spec.json`](https://raw.githubusercontent.com/kody-w/rapp-god/main/api/v1/ecosystem-spec.json) v1.2.0.*

The RAPP ecosystem is described in **four independent places at once** — on purpose. If there were one description, it could silently rot and nobody would notice. With four, any divergence between them *is* drift, and drift is mechanically detectable.

> **Purpose:** four independent representations of the same truth so any divergence is detectable. No single point can silently drift.

It is called a "triangle" because the geometry of mutual cross-checks (the two grail mirrors compare byte-for-byte, the agent's enum must cover the spec, the Bible must be pinned) forms a closed figure of constraints. In practice there are **four legs**.

---

## The four legs

| Leg | What it holds | Where it lives |
|---|---|---|
| **`rapp_agent.py`** | The executable contract — its **action enum** is the capability surface. | `@rapp/rapp` in [kody-w/RAR](https://github.com/kody-w/RAR) + `rapp_brainstem/agents/` |
| **rapp-god** | This `ecosystem-spec.json` (machine) + `ECOSYSTEM_SPEC.md` (human). The registry observatory. | `kody-w/rapp-god/api/v1/ecosystem-spec.json` |
| **rapp-map** | A **byte-identical** copy of `ecosystem-spec.json` + `ECOSYSTEM_SPEC.md`. The ecosystem index + neuron mesh. | `kody-w/rapp-map/ecosystem-spec.json` |
| **RAPP-Bible** | The human-facing **rendering** of the spec — the one-source share you are reading now. | `kody-w/RAPP-Bible` |

`ecosystem-spec.json` is published **byte-identical** to two independent grail repos (rapp-god and rapp-map). The same content, two hosts, so a tampered or stale copy stands out the moment you compare:

```
rapp-god: https://raw.githubusercontent.com/kody-w/rapp-god/main/api/v1/ecosystem-spec.json
rapp-map: https://raw.githubusercontent.com/kody-w/rapp-map/main/ecosystem-spec.json
human:    https://kody-w.github.io/RAPP-Bible/   (this Bible, rendering the spec)
```

---

## The four checks

The `verify` action (and the `ecosystem-sync` swarm) runs these:

1. **`sha256(rapp-god/ecosystem-spec.json) == sha256(rapp-map/ecosystem-spec.json)`** — the two independent mirrors must match byte-for-byte. Any divergence between them is drift.
2. **`rapp_agent.py` action enum ⊇ `ecosystem-spec.json.required_actions`** — the agent must implement at least every required action. The spec can describe a capability; if the agent's enum doesn't carry the action, the capability is a `to_close` gap, not a live feature.
3. **`RAPP-Bible spec_version == ecosystem-spec.json.version`** — the Bible must be pinned to the spec it renders. **This Bible renders v1.2.0, sha256 `f1ddcf7e1302a82195fa682ad94140d0d066bbe60647befc5030ec5b50507e9e`.** (v1.2.0's headline addition is the `lexicon` pointer: `LEXICON.md` at the species root is the canon language file — Constitution Article LII; it seals at rapp-body genesis.)
4. **Every `capability_domain` capability tagged `native` maps to a live action in the agent's enum** — no native capability is claimed without a real action behind it.

---

## How drift gets caught and fixed

```
rapp_agent.py  action=verify
   ├─ fetch rapp-god/ecosystem-spec.json   ─┐
   ├─ fetch rapp-map/ecosystem-spec.json   ─┤  sha256 compare → mirrors agree?
   ├─ read own metadata action enum        ─┘  enum ⊇ required_actions?
   ├─ read RAPP-Bible spec_version          → == spec.version?
   └─ for each native capability            → action exists in enum?
        ↓
   any failure = drift, named with its leg
```

One agent self-checks all four legs. When something *has* drifted — a new action shipped but the spec wasn't bumped, or the two mirrors diverged, or the Bible's pin lagged — you don't patch one leg in isolation. You summon the **`ecosystem-sync` swarm**: it re-derives the whole spec from the **live** ecosystem (the agent's real enum, the actual repos, the real schemas) and reconciles drift across all four legs at once. Then the spec is re-published byte-identical to rapp-god and rapp-map, the Bible re-pins, and `verify` goes green again.

This is the governance contract in one sentence: **the truth is described four times so it can never quietly become four different truths.**

---

## What this means for you, the reader

- If you want the **freshest** machine truth, fetch either mirror and diff them — if they match, you have canon.
- If you want the **human** truth, you're reading it. This Bible is pinned to `ecosystem-spec.json` **v1.2.0**.
- If you find this Bible disagreeing with the spec JSON, **the JSON wins** and this Bible is the leg that drifted — open an issue or a PR against [kody-w/RAPP-Bible](https://github.com/kody-w/RAPP-Bible).
- If you are building on the ecosystem and add a capability, the loop is: ship the agent action → bump the spec → publish to both mirrors → re-pin the Bible → `verify` green.

*Authority: `ecosystem-spec.json` v1.2.0 `drift_triangle` + `mirrors`. The `verify` action is the executable form of this page.*
