# AIBAST Agents Library Overview

Start here to choose a solution, inspect its implementation, reproduce its
synthetic workflow, and identify what still needs approval before production.
The package [field guides](../solutions/ask-hr/FIELD-GUIDE.md) support that
delivery sequence. Unfamiliar terms are defined in the
[Glossary](../03-references/Glossary.md).

## What the AIBAST Agents Library Is

AIBAST is the Artificial Intelligence Business Applications Specialist Team.
The library publishes industry agent templates for RAPP, the Rapid Agent
Prototype Pattern ([Constitution](../CONSTITUTION.md)). Its positioning is
**"engine, not experience"**: reusable infrastructure rather than a consumer
product ([repository guidance](../CLAUDE.md)).

The local Brainstem is a learning and prototyping environment. Prove a
workflow there, then adapt it for the appropriate Microsoft deployment
surface; the local prototype is not the product to ship
([project introduction](../README.md)).

### Three Tiers

The tiers describe deployment choices, not agent quality ratings. Each tier
is self-contained; using all three is not mandatory
([architecture and tier definitions](../CLAUDE.md)).

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

These reading paths follow the [Ask HR field guide](../solutions/ask-hr/FIELD-GUIDE.md)
and [Building Permit Processing package](../solutions/building-permit-processing/README.md).

The repository is an experimental project managed by an AIBAST v-team, not
an officially supported Microsoft product. Its agent templates must be
customized before production use ([Constitution](../CONSTITUTION.md),
[contribution guidance](../CONTRIBUTING.md)).

## How the Library Is Organized

The numbered spine presents the delivery questions in order. The existing
packages, runtime agents, Academy, and site remain their own surfaces
([package boundaries](../solutions/README.md),
[library and Academy introduction](../README.md)).

