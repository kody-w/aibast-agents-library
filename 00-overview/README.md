# AIBAST Agents Library Overview

**AIBAST Frontier is an early, experimental learning lane: learn it now, prove it works, land it native.**

> **Template.** These runbooks and agents are examples. They cover the full path to a production build and must be modified to meet each customer's specific requirements. The customer or their partner connects them to their own systems, identity, data and governance in their environment.

Choose the path that fits your engagement: learn and teach in
AIBAST Frontier (experimental), use assisted authoring, or build directly in Copilot Studio
([Ask HR field guide example](../solutions/ask-hr/FIELD-GUIDE.md)).

| Benefit | What You Do | Source |
| --- | --- | --- |
| Learn it now | Learn, teach, and change a workflow's behavior immediately in AIBAST Frontier (experimental). | [Product Golden Path](../CLAUDE.md#product-golden-path) |
| Prove it | Replay locked cases and retain their evidence; distinguish synthetic workflow proof from customer results. | [Release gate and claims policy](../solutions/README.md) |
| Land it native | Build and validate Microsoft-native Copilot Studio skills, then follow the integration, evaluation, rollout, and operating steps for the target environment. | [Production delivery spine](#production-delivery-spine), [Ask HR delivery modes example](../solutions/ask-hr/FIELD-GUIDE.md) |
| Keep it current | Update source files, regenerate the runbooks, and revalidate changed inputs rather than reusing old acceptance. | [Generated runbooks](../solutions/README.md), [source integrity](../docs/RELEASE-PROCESS.md#workshop-source-integrity) |

Unfamiliar terms are defined in the [Glossary](../03-references/Glossary.md).

## Template Responsibilities

Templates cover the full path to a production build: agent behavior, the
synthetic data contract, integration and identity designs, an evaluation
suite, and playbooks for pilot, rollout, and operation.
The customer or partner adapts the template to specific requirements and
wires their own systems, identity and access, data, thresholds, approvals,
governance, and publishing in their environment
([package contract](../solutions/README.md),
[Ask HR customer gate example](../solutions/ask-hr/FIELD-GUIDE.md#evidence-gates)).

## What the AIBAST Agents Library Is

AIBAST is the Artificial Intelligence Business Applications Specialist Team.
The library combines industry agent templates with **AIBAST Frontier (experimental)**, a
learning tool
([Constitution](../CONSTITUTION.md),
[Product Golden Path](../CLAUDE.md#product-golden-path)). The library's positioning is
**"engine, not experience"**: reusable infrastructure rather than a consumer
product ([repository guidance](../CLAUDE.md)).

In AIBAST Frontier (experimental), the local Brainstem is a learning and
prototyping environment. Prove a workflow there, then adapt it for the
appropriate Microsoft deployment surface; the local prototype is not the product to ship
([project introduction](../README.md)).

Technical documentation: AIBAST Frontier runs on RAPP — see the
[production guide](https://microsoft.github.io/aibast-agents-library/docs/rapp-guide.html)
and the [Glossary](../03-references/Glossary.md).

### Three Tiers

The tiers describe deployment choices, not agent quality ratings. Each tier
is self-contained; using all three is not mandatory
([architecture and tier definitions](../CLAUDE.md),
[agent quality tiers](../CONSTITUTION.md#article-v--quality-tiers)).

| Tier | Name | Runtime and Delivery Surface |
| --- | --- | --- |
| 1 | Brainstem | Local Flask server using GitHub Copilot for the agent conversation and tool-calling loop. |
| 2 | Spinal Cord | Azure Functions and Azure OpenAI for the cloud-hosted layer. |
| 3 | Nervous System | Copilot Studio and Teams for the Microsoft 365 delivery layer. |

### Packages and Readers

A **solution package** is the set of workshop, deployment, manual-build,
evaluation, screenshot, and export assets under `solutions/<slug>/`. It sits
beside the portable Python agent; it does not replace the agent's single-file
contract ([package structure](../solutions/README.md),
[Single File Principle](../CONSTITUTION.md)).

| Reader | Start With |
| --- | --- |
| Field or delivery engineer | The solution overview, architecture, deployment recipe, and production replacement seams. |
| Workshop facilitator or learner | The field guide and guided workshop; choose the default Copilot-assisted lane or the optional Brainstem track. |
| Reviewer or business owner | The synthetic evidence, manual reproduction steps, acceptance cases, and publication boundary. |

These reading paths follow the [Ask HR field guide example](../solutions/ask-hr/FIELD-GUIDE.md)
and [Building Permit Processing package example](../solutions/building-permit-processing/README.md).

*AIBAST Frontier is an open-source learning library published in the Microsoft GitHub organization. It is not a Microsoft product, is not part of the Microsoft Frontier program, and does not confer Microsoft AI Cloud Partner Program badges or designations.*

Agent templates must be customized before production use
([Constitution](../CONSTITUTION.md),
[contribution guidance](../CONTRIBUTING.md)).

## Two Delivery Lanes

AIBAST Frontier is an early, experimental learning lane: one portable agent file holds the behavior and synthetic data so you can learn, teach, and change it immediately.
The Runbook lane builds the same agent by hand in Copilot Studio and needs no Python or local tooling.

Both lanes are kept on purpose; neither replaces the other
([source-of-truth boundaries](../solutions/README.md#source-of-truth-boundaries),
[Product Golden Path](../CLAUDE.md#product-golden-path)).
See the [Ask HR Manual mode example](../solutions/ask-hr/FIELD-GUIDE.md#manual-mode--literal-browser-construction).

| Lane | How You Use It |
| --- | --- |
| AIBAST Frontier (experimental) | Learn, teach, and change behavior immediately in the Brainstem (Tier 1). One portable `agent.py` carries the solution's behavior and synthetic data. See the [Product Golden Path](../CLAUDE.md#product-golden-path), [Single File Principle](../CONSTITUTION.md#article-ii--the-single-file-principle), [runtime ownership](../solutions/README.md#source-of-truth-boundaries), and [tier definitions](../CLAUDE.md#architecture-three-tiers). |
| Runbook lane | In Phase 2, build the Microsoft-native form from instructions, knowledge, and **Copilot Studio skills**. The manual build includes browser construction, model selection, and Preview. See the [Ask HR Manual mode example](../solutions/ask-hr/FIELD-GUIDE.md#manual-mode--literal-browser-construction) and [Ask HR source-controlled skill example](../solutions/ask-hr/copilot-studio/behaviors/aibast_leave-balance.mcs.yml). |

AIBAST Frontier (experimental) is a local learning tool that feeds Microsoft-native Copilot
Studio skills, following the
[Microsoft downstream path](../beta/GOLDEN_PATH.md#microsoft-downstream-path).

**Easy mode is the assisted middle path:** GitHub Copilot authors, reviews,
pushes, and validates the same Copilot Studio project
([source-of-truth boundaries](../solutions/README.md#source-of-truth-boundaries),
[Ask HR Easy mode example](../solutions/ask-hr/FIELD-GUIDE.md#easy-mode--github-copilot-default)).

These are alternative build choices within **Phase 2 — Build and Prove the
Agent**, not consecutive delivery phases. The full
[Phase 0–6 spine](#production-delivery-spine) also covers qualification,
environment preparation, customer integration, evaluation, rollout, and
operation.

Each runbook's `1.Overview.md` includes a **Delivery Lanes** comparison with
repository counts. See
[Lane Complexity at a Glance](../01-solutions/README.md#lane-complexity-at-a-glance)
for the library-wide table. Keep counts in these generated tables rather
than duplicating them here.

## How the Library Is Organized

The numbered spine presents the delivery questions in order. The existing
packages, runtime agents, Academy, and site remain their own surfaces
([package boundaries](../solutions/README.md),
[library and Academy introduction](../README.md)).

| Location | Purpose | Start Here If… |
| --- | --- | --- |
| [00-overview/](README.md) | Purpose, navigation, runbook anatomy, and solution taxonomy. | You are new to the library. |
| [01-solutions/](../01-solutions/README.md) | Generated production-template runbooks, organized by catalog solution. | You need the Phase 0–6 delivery path and its ownership boundaries. |
| [02-patterns/](../02-patterns/README.md) | Reusable practices and links to complementary AI Agent Runbooks patterns. | You need to resolve a repeated architecture or delivery question. |
| [03-references/](../03-references/README.md) | Glossary and process references. | You need a term, governing rule, or release procedure. |
| [solutions/](../solutions/README.md) | Original solution packages: source, workshop materials, evidence, and exports. | You need the actual build inputs or recorded evidence. |
| [agents/](../agents/@aibast-agents-library/) | Portable Python templates grouped into industry stacks. | You need to inspect or adapt runtime behavior. |
| [Microsoft AI Academy](https://microsoft.github.io/aibast-agents-library/academy.html) | Workshop learning and reusable skills. | You want a guided learning path. |
| [Library site](https://microsoft.github.io/aibast-agents-library/) | Searchable agent catalog with vertical filters and install commands. | You want to browse by industry or find a template. |

The initial runbooks are **Ask HR** and **Building Permit Processing**;
additional solutions are added one by one after their per-solution notes
are authored and validated ([package contract](../solutions/README.md)).
Use the [solution index](../01-solutions/README.md) to distinguish an available
runbook from its underlying package. The projection does not move or replace
the package sources.

## Anatomy of a Solution Runbook

Read artifacts 1 through 4 in order; use resources and acceptance evidence
alongside them. The source links below show the package inputs behind each
artifact, rather than a second place to maintain those facts. Package-specific
links are labeled examples from Ask HR or Building Permit Processing; the
catalog, registry, and package contract apply library-wide.

| Artifact | Delivery Question and Source Mapping |
| --- | --- |
| `0.Resources/README.md` | Where are the inputs and sources? The full source ledger and links to package assets, workshop pages, evidence, and exports; see the [Ask HR package map example](../solutions/ask-hr/README.md). |
| `1.Overview.md` | Why this solution, and for whom? Uses [catalog business copy](../solutions/catalog.json), [registry personas](../registry.json), and the [Ask HR scope and approval boundary example](../solutions/ask-hr/README.md). |
| `2.Architecture.md` | What is the design and who owns each part? Covers component responsibilities, the data contract, integration points, identity and permissions, the single component inventory, state and recovery, design decisions, and non-functional considerations; inputs include [catalog architecture](../solutions/catalog.json) and the [Ask HR deployment recipe example](../solutions/ask-hr/deployment.json). |
| `3.Runbook.md` | How do I deliver and operate it? Prerequisites, owner-tagged numbered steps and exit criteria across [Phases 0–6](#production-delivery-spine), followed by separate Template and Customer or partner deliverables. Build-lane selection occurs in Phase 2. |
| `4.Sample-prompts.md` | What should I test, and what must never happen? A per-case acceptance matrix and boundary tests, using catalog prompts, the [Ask HR locked cases example](../tests/demo_cases/ask-hr.json), [Ask HR canonical transcripts example](../solutions/ask-hr/evals/transcripts.json), and [Ask HR global instructions example](../solutions/ask-hr/manual/GLOBAL-INSTRUCTIONS.md). |
| `5.Acceptance-Evidence.md` | What evidence is recorded? Optional summary when the package contains evidence JSON or visual checkpoints; inspect the [Ask HR evaluation files example](../solutions/ask-hr/evals/) and [Ask HR evidence boundary example](../solutions/ask-hr/FIELD-GUIDE.md). |

Parts 1–5 cite sources inline; each `Next` section links to the full source
ledger in `0.Resources/README.md`. They do not repeat a `Sources` section.

## Production Delivery Spine

`3.Runbook.md` follows the same end-to-end delivery shape as AI Agent
Runbooks. Prerequisites name an owner, every numbered step belongs to
**Template** or **Customer or partner**, and every phase ends with
**Exit criteria** ([template model](../solutions/README.md)).

| Delivery Phase | Purpose |
| --- | --- |
| Phase 0 — Qualify and Adapt the Template | Qualify the use case, record a problem baseline, adapt scope and the data contract, and name owners. |
| Phase 1 — Environment, Identity and Access | Prepare the target environment and confirm identity, access, and policy requirements. |
| Phase 2 — Build and Prove the Agent | Choose one alternative build lane and verify a Draft on synthetic data with the locked cases replayed. |
| Phase 3 — Wire In Your Systems | Connect each declared integration read-only first; keep writes behind approval. |
| Phase 4 — Evaluate on Your Data | Rerun locked cases and boundary tests on customer data using thresholds set by the customer's business owner. |
| Phase 5 — Pilot and Rollout | Resolve go/no-go, publication, sharing, channels, audiences, and approvals. |
| Phase 6 — Operate | Establish ALM, monitoring, content freshness, re-verification, and recovery. |

The final **Deliverables Checklist** separates **Template provides** from
**Customer or partner delivers**. Workshop integrity rules belong to Phase 2;
operational recovery is covered by Architecture's **State and Recovery** and
Phase 6, rather than a separate Runbook **Failure Recovery** section.
Delivery phase numbers are not repository rollout milestones.

## Solution Taxonomy

The generated table joins the [solution catalog](../solutions/catalog.json)
and [registry](../registry.json) to show solution coverage by vertical and
normalized journey stage.

<!-- BEGIN GENERATED: solution-taxonomy (tools/build_solution_runbooks.py) -->

| Vertical | Solutions | Journey stages |
| --- | --- | --- |
| B2B Sales | [Account Intelligence Agent](../01-solutions/account-intelligence/1.Overview.md) | Understand |
| B2B Sales | [Deal Progression Agent](../01-solutions/deal-progression/1.Overview.md) | Optimize |
| B2B Sales | [Proposal Generation Agent](../01-solutions/proposal-generation/1.Overview.md) | Create |
| B2B Sales | [Sales Qualification Agent](../01-solutions/sales-qualification/1.Overview.md) | Prioritize |
| B2B Sales | [Win/Loss Analysis Agent](../solutions/win-loss-analysis/README.md) | Learn |
| B2C Sales | [Cart Abandonment Recovery Agent](../01-solutions/cart-abandonment-recovery/1.Overview.md) | Recover / Learn (secondary) |
| B2C Sales | [Customer Loyalty and Rewards Agent](../01-solutions/customer-loyalty-rewards/1.Overview.md) | Retain / Optimize (secondary) |
| B2C Sales | [Omnichannel Engagement Agent](../01-solutions/omnichannel-engagement/1.Overview.md) | Understand / Optimize (secondary) |
| B2C Sales | [Personalized Shopping Agent](../01-solutions/personalized-shopping-assistant/1.Overview.md) | Discover / Advise (secondary) |
| Cross-Industry | [Cross-Selling Opportunities Agent](../01-solutions/cross-selling/1.Overview.md) | Expand |
| Cross-Industry | [Customer Escalations Agent](../01-solutions/ai-customer-assistant/1.Overview.md) | Serve |
| Cross-Industry | [Discount Finder Agent](../01-solutions/procurement-support/1.Overview.md) | Optimize |
| Cross-Industry | [Procurement Agent](../01-solutions/procurement-agent/1.Overview.md) | Optimize |
| Energy | [Asset Maintenance Forecast Agent](../01-solutions/asset-maintenance-forecast/1.Overview.md) | Optimize |
| Energy | [Emissions Tracking Agent](../01-solutions/emission-tracking/1.Overview.md) | Govern |
| Energy | [Field Service Dispatch Agent](../01-solutions/field-service-dispatch/1.Overview.md) | Serve |
| Energy | [Permit Management Agent](../01-solutions/permit-license-management/1.Overview.md) | Govern |
| Energy | [Regulatory Reporting Agent](../01-solutions/energy-regulatory-reporting/1.Overview.md) | Govern |
| Financial Services | [Claims Processing Agent](../01-solutions/claims-processing/1.Overview.md) | Decide |
| Financial Services | [Customer Onboarding Agent](../01-solutions/fs-customer-onboarding/1.Overview.md) | Govern |
| Financial Services | [Customer Sentiment and Churn Prediction Agent](../01-solutions/customer-sentiment-churn/1.Overview.md) | Engage |
| Financial Services | [Financial Advisor Agent](../01-solutions/financial-advisor-copilot/1.Overview.md) | Engage |
| Financial Services | [Fraud Detection and Alert Agent](../01-solutions/fraud-detection-alert/1.Overview.md) | Protect |
| Financial Services | [Loan Origination Assistant](../01-solutions/loan-origination-assistant/1.Overview.md) | Decide |
| Financial Services | [Portfolio Rebalancing Agent](../01-solutions/portfolio-rebalancing/1.Overview.md) | Optimize |
| Financial Services | [Regulatory Compliance Agent](../01-solutions/fs-regulatory-compliance/1.Overview.md) | Govern |
| Financial Services | [Underwriting Support Agent](../solutions/underwriting-support/README.md) | Decide |
| Financial Services | [Wealth Insights Generator Agent](../solutions/wealth-insights-generator/README.md) | Engage |
| Healthcare | [Care Gap Closure Agent](../01-solutions/care-gap-closure/1.Overview.md) | Govern |
| Healthcare | [Clinical Notes Summarizer Agent](../01-solutions/clinical-notes-summarizer/1.Overview.md) | Activate |
| Healthcare | [Patient Intake and Scheduling Agent](../01-solutions/patient-intake/1.Overview.md) | Activate |
| Healthcare | [Prior Authorization Agent](../01-solutions/prior-authorization/1.Overview.md) | Govern |
| Human Resources | [Ask HR Agent](../01-solutions/ask-hr/1.Overview.md) | Empower |
| Manufacturing | [Inventory Rebalancing Agent](../01-solutions/inventory-rebalancing/1.Overview.md) | Optimize |
| Manufacturing | [Maintenance Scheduling Agent](../01-solutions/maintenance-scheduling/1.Overview.md) | Optimize |
| Manufacturing | [Order Status Communications Agent](../01-solutions/order-status-communication/1.Overview.md) | Serve |
| Manufacturing | [Product Line Optimization Agent](../01-solutions/product-line-optimization/1.Overview.md) | Optimize |
| Manufacturing | [Supply Risk Monitoring Agent](../solutions/supplier-risk-monitoring/README.md) | Protect |
| Professional Services | [Client Health Score Agent](../01-solutions/client-health-score/1.Overview.md) | Optimize |
| Professional Services | [Contract Risk Review Agent](../01-solutions/contract-risk-review/1.Overview.md) | Govern |
| Professional Services | [Resource Utilization Agent](../01-solutions/resource-utilization/1.Overview.md) | Optimize |
| Professional Services | [Time Entry and Billing Agent](../solutions/time-entry-billing/README.md) | Operate |
| Retail & CPG | [Inventory Visibility Agent](../01-solutions/inventory-visibility/1.Overview.md) | Plan / Fulfill (secondary) |
| Retail & CPG | [Personalized Marketing Agent](../01-solutions/personalized-marketing/1.Overview.md) | Plan / Evaluate (secondary) |
| Retail & CPG | [Retail Store Associate Copilot](../01-solutions/store-associate-copilot/1.Overview.md) | Serve / Coordinate (secondary) |
| Retail & CPG | [Returns and Complaints Resolution Agent](../01-solutions/returns-complaints-resolution/1.Overview.md) | Resolve / Learn (secondary) |
| Retail & CPG | [Supply Chain Disruption Alert Agent](../solutions/supply-chain-disruption-alert/README.md) | Optimize |
| SLG Government | [Building Permit Processing Agent](../01-solutions/building-permit-processing/1.Overview.md) | Govern |
| SLG Government | [Utility Billing and Assistance Agent](../solutions/utility-billing-assistance/README.md) | Serve |
| Software & Digital Products | [License Renewal and Expansion Agent](../01-solutions/license-renewal-expansion/1.Overview.md) | Retain |
| Software & Digital Products | [Product Feedback Synthesizer Agent](../01-solutions/product-feedback-synthesizer/1.Overview.md) | Innovate |

<!-- END GENERATED: solution-taxonomy -->

## Journey Stages

For the runbook index, each catalog journey stage is normalized to a primary
stage: take the text before ` and ` and capitalize its first letter. For
example, `Serve and coordinate` is grouped under `Serve`; the original
[catalog value](../solutions/catalog.json) is not changed. A journey stage
describes the workflow's role, not readiness or permission to publish.

## Claims and Synthetic-Data Policy

The [package claims policy](../solutions/README.md) applies to runbooks and
workshop delivery:

- Use qualitative business claims, such as improves, reduces, accelerates,
  strengthens, or protects.
- Label synthetic demo evidence clearly. Synthetic figures are not customer
  results or performance commitments.
- Do not treat a recorded case as a customer KPI, a live-system result, or
  production-readiness evidence. A screenshot proves only its visible state
  ([Ask HR evidence boundary example](../solutions/ask-hr/FIELD-GUIDE.md)).
- Keep real customer names, personal data, and credentials out of published
  template source and example evidence
  ([Agent Constitution](../agents/@aibast-agents-library/AGENT_CONSTITUTION.md),
  [repository Constitution](../CONSTITUTION.md)).
- Keep the Phase 2 synthetic build in Draft; publishing belongs to the
  separately approved pilot and rollout in Phase 5. Passing source checks
  is not native Copilot Studio acceptance
  ([Ask HR delivery gates example](../solutions/ask-hr/FIELD-GUIDE.md),
  [workshop source integrity](../docs/RELEASE-PROCESS.md)).

## Relationship to Microsoft AI Agent Runbooks

This spine follows the same overview, solution/scenario, pattern, and reference
structure as `microsoft/ai-agent-runbooks`. Use the
[pattern reuse table](../02-patterns/README.md#reuse-from-ai-agent-runbooks)
for its delivery guidance, including
[Enterprise RAG Pattern](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Enterprise-RAG-Pattern/Enterprise-RAG-Pattern.md)
and
[Human-in-the-Loop Review & Approval](https://github.com/microsoft/ai-agent-runbooks/blob/main/02-patterns/Human-in-the-Loop-Review-and-Approval/Human-in-the-Loop-Review-and-Approval.md).

The scope is complementary: AIBAST supplies portable agent implementations,
synthetic workflow evidence, workshop build inputs, and exports
([package contract](../solutions/README.md)); the reuse table points to shared
implementation guidance instead of duplicating it. Consult the
[reference index](../03-references/README.md) for the companion delivery
library and limitations guide.

## How to Contribute

Follow [CONTRIBUTING.md](../CONTRIBUTING.md) for agent requirements, validation,
and the staging release path. Correct package facts in their
[source-of-truth files](../solutions/README.md), not in generated runbooks.
For a reusable practice, see
[How to add a pattern](../02-patterns/README.md#how-to-add-a-pattern).

## Regenerating the Runbooks

After updating the source files, run from the repository root:

```text
python tools/build_solution_runbooks.py
```

This refreshes the generated solution runbooks and the taxonomy block above.
Keep narrative edits outside the taxonomy markers; package source ownership
remains as defined in [solutions/README.md](../solutions/README.md).
