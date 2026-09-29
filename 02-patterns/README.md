# How to Use Patterns

Use a solution runbook for an end-to-end business workflow. Use a pattern for
a decision or implementation practice that recurs across workflows. The
[package contract](../solutions/README.md) supplies the build inputs and
evidence; this index makes the reusable practices easier to find.

## Patterns Versus Solutions

| Dimension | Solution | Pattern |
| --- | --- | --- |
| Starting Question | Which business workflow are we demonstrating or delivering? | Which repeated technical or delivery problem needs a consistent approach? |
| Scope | A named use case, its build inputs, and its acceptance evidence. | A practice applied within one or more solutions. |
| Reading Path | Overview, architecture, runbook, sample prompts, and recorded evidence. | Pattern overview followed by its implementation runbook. |
| Example | [Ask HR](../solutions/ask-hr/README.md): synthetic policy guidance and reviewable drafts. | Evidence-first acceptance: the shared [release gate](../solutions/README.md). |

The [Glossary](../03-references/Glossary.md) defines package and runtime terms.
The [pattern index](patterns.json) owns stable IDs, titles, status, links,
summaries, and applicability text. Keep this README aligned with it.

## AIBAST Patterns

All eight standalone pattern pairs are **Planned** for Phase 3. The table
points to existing evidence of each practice, not to unwritten pattern
documents. Planned status comes from [patterns.json](patterns.json).

| Pattern | Status | Summary | Use It When… | AIBAST Source |
| --- | --- | --- | --- | --- |
| Evidence-First Release Gate | Planned | Trace each one-pager promise through implemented behavior, isolated transcripts, static demos, and Copilot Studio replay. | Preparing a solution for the seven-step release gate. | [Package release gate](../solutions/README.md) |
| Synthetic-Snapshot Demo Agent | Planned | Keep portable behavior in one Python file and ground the manual pilot in a fixed synthetic snapshot. | Demonstrating workflow behavior before replacing synthetic inputs with approved sources. | [Single File Principle](../CONSTITUTION.md), [Ask HR snapshot](../solutions/ask-hr/manual/GLOBAL-INSTRUCTIONS.md) |
| Copilot Studio Skills and Global Instructions | Planned | Package routing, knowledge, and SKILL.md procedures with shared privacy, human-review, and side-effect gates. | Rebuilding the packaged agent in Copilot Studio without weakening its reviewed instructions. | [Global instructions](../solutions/ask-hr/manual/GLOBAL-INSTRUCTIONS.md), [example skill](../solutions/ask-hr/manual/skills/aibast_leave-balance_01/SKILL.md) |
| Easy and Manual Mode Workshop Delivery | Planned | Deliver the same reviewed agent through Copilot-assisted authoring or a literal manual browser build. | Choosing a workshop lane and checking instructions, knowledge, skills, model, and case parity. | [Field-guide delivery modes and gates](../solutions/ask-hr/FIELD-GUIDE.md) |
| Transcript-Replay Acceptance Testing | Planned | Replay the canonical persona-language corpus in the target runtime and check source-backed entities and decisions. | Testing routing and behavior before accepting a Draft or changing its implementation. | [Canonical transcripts](../solutions/ask-hr/evals/transcripts.json), [locked demo cases](../tests/demo_cases/ask-hr.json), [acceptance rules](../agents/@aibast-agents-library/AGENT_CONSTITUTION.md) |
| No-Terminal Deployment Recipe | Planned | Describe source retrieval, installation, expected tool, and smoke test in deployment.json. | Letting GitHub Copilot Agent mode install and verify an agent without asking the learner to open a terminal. | [Deployment recipe](../solutions/ask-hr/deployment.json), [recipe ownership](../solutions/README.md) |
| Brainstem to Copilot Studio Tier Promotion | Planned | Separate local Brainstem, Azure, and Copilot Studio responsibilities in three self-contained tiers. | Choosing a deployment tier after proving local behavior, without treating every tier as mandatory. | [Three-tier architecture](../CLAUDE.md), [local prototyping position](../README.md) |
| Visual Evidence and Browserfilm Capture | Planned | Retain real screenshot frames and a manifest to build an auditable walkthrough GIF and contact sheet. | Capturing workshop evidence without mock screens, customer data, credentials, or unapproved publication. | [Browserfilm capture and evidence rules](../tools/rapp-browserfilm.md) |

