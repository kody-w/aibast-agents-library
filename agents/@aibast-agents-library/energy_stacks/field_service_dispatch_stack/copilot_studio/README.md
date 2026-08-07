# Field Service Dispatch Agent — build it in Copilot Studio

`field_service_dispatch_agent.py` (one directory up) is the **intent**: what
this agent knows, what it computes, and the rules it never breaks. This folder
is that intent implemented as a native Copilot Studio **agentic-loop agent**,
authored the way Microsoft's Copilot Studio CLI authors one — as a `pac
copilot` project you push and publish, not a description you read.

Component layout and YAML conventions follow the
[microsoft/copilot-studio-plugin](https://github.com/microsoft/copilot-studio-plugin)
(`mcs-assistant`) authoring format for CLI-authored agents.

## How the intent maps to Copilot Studio

| In `agent.py` | Becomes | File here |
|---|---|---|
| Module docstring + guardrail behavior | Agent instructions | `instructions.md` → `settings.mcs.yml` |
| `operation: dispatch_dashboard` | Skill | `behaviors/dispatch-dashboard_fsd101.mcs.yml` |
| `operation: route_optimization` (incl. the utilization formula) | Skill | `behaviors/route-optimization_fsd102.mcs.yml` |
| `operation: technician_assignment` (incl. the scoring rule) | Skill | `behaviors/technician-assignment_fsd103.mcs.yml` |
| `operation: emergency_response` | Skill | `behaviors/emergency-response_fsd104.mcs.yml` |
| `TECHNICIANS`, `SERVICE_REQUESTS`, `GEOGRAPHIC_ZONES` | File knowledge (demo tier) | `capabilities/knowledge/files/field-service-operations-data.md` |
| The certification gate | Policy knowledge + instruction rule | `capabilities/knowledge/files/certification-and-dispatch-policy.md` |
| `zone` parameter | Scope-filter rule in instructions and every skill | — |

The deterministic rules (candidate eligibility, `score = efficiency + 10
in-zone + 5 available`, `utilization = (1 - capacity/slots) × 100`) live in
the **skills**, spelled out as arithmetic the agent must compute — not left to
model judgment. In production they move into tools (last section).

## Prerequisites

- A Power Platform environment where you can create agents, and its
  **environment ID** (Copilot Studio → Settings, or the maker portal URL).
- [Power Platform CLI](https://learn.microsoft.com/power-platform/developer/cli/introduction)
  (`pac`) **version 2.9.3 or later** — earlier versions do not have the
  CLI-authoring commands used here.
- Copilot Studio licensing in the tenant.

**The fast path — no commands, just conversation.** Download the library's
Sales Specialist Twin agent
(`agents/@aibast-agents-library/general_stacks/sales_specialist_twin_stack/sales_specialist_twin_agent.py`),
drop it into your brainstem's `agents/` folder, and say *"deploy the field
service dispatch agent to Copilot Studio."* GitHub Copilot fetches this
mission's playbook from the library (`twin/playbooks/deploy-copilot-studio.md`)
and executes every step below itself. The steps that follow are what the twin
does under the hood, documented so you can audit exactly what runs.

## Build

### 1. Authenticate

```
pac auth create
```

Complete the browser sign-in with an account that can create agents in the
target environment.

### 2. Create the agent project

```
pac copilot init \
  --name "Field Service Dispatch Agent" \
  --publisher-prefix aibast \
  --authoring-mode cli-copilot \
  --project-dir field-service-dispatch \
  --environment "<your-environment-id>"
```

This creates `field-service-dispatch/` containing `settings.mcs.yml` plus the
`behaviors/`, `capabilities/`, and `.mcs/` structure. Never hand-edit `.mcs/`
— it is CLI-managed state.

### 3. Copy the components in

From this folder, copy into the project you just created:

```
behaviors/*.mcs.yml                →  field-service-dispatch/behaviors/
capabilities/knowledge/files/*     →  field-service-dispatch/capabilities/knowledge/files/
```

### 4. Set the instructions

Open `field-service-dispatch/settings.mcs.yml`. Keep every generated field
(`schemaName`, environment binding, model, IDs) exactly as `pac` wrote it.
Set the instructions segment to the full contents of `instructions.md`:

```yaml
configuration:
  agentSettings:
    instructions:
      segments:
        - kind: StaticSegment
          value: |
            <paste the full contents of instructions.md here, indented to match>
```

### 5. Push, then publish

```
pac copilot pull --project-dir field-service-dispatch
pac copilot push --project-dir field-service-dispatch
pac copilot publish --bot "<schemaName from settings.mcs.yml>" --environment "<your-environment-id>"
```

Pull before push is the required order. **Publishing makes the agent live for
everyone it is shared with** — do it deliberately.

## Verify — the answers are checkable, not vibes

Open the agent in the Copilot Studio test pane (or Teams once shared) and ask
these. The expected results below are computed from the data, so a wrong
answer is visible:

1. **"Show me the dispatch dashboard."** → 5 requests, SR-4005 (CRITICAL)
   first, 4 unassigned, 3 available technicians.
2. **"Who should take SR-4001?"** → Marcus Thompson (TECH-205), score 107
   (92 + 10 in-zone + 5 not-on-a-job), beating Carlos Rivera (TECH-201) at 99
   (94 + 5) — in-zone outranks raw efficiency here. If the agent recommends
   Carlos, it is not applying the scoring rule.
3. **"Who can respond to the SCADA emergency?"** → exactly one eligible
   responder: Marcus Thompson, on break, already in Denver where the failure
   is. Anyone else named is a hallucination — no other technician holds
   `scada_systems`.
4. **"Assign the pipeline survey to Carlos Rivera."** → must refuse: Carlos
   does not hold `pipeline_inspection`, and the agent recommends rather than
   assigns. Both boundaries should appear in the answer.
5. **"Show the dashboard for the Central zone only."** → 3 requests, and the
   counts (not just the rows) reflect the filter.

If 2, 3, or 4 fail, the build is not done — fix before showing anyone.

## Production: swap the demo file for real tools

The operations-data file exists so the agent works on day one. A production
deployment replaces it with **tools** that read live systems — structured,
changing data should be queried, not RAG-searched:

- **SharePoint lists**: import `data/technicians.csv` and
  `data/service_requests.csv` as lists, then add SharePoint *Get items*
  connector tools in the Copilot Studio portal (Tools → Add → Connector),
  which binds the connection and generates the `capabilities/tools/*.mcs.yml`
  for you. Connector tool YAML carries tenant-specific connection references,
  which is why this folder does not ship pre-baked tool files.
- **Dynamics 365 Field Service**: if the tenant runs it, the roster and work
  orders already live in Dataverse (`bookableresource`, `msdyn_workorder`) —
  point Dataverse connector tools at those tables instead of lists.
- Keep the skills unchanged: they define the procedure and the arithmetic
  regardless of where the rows come from. Remove
  `field-service-operations-data.md` (and its `.mcs.yml` sidecar) once tools
  are connected, then re-run the five verification questions.

---

*Microsoft AI Business Applications Specialist Team (AIBAST). All data in
this folder is synthetic. Agent templates are starting points that must be
customized and reviewed before production use.*
