# AIBAST Agents Library Overview

**AIBAST Frontier is an early, experimental learning lane: learn it now, prove it works, land it native.**

Choose the path that fits your engagement: learn and teach in
AIBAST Frontier (experimental), use assisted authoring, or build directly in Copilot Studio
([Ask HR field guide example](../solutions/ask-hr/FIELD-GUIDE.md)).

| Benefit | What You Do | Source |
| --- | --- | --- |
| Learn it now | Learn, teach, and change a workflow's behavior immediately in AIBAST Frontier (experimental). | [Product Golden Path](../CLAUDE.md#product-golden-path) |
| Prove it | Replay locked cases and retain their evidence; distinguish synthetic workflow proof from customer results. | [Release gate and claims policy](../solutions/README.md) |
| Land it native | Build and validate Microsoft-native Copilot Studio skills through Easy mode or the independent manual build. | [Ask HR delivery modes example](../solutions/ask-hr/FIELD-GUIDE.md) |
| Keep it current | Update source files, regenerate the runbooks, and revalidate changed inputs rather than reusing old acceptance. | [Generated runbooks](../solutions/README.md), [source integrity](../docs/RELEASE-PROCESS.md#workshop-source-integrity) |

Unfamiliar terms are defined in the [Glossary](../03-references/Glossary.md).

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
| Runbook lane | Build the Microsoft-native form from instructions, knowledge, and **Copilot Studio skills**. The AI Agent Runbooks-style documents guide manual browser construction, model selection, and Preview. See the [Ask HR Manual mode example](../solutions/ask-hr/FIELD-GUIDE.md#manual-mode--literal-browser-construction) and [Ask HR source-controlled skill example](../solutions/ask-hr/copilot-studio/behaviors/aibast_leave-balance.mcs.yml). |

AIBAST Frontier (experimental) is a local learning tool that feeds Microsoft-native Copilot
Studio skills, following the
[Microsoft downstream path](../beta/GOLDEN_PATH.md#microsoft-downstream-path).

**Easy mode is the assisted middle path:** GitHub Copilot authors, reviews,
pushes, and validates the same Copilot Studio project
([source-of-truth boundaries](../solutions/README.md#source-of-truth-boundaries),
[Ask HR Easy mode example](../solutions/ask-hr/FIELD-GUIDE.md#easy-mode--github-copilot-default)).

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
artifact, rather than a second place to maintain those facts. Package-specific
links are labeled examples from Ask HR or Building Permit Processing; the
catalog, registry, and release gate apply library-wide.

| Artifact | Delivery Question and Source Mapping |
| --- | --- |
| `0.Resources/README.md` | Where are the inputs? Links to the package's source, manual kit, workshops, screenshots, and exports; see the [Ask HR package map example](../solutions/ask-hr/README.md). |
| `1.Overview.md` | Why this solution, and for whom? Uses [catalog business copy](../solutions/catalog.json), [registry personas](../registry.json), and the [Ask HR scope and approval boundary example](../solutions/ask-hr/README.md). |
| `2.Architecture.md` | How is it built? Uses [catalog architecture](../solutions/catalog.json), package components, and the [Building Permit Processing replacement seams example](../solutions/building-permit-processing/FIELD-GUIDE.md). |
| `3.Runbook.md` | How do I reproduce and validate it? Uses the [Ask HR deployment recipe example](../solutions/ask-hr/deployment.json), [Ask HR Easy and Manual modes example](../solutions/ask-hr/FIELD-GUIDE.md), and [release gate](../solutions/README.md). |
| `4.Sample-prompts.md` | What should I test, and what must never happen? Uses catalog prompts, [Ask HR locked cases example](../tests/demo_cases/ask-hr.json), [Ask HR canonical transcripts example](../solutions/ask-hr/evals/transcripts.json), and [Ask HR global instructions example](../solutions/ask-hr/manual/GLOBAL-INSTRUCTIONS.md). |
| `5.Acceptance-Evidence.md` | What evidence is recorded? Optional summary when the package contains evidence JSON or visual checkpoints; inspect the [Ask HR evaluation files example](../solutions/ask-hr/evals/) and [Ask HR evidence boundary example](../solutions/ask-hr/FIELD-GUIDE.md). |

## Solution Taxonomy

The generated table joins the [solution catalog](../solutions/catalog.json)
and [registry](../registry.json) to show solution coverage by vertical and
normalized journey stage.

<!-- BEGIN GENERATED: solution-taxonomy (tools/build_solution_runbooks.py) -->

| Vertical | Solutions | Journey stages |
| --- | --- | --- |
| B2B Sales | [Account Intelligence Agent](../solutions/account-intelligence/README.md) | Understand |
| B2B Sales | [Deal Progression Agent](../solutions/deal-progression/README.md) | Optimize |
| B2B Sales | [Proposal Generation Agent](../solutions/proposal-generation/README.md) | Create |
| B2B Sales | [Sales Qualification Agent](../solutions/sales-qualification/README.md) | Prioritize |
| B2B Sales | [Win/Loss Analysis Agent](../solutions/win-loss-analysis/README.md) | Learn |
| B2C Sales | [Cart Abandonment Recovery Agent](../solutions/cart-abandonment-recovery/README.md) | Recover / Learn (secondary) |
| B2C Sales | [Customer Loyalty and Rewards Agent](../solutions/customer-loyalty-rewards/README.md) | Retain / Optimize (secondary) |
| B2C Sales | [Omnichannel Engagement Agent](../solutions/omnichannel-engagement/README.md) | Understand / Optimize (secondary) |
| B2C Sales | [Personalized Shopping Agent](../solutions/personalized-shopping-assistant/README.md) | Discover / Advise (secondary) |
| Cross-Industry | [Cross-Selling Opportunities Agent](../solutions/cross-selling/README.md) | Expand |
| Cross-Industry | [Customer Escalations Agent](../solutions/ai-customer-assistant/README.md) | Serve |
| Cross-Industry | [Discount Finder Agent](../solutions/procurement-support/README.md) | Optimize |
| Cross-Industry | [Procurement Agent](../solutions/procurement-agent/README.md) | Optimize |
| Energy | [Asset Maintenance Forecast Agent](../solutions/asset-maintenance-forecast/README.md) | Optimize |
| Energy | [Emissions Tracking Agent](../solutions/emission-tracking/README.md) | Govern |
| Energy | [Field Service Dispatch Agent](../solutions/field-service-dispatch/README.md) | Serve |
| Energy | [Permit Management Agent](../solutions/permit-license-management/README.md) | Govern |
| Energy | [Regulatory Reporting Agent](../solutions/energy-regulatory-reporting/README.md) | Govern |
| Financial Services | [Claims Processing Agent](../solutions/claims-processing/README.md) | Decide |
| Financial Services | [Customer Onboarding Agent](../solutions/fs-customer-onboarding/README.md) | Govern |
| Financial Services | [Customer Sentiment and Churn Prediction Agent](../solutions/customer-sentiment-churn/README.md) | Engage |
| Financial Services | [Financial Advisor Agent](../solutions/financial-advisor-copilot/README.md) | Engage |
| Financial Services | [Fraud Detection and Alert Agent](../solutions/fraud-detection-alert/README.md) | Protect |
| Financial Services | [Loan Origination Assistant](../solutions/loan-origination-assistant/README.md) | Decide |
| Financial Services | [Portfolio Rebalancing Agent](../solutions/portfolio-rebalancing/README.md) | Optimize |
| Financial Services | [Regulatory Compliance Agent](../solutions/fs-regulatory-compliance/README.md) | Govern |
| Financial Services | [Underwriting Support Agent](../solutions/underwriting-support/README.md) | Decide |
| Financial Services | [Wealth Insights Generator Agent](../solutions/wealth-insights-generator/README.md) | Engage |
| Healthcare | [Care Gap Closure Agent](../solutions/care-gap-closure/README.md) | Govern |
| Healthcare | [Clinical Notes Summarizer Agent](../solutions/clinical-notes-summarizer/README.md) | Activate |
| Healthcare | [Patient Intake and Scheduling Agent](../solutions/patient-intake/README.md) | Activate |
| Healthcare | [Prior Authorization Agent](../solutions/prior-authorization/README.md) | Govern |
| Human Resources | [Ask HR Agent](../01-solutions/ask-hr/1.Overview.md) | Empower |
| Manufacturing | [Inventory Rebalancing Agent](../solutions/inventory-rebalancing/README.md) | Optimize |
| Manufacturing | [Maintenance Scheduling Agent](../solutions/maintenance-scheduling/README.md) | Optimize |
| Manufacturing | [Order Status Communications Agent](../solutions/order-status-communication/README.md) | Serve |
| Manufacturing | [Product Line Optimization Agent](../solutions/product-line-optimization/README.md) | Optimize |
| Manufacturing | [Supply Risk Monitoring Agent](../solutions/supplier-risk-monitoring/README.md) | Protect |
| Professional Services | [Client Health Score Agent](../solutions/client-health-score/README.md) | Optimize |
| Professional Services | [Contract Risk Review Agent](../solutions/contract-risk-review/README.md) | Govern |
| Professional Services | [Resource Utilization Agent](../solutions/resource-utilization/README.md) | Optimize |
| Professional Services | [Time Entry and Billing Agent](../solutions/time-entry-billing/README.md) | Operate |
| Retail & CPG | [Inventory Visibility Agent](../solutions/inventory-visibility/README.md) | Plan / Fulfill (secondary) |
| Retail & CPG | [Personalized Marketing Agent](../solutions/personalized-marketing/README.md) | Plan / Evaluate (secondary) |
| Retail & CPG | [Retail Store Associate Copilot](../solutions/store-associate-copilot/README.md) | Serve / Coordinate (secondary) |
| Retail & CPG | [Returns and Complaints Resolution Agent](../solutions/returns-complaints-resolution/README.md) | Resolve / Learn (secondary) |
| Retail & CPG | [Supply Chain Disruption Alert Agent](../solutions/supply-chain-disruption-alert/README.md) | Optimize |
| SLG Government | [Building Permit Processing Agent](../01-solutions/building-permit-processing/1.Overview.md) | Govern |
| SLG Government | [Utility Billing and Assistance Agent](../solutions/utility-billing-assistance/README.md) | Serve |
| Software & Digital Products | [License Renewal and Expansion Agent](../solutions/license-renewal-expansion/README.md) | Retain |
| Software & Digital Products | [Product Feedback Synthesizer Agent](../solutions/product-feedback-synthesizer/README.md) | Innovate |

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
- Keep real customer names, personal data, and credentials out of agent
  content ([Agent Constitution](../agents/@aibast-agents-library/AGENT_CONSTITUTION.md),
  [repository Constitution](../CONSTITUTION.md)).
- Keep workshop agents in Draft. Publishing requires separate human approval;
  passing source checks is not native Copilot Studio acceptance
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