## Reuse from AI Agent Runbooks

These 17 overview/runbook pairs are linked through
[patterns.json](patterns.json), not copied into AIBAST. The application
summaries below concern AIBAST's source practices and possible delivery
decisions; they do not claim that a package implements every platform in a
linked pattern. A changed host or input still needs its own acceptance
evidence ([workshop source integrity](../docs/RELEASE-PROCESS.md)).

| Pattern | Runbook | AIBAST Application | Use It in AIBAST When… |
| --- | --- | --- | --- |
| [Agent Governance & Rollout Control Plane](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Agent-Governance-and-Rollout-Control-Plane/Agent-Governance-and-Rollout-Control-Plane.md) | [Runbook](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Agent-Governance-and-Rollout-Control-Plane/Agent-Governance-and-Rollout-Control-Plane-Runbook.md) | Separate workshop evidence from production approval and agreed governance. | Agreeing production connections, governance, telemetry, support, and success measures after a Draft workshop. [Source](../solutions/ask-hr/FIELD-GUIDE.md) |
| [Agent Publishing & Channel Deployment](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Agent-Publishing-and-Channel-Deployment/Agent-Publishing-and-Channel-Deployment.md) | [Runbook](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Agent-Publishing-and-Channel-Deployment/Agent-Publishing-and-Channel-Deployment-Runbook.md) | Keep a validated Draft separate from the decision to publish. | Planning publication only after replaying the acceptance corpus and receiving explicit human approval. [Release gate](../solutions/README.md), [Draft boundary](../solutions/ask-hr/FIELD-GUIDE.md) |
| [Agentic Workflow Orchestration](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Agentic-Workflow-Orchestration/Agentic-Workflow-Orchestration.md) | [Runbook](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Agentic-Workflow-Orchestration/Agentic-Workflow-Orchestration-Runbook.md) | Compose multiple agents around a business scenario. | Extending a multi-agent stack such as account intelligence while preserving isolated solution tests. [Stack inventory](../registry.json), [isolated acceptance](../agents/@aibast-agents-library/AGENT_CONSTITUTION.md) |
| [Branded Office Artifact Generation](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Branded-Office-Artifact-Generation/Branded-Office-Artifact-Generation.md) | [Runbook](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Branded-Office-Artifact-Generation/Branded-Office-Artifact-Generation-Runbook.md) | Preserve source evidence and claim boundaries in delivery artifacts. | Preparing Office deliverables from approved one-pager content without turning synthetic figures into customer claims. [One-pager contract](../agents/@aibast-agents-library/AGENT_CONSTITUTION.md), [claims policy](../solutions/README.md) |
| [Copilot Connector Knowledge Onboarding](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Copilot-Connector-Knowledge-Onboarding/Copilot-Connector-Knowledge-Onboarding.md) | [Runbook](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Copilot-Connector-Knowledge-Onboarding/Copilot-Connector-Knowledge-Onboarding-Runbook.md) | Replace synthetic knowledge with approved, least-privilege sources. | Evaluating an indexed knowledge option for the approved HR policy or permit-document replacement seam. [Approved connections](../solutions/catalog.json), [permit seams](../solutions/building-permit-processing/FIELD-GUIDE.md) |
| [Copilot Credits & Cost Control](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Copilot-Credits-Cost-Control/Copilot-Credits-Cost-Control.md) | [Runbook](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Copilot-Credits-Cost-Control/Copilot-Credits-Cost-Control-Runbook.md) | Review production consumption alongside deployment-tier choices. | Planning Azure or Copilot Studio use beyond the local prototype. [Deployment tiers](../CLAUDE.md), [production customer gate](../solutions/ask-hr/FIELD-GUIDE.md) |
| [Copilot Studio Migration & Modernisation](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Copilot-Studio-Migration-and-Modernisation/Copilot-Studio-Migration-and-Modernisation.md) | [Runbook](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Copilot-Studio-Migration-and-Modernisation/Copilot-Studio-Migration-and-Modernisation-Runbook.md) | Preserve the reviewed behavior contract when changing the delivery host. | Adapting a proven agent to Copilot Studio and replaying its canonical cases in the target environment. [Downstream direction](../beta/GOLDEN_PATH.md), [replay requirement](../solutions/README.md) |
| [Copilot Studio & Foundry Split Architecture](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Copilot-Studio-and-Foundry-Split-Architecture/Copilot-Studio-and-Foundry-Split-Architecture.md) | [Runbook](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Copilot-Studio-and-Foundry-Split-Architecture/Copilot-Studio-and-Foundry-Split-Architecture-Runbook.md) | Separate local proof, cloud execution, and end-user delivery. | Choosing responsibilities across Copilot Studio and Microsoft Foundry in the downstream path. [Microsoft downstream direction](../beta/GOLDEN_PATH.md) |
| [Cowork Skill Delivery and Scheduled Reviews](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Cowork-Skill-Delivery-and-Scheduled-Reviews/Cowork-Skill-Delivery-and-Scheduled-Reviews.md) | [Runbook](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Cowork-Skill-Delivery-and-Scheduled-Reviews/Cowork-Skill-Delivery-and-Scheduled-Reviews-Runbook.md) | Reuse reviewed instructions and skills without implying acceptance in another host. | Considering Cowork as an additional destination; the packaged skills and Preview evidence here are for Copilot Studio. [Manual build and Preview](../solutions/ask-hr/FIELD-GUIDE.md), [source-integrity rule](../docs/RELEASE-PROCESS.md) |
| [Declarative vs Custom Engine Agent](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Declarative-vs-Custom-engine-agent/Declarative-Agents-vs-Copilot-Studio-Custom-Engine-Agents.md) | [Runbook](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Declarative-vs-Custom-engine-agent/Declarative-Agents-vs-Copilot-Studio-Custom-Engine-Agents-Runbook.md) | Choose a downstream agent surface after proving the intended behavior. | Deciding how to deliver a proven workflow in Copilot Studio or Microsoft 365 Copilot rather than assuming the workshop fixes the agent type. [Microsoft downstream direction](../beta/GOLDEN_PATH.md) |
| [Enterprise RAG Pattern](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Enterprise-RAG-Pattern/Enterprise-RAG-Pattern.md) | [Runbook](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Enterprise-RAG-Pattern/Enterprise-RAG-Pattern-Runbook.md) | Keep production retrieval separate from the packaged synthetic snapshot. | Evaluating governed retrieval for approved HR policies or SharePoint permit documents. [HR boundary](../solutions/ask-hr/manual/GLOBAL-INSTRUCTIONS.md), [permit sources and seams](../solutions/building-permit-processing/manual/GLOBAL-INSTRUCTIONS.md) |
| [Governed Analytics Review](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Governed-Analytics-Review/Governed-Analytics-Review.md) | [Runbook](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Governed-Analytics-Review/Governed-Analytics-Review-Runbook.md) | Keep analytical decisions traceable to approved evidence and human review. | Replacing synthetic win-loss, client-health, emissions, or utilization inputs without presenting preliminary scores as verified results. [Scenario boundaries and intended connections](../solutions/catalog.json) |
| [Grounding & Response Quality Remediation](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Grounding-and-Response-Quality-Remediation/Grounding-and-Response-Quality-Remediation.md) | [Runbook](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Grounding-and-Response-Quality-Remediation/Grounding-and-Response-Quality-Remediation-Runbook.md) | Diagnose missing knowledge, inventory mismatch, and missing expected entities before accepting a run. | A Preview answer fails a locked case or the Easy and Manual inventories differ. [Failure recovery](../solutions/ask-hr/FIELD-GUIDE.md) |
| [Human-in-the-Loop Review & Approval](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Human-in-the-Loop-Review-and-Approval/Human-in-the-Loop-Review-and-Approval.md) | [Runbook](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Human-in-the-Loop-Review-and-Approval/Human-in-the-Loop-Review-and-Approval-Runbook.md) | Separate recommendations and drafts from authorized real-world actions. | Defining approval for HR decisions, permit changes, notifications, or other production writes. [HR gates](../solutions/ask-hr/manual/GLOBAL-INSTRUCTIONS.md), [permit gates](../solutions/building-permit-processing/manual/GLOBAL-INSTRUCTIONS.md) |
| [Intelligent Document Processing Pipeline](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Intelligent-Document-Processing-Pipeline/Intelligent-Document-Processing-Pipeline.md) | [Runbook](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Intelligent-Document-Processing-Pipeline/Intelligent-Document-Processing-Pipeline-Runbook.md) | Separate document evidence preparation from the final business decision. | Planning document handling for claims, authorization evidence, or permit intake while preserving the package's approval boundary. [Scenario copy](../solutions/catalog.json), [permit decision rules](../solutions/building-permit-processing/manual/GLOBAL-INSTRUCTIONS.md) |
| [MCP Federated Connectors](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/MCP-Federated-Connectors/MCP-Federated-Connectors.md) | [Runbook](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/MCP-Federated-Connectors/MCP-Federated-Connectors-Runbook.md) | Treat live retrieval as a future integration rather than a demonstrated connection. | Evaluating a federated option for approved external knowledge; the packaged permit pilot has no live MCP connection. [Pilot data boundary and production seams](../solutions/building-permit-processing/manual/GLOBAL-INSTRUCTIONS.md) |
| [MCP Server Integration](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/MCP-Server-Integration/MCP-Server-Integration.md) | [Runbook](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/MCP-Server-Integration/MCP-Server-Integration-Runbook.md) | Bind approved live-system tools at the production replacement seam. | Choosing a tool interface for approved system access while keeping external writes behind separate governance and human approval. [Production seams](../solutions/building-permit-processing/manual/GLOBAL-INSTRUCTIONS.md) |