| Location | Purpose | Start Here If… |
| --- | --- | --- |
| [00-overview/](README.md) | Purpose, navigation, runbook anatomy, and solution taxonomy. | You are new to the library. |
| [01-solutions/](../01-solutions/README.md) | Generated delivery runbooks, organized by catalog solution. | You need the build and acceptance path for a particular solution. |
| [02-patterns/](../02-patterns/README.md) | Reusable practices and links to complementary AI Agent Runbooks patterns. | You need to resolve a repeated architecture or delivery question. |
| [03-references/](../03-references/README.md) | Glossary and process references. | You need a term, governing rule, or release procedure. |
| [solutions/](../solutions/README.md) | Original solution packages: source, workshop materials, evidence, and exports. | You need the actual build inputs or recorded evidence. |
| [agents/](../agents/@aibast-agents-library/) | Portable Python templates grouped into industry stacks. | You need to inspect or adapt runtime behavior. |
| [Microsoft AI Academy](https://microsoft.github.io/aibast-agents-library/academy.html) | Workshop learning and reusable skills. | You want a guided learning path. |
| [Library site](https://microsoft.github.io/aibast-agents-library/) | Searchable agent catalog with vertical filters and install commands. | You want to browse by industry or find a template. |

Phase 1 provides runbooks for **Ask HR** and **Building Permit Processing**;
the remaining catalog solutions follow in Phase 2. Use the
[solution index](../01-solutions/README.md) to distinguish an available
runbook from its underlying package. The projection does not move or replace
the [package sources](../solutions/README.md).

## Anatomy of a Solution Runbook

Read artifacts 1 through 4 in order; use resources and acceptance evidence
alongside them. The source links below show the package inputs behind each
artifact, rather than a second place to maintain those facts.

| Artifact | Delivery Question and Source Mapping |
| --- | --- |
| `0.Resources/README.md` | Where are the inputs? Links to the package's source, manual kit, workshops, screenshots, and exports; see the [package map](../solutions/ask-hr/README.md). |
| `1.Overview.md` | Why this solution, and for whom? Uses [catalog business copy](../solutions/catalog.json), [registry personas](../registry.json), and the package's [scope and approval boundary](../solutions/ask-hr/README.md). |
| `2.Architecture.md` | How is it built? Uses [catalog architecture](../solutions/catalog.json), package components, and the field guide's [production replacement seams](../solutions/building-permit-processing/FIELD-GUIDE.md). |
| `3.Runbook.md` | How do I reproduce and validate it? Uses the [deployment recipe](../solutions/ask-hr/deployment.json), [Easy and Manual delivery modes](../solutions/ask-hr/FIELD-GUIDE.md), and [release gate](../solutions/README.md). |
| `4.Sample-prompts.md` | What should I test, and what must never happen? Uses catalog prompts, [locked cases](../tests/demo_cases/ask-hr.json), [canonical transcripts](../solutions/ask-hr/evals/transcripts.json), and [global instructions](../solutions/ask-hr/manual/GLOBAL-INSTRUCTIONS.md). |
| `5.Acceptance-Evidence.md` | What evidence is recorded? Optional summary when the package contains evidence JSON or visual checkpoints; inspect the original [evaluation files](../solutions/ask-hr/evals/) and their [evidence boundary](../solutions/ask-hr/FIELD-GUIDE.md). |

## Solution Taxonomy

The generated table joins the [solution catalog](../solutions/catalog.json)
and [registry](../registry.json) to show solution coverage by vertical and
normalized journey stage.

<!-- BEGIN GENERATED: solution-taxonomy (tools/build_solution_runbooks.py) -->

| Vertical | Solutions | Journey stages |
| --- | --- | --- |
| B2B Sales | [Account Intelligence Agent](../solutions/account-intelligence/README.md)<br>[Deal Progression Agent](../solutions/deal-progression/README.md)<br>[Proposal Generation Agent](../solutions/proposal-generation/README.md)<br>[Sales Qualification Agent](../solutions/sales-qualification/README.md)<br>[Win/Loss Analysis Agent](../solutions/win-loss-analysis/README.md) | Create<br>Learn<br>Optimize<br>Prioritize<br>Understand |
| B2C Sales | [Cart Abandonment Recovery Agent](../solutions/cart-abandonment-recovery/README.md)<br>[Customer Loyalty and Rewards Agent](../solutions/customer-loyalty-rewards/README.md)<br>[Omnichannel Engagement Agent](../solutions/omnichannel-engagement/README.md)<br>[Personalized Shopping Agent](../solutions/personalized-shopping-assistant/README.md) | Discover / Advise (secondary)<br>Recover / Learn (secondary)<br>Retain / Optimize (secondary)<br>Understand / Optimize (secondary) |
| Cross-Industry | [Cross-Selling Opportunities Agent](../solutions/cross-selling/README.md)<br>[Customer Escalations Agent](../solutions/ai-customer-assistant/README.md)<br>[Discount Finder Agent](../solutions/procurement-support/README.md)<br>[Procurement Agent](../solutions/procurement-agent/README.md) | Expand<br>Optimize<br>Serve |
| Energy | [Asset Maintenance Forecast Agent](../solutions/asset-maintenance-forecast/README.md)<br>[Emissions Tracking Agent](../solutions/emission-tracking/README.md)<br>[Field Service Dispatch Agent](../solutions/field-service-dispatch/README.md)<br>[Permit Management Agent](../solutions/permit-license-management/README.md)<br>[Regulatory Reporting Agent](../solutions/energy-regulatory-reporting/README.md) | Govern<br>Optimize<br>Serve |
| Financial Services | [Claims Processing Agent](../solutions/claims-processing/README.md)<br>[Customer Onboarding Agent](../solutions/fs-customer-onboarding/README.md)<br>[Customer Sentiment and Churn Prediction Agent](../solutions/customer-sentiment-churn/README.md)<br>[Financial Advisor Agent](../solutions/financial-advisor-copilot/README.md)<br>[Fraud Detection and Alert Agent](../solutions/fraud-detection-alert/README.md)<br>[Loan Origination Assistant](../solutions/loan-origination-assistant/README.md)<br>[Portfolio Rebalancing Agent](../solutions/portfolio-rebalancing/README.md)<br>[Regulatory Compliance Agent](../solutions/fs-regulatory-compliance/README.md)<br>[Underwriting Support Agent](../solutions/underwriting-support/README.md)<br>[Wealth Insights Generator Agent](../solutions/wealth-insights-generator/README.md) | Decide<br>Engage<br>Govern<br>Optimize<br>Protect |
| Healthcare | [Care Gap Closure Agent](../solutions/care-gap-closure/README.md)<br>[Clinical Notes Summarizer Agent](../solutions/clinical-notes-summarizer/README.md)<br>[Patient Intake and Scheduling Agent](../solutions/patient-intake/README.md)<br>[Prior Authorization Agent](../solutions/prior-authorization/README.md) | Activate<br>Govern |
| Human Resources | [Ask HR Agent](../01-solutions/ask-hr/1.Overview.md) | Empower |
| Manufacturing | [Inventory Rebalancing Agent](../solutions/inventory-rebalancing/README.md)<br>[Maintenance Scheduling Agent](../solutions/maintenance-scheduling/README.md)<br>[Order Status Communications Agent](../solutions/order-status-communication/README.md)<br>[Product Line Optimization Agent](../solutions/product-line-optimization/README.md)<br>[Supply Risk Monitoring Agent](../solutions/supplier-risk-monitoring/README.md) | Optimize<br>Protect<br>Serve |
| Professional Services | [Client Health Score Agent](../solutions/client-health-score/README.md)<br>[Contract Risk Review Agent](../solutions/contract-risk-review/README.md)<br>[Resource Utilization Agent](../solutions/resource-utilization/README.md)<br>[Time Entry and Billing Agent](../solutions/time-entry-billing/README.md) | Govern<br>Operate<br>Optimize |
| Retail & Consumer Goods | [Inventory Visibility Agent](../solutions/inventory-visibility/README.md)<br>[Personalized Marketing Agent](../solutions/personalized-marketing/README.md)<br>[Retail Store Associate Copilot](../solutions/store-associate-copilot/README.md)<br>[Returns and Complaints Resolution Agent](../solutions/returns-complaints-resolution/README.md)<br>[Supply Chain Disruption Alert Agent](../solutions/supply-chain-disruption-alert/README.md) | Optimize<br>Plan / Evaluate (secondary)<br>Plan / Fulfill (secondary)<br>Resolve / Learn (secondary)<br>Serve / Coordinate (secondary) |
| Software & Digital Products | [License Renewal and Expansion Agent](../solutions/license-renewal-expansion/README.md)<br>[Product Feedback Synthesizer Agent](../solutions/product-feedback-synthesizer/README.md) | Innovate<br>Retain |
| State & Local Government | [Building Permit Processing Agent](../01-solutions/building-permit-processing/1.Overview.md)<br>[Utility Billing and Assistance Agent](../solutions/utility-billing-assistance/README.md) | Govern<br>Serve |

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
  ([field-guide evidence boundary](../solutions/ask-hr/FIELD-GUIDE.md)).
- Keep real customer names, personal data, and credentials out of agent
  content ([Agent Constitution](../agents/@aibast-agents-library/AGENT_CONSTITUTION.md),
  [repository Constitution](../CONSTITUTION.md)).
- Keep workshop agents in Draft. Publishing requires separate human approval;
  passing source checks is not native Copilot Studio acceptance
  ([delivery gates](../solutions/ask-hr/FIELD-GUIDE.md),
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
