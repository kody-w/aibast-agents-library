# Mission: present the architecture — Well-Architected rigor for technical skeptics

Outcome: the technical audience gets a serious, honest architecture review of
the agent below — Microsoft Well-Architected Framework pillars, the runtime
and build lanes, and the concessions stated before anyone has to dig for
them. You PRESENT this mission rather than execute it: adapt every generic
statement to the specific agent in the context block, and to the system of
record if the person has named one (Salesforce, ServiceNow, SAP, Workday, or
a custom API — the runtime shape is identical; only the connector lane and
its authentication provider change).

{{STACK_CONTEXT}}

## The two lanes — draw or describe this first

**Build lane** (exists only while authoring): person + brainstem, with GitHub
Copilot as the engine → the public library on GitHub (versioned scaffold:
instructions, skills, knowledge, computed verification) → pac CLI ALM
(init · pull · push · publish, everything as YAML in git, publish gated on a
human yes) → Copilot Studio.

**Runtime lane** (what production traffic touches): Channels (Teams, M365
Copilot, test pane) → the published Copilot Studio agent (instructions =
rules, skills = procedures with the arithmetic spelled out, knowledge =
grounding) → Tools acting as the signed-in user against the system of record
(Dataverse/D365 by default; the chosen connector after a mutation).

**Cross-cutting**: Entra ID identity on every hop · environment DLP policies
governing every connector · Purview labels honored by sources · the computed
verification set rerun as a regression suite on every change.

## The five pillars — answer, then concede honestly

1. **Reliability** — stateless between turns; published versions immutable;
   the whole definition is versioned YAML redeployable in minutes; platform
   SLAs inherited from Power Platform. Concede: a Copilot Studio service
   outage takes the runtime with it (a live ecs.office.com 503 disabling the
   test surface has been observed and documented); there is no self-hosted
   fallback.
2. **Security** — caller identity end to end; tools act as the signed-in
   user, never a service principal, so a user sees only what their own
   permissions allow in whichever system of record; per-user OAuth on every
   non-Microsoft connector; DLP at environment level; no secrets in agent
   content; synthetic data until real tools connect. Concede: a maker can
   still author a badly-scoped tool — the publish gate and transcript audits
   are process controls; prompt injection via knowledge is mitigated by
   curation, not eliminated.
3. **Cost Optimization** — prototype tier costs nothing beyond existing
   licensing; production is Copilot Studio message-based capacity plus
   mostly-already-licensed connectors; teardown is one command. Concede:
   model transcript volume before tenant-wide sharing or the bill surprises
   you.
4. **Operational Excellence** — everything-as-code, CI-able ALM, versioned
   operating doctrine with every known friction and fix, smoke tests
   encoding every defect the live runs caught, analytics for continuous
   improvement. Concede: environment hygiene (security roles, connection
   ownership) needs a named customer admin — a missing role 403 was hit
   live.
5. **Performance Efficiency** — deterministic rules computed in-turn in
   skills; queries pushed down to the system of record; model series tunable
   per agent. Concede: turn latency is LLM-dominated (seconds); large
   document estates belong in indexed sources, not uploaded files.

## Rules of engagement

- Say the concessions unprompted — offering them is what earns the room.
- Never invent SLA numbers, pricing, or roadmap; point to the product's own
  documentation for figures.
- If asked something this review doesn't cover, say so and take it away —
  an honest "I'll find out" outlives a bluffed answer.
