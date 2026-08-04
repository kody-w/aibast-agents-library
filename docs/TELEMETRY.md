# Telemetry — the aibast.tooling.v1 event contract

Every AIBAST TA tool (RAPP, AIDEATE, LIBRARY, DMT, SOWAGENT) emits one
minimal, uniform event: **ToolInteractionEvent**. Schema:
[`schemas/tool-interaction-event.schema.json`](../schemas/tool-interaction-event.schema.json)
· emitter: [`scripts/telemetry.py`](../scripts/telemetry.py).

```json
{
  "eventId"         : "guid",
  "eventName"       : "rapp.prototype.generated",
  "toolId"          : "RAPP | AIDEATE | LIBRARY | DMT | SOWAGENT",
  "toolVersion"     : "semver",
  "correlationId"   : "guid",         // one per engagement, end to end
  "msxOpportunityId": "string|null",  // MANDATORY for L3/L4 credit
  "tpid"            : "string|null",  // consumption joins here
  "actorRole"       : "TA | SE | GBB | PARTNER | ISD",  // role, not name
  "actorRegion"     : "AMER | EMEA | APAC | LATAM",
  "programId"       : "SFRC | ERP | CCAS | AGENTS | LOWCODE",
  "outcome"         : "success | failure | abandoned",
  "durationMs"      : "int",          // powers every speed KPI
  "timestampUtc"    : "iso8601"
}
```

## The four rules

1. **Six events, that's all** — `created · started · completed · failed ·
   deployed · shared` (plus `generated` for RAPP's signature moment).
   Uniform verbs across every tool so one query serves all.
2. **Correlation ID is the spine** — issued at first touch, carried through
   AIdeate → RAPP → Library → deployment. Without it there is no funnel.
3. **MSX ID is the price of credit** — no opportunity ID, no L3/L4
   attribution. Make it the rule everywhere.
4. **Role, never person** — `actorRole` + `actorRegion` only. This is the
   guardrail that lets the tooling ship without a trust problem.

## Prohibited in any payload

Prompts, responses, customer data, document contents, individual user
identity. The contract enforces this structurally: the schema sets
`additionalProperties: false`, and the emitter rejects unknown keys AND
name-matches a denylist (`prompt`, `response`, `customer`, `document`,
`user`, `email`, …) so prohibited content has nowhere to ride.

## Where events go — and where they never go

Events POST to the internal collector named by the
**`AIBAST_TELEMETRY_ENDPOINT`** environment variable. With no endpoint
configured, the emitter validates and returns the event without sending —
tools work offline and nothing is spooled to disk. **Business identifiers
(`msxOpportunityId`, `tpid`) exist only in flight to the internal
collector. They are never written into this repository, its `state/`
snapshots, or the public metrics dashboard** — the public
[metrics page](../metrics.html) shows only anonymous, aggregate,
public-API-sourced numbers. The two systems are deliberately disjoint.

## Emitting

```python
from telemetry import emit                       # scripts/ on the path
emit("library.agent.deployed", tool_id="LIBRARY", tool_version="1.0.0",
     correlation_id=engagement_cid, actor_role="SE", actor_region="EMEA",
     program_id="AGENTS", outcome="success", duration_ms=elapsed_ms,
     msx_opportunity_id=opp_id)                  # mandatory for L3/L4 credit
```

```bash
python3 scripts/telemetry.py --event-name rapp.prototype.generated \
  --tool-id RAPP --tool-version 1.0.0 --actor-role TA --actor-region AMER \
  --program-id AGENTS --outcome success --duration-ms 5321 --dry-run
```

A contract violation raises/exits non-zero and the event is dropped loudly —
a bad event is never sent, and telemetry failure never breaks the tool.