## Pattern Folder Structure and Naming

For Phase 3 AIBAST pattern documents, use **Title-Case-With-Hyphens** for the
folder and matching document names:

```text
02-patterns/
└── <Name>/
    ├── <Name>.md
    └── <Name>-Runbook.md
```

| File | Purpose |
| --- | --- |
| `<Name>.md` | Explain the problem, when the pattern fits, design decisions, and evidence limits. |
| `<Name>-Runbook.md` | Give prerequisites, implementation steps, validation, and recovery. |

For example, the planned `Evidence-First-Release-Gate/` pair will use
`Evidence-First-Release-Gate.md` and `Evidence-First-Release-Gate-Runbook.md`.
Use the reserved folder value in [patterns.json](patterns.json); do not infer
external filenames from their display titles.

## How to Add a Pattern

This is the **Phase 3** contribution path; the planned pairs above are not
yet available.

1. Identify the repeated practice and cite the existing package or governing
   source. Keep its synthetic-data and approval boundaries explicit
   ([claims policy](../solutions/README.md)).
2. Use the existing stable ID and folder from [patterns.json](patterns.json),
   or register a new distinct ID for a genuinely new pattern.
3. Write both Title-Case-With-Hyphens documents. Include executable
   prerequisites and acceptance checks, not just a description of intent.
4. Update the index summary, applicability, and availability when the pair is
   complete; keep this README consistent. Never rename an ID already used
   by solution runbooks.
5. Reference the pattern ID in the relevant solution's
   [runbook notes](../solutions/runbook-notes.json), regenerate with
   `python tools/build_solution_runbooks.py`, and validate the generated links.
6. Follow [CONTRIBUTING.md](../CONTRIBUTING.md) and the
   [release process](../docs/RELEASE-PROCESS.md).

Return to the [solution runbooks](../01-solutions/README.md) to apply a
pattern within a specific workflow.
