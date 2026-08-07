# Grant Lifecycle and Budget Reference

> SYNTHETIC — DEMO DATA. This workflow and category reference is illustrative
> and does not reflect any specific jurisdiction's adopted grant policy. This
> file exists so the agent has a working world to answer from on day one. In
> production, replace this file with tools that read your adopted grants policy,
> procurement manual, and chart of accounts (see the README's production
> section).

## Application workflow

Six phases, in fixed order. The portfolio records a grant *status*, not a step
number — never claim a specific grant has reached a specific step unless the
data says so.

### 1. Pre Application

| # | Step |
|---|------|
| 1 | Identify funding opportunity |
| 2 | Review NOFO requirements |
| 3 | Assess eligibility |
| 4 | Obtain internal authorization |

### 2. Application

| # | Step |
|---|------|
| 1 | Prepare project narrative |
| 2 | Develop budget justification |
| 3 | Gather required certifications |
| 4 | Complete SF-424 forms |
| 5 | Submit via grants.gov or state portal |

### 3. Post Submission

| # | Step |
|---|------|
| 1 | Confirm receipt |
| 2 | Respond to clarification requests |
| 3 | Await award notification |

### 4. Award Setup

| # | Step |
|---|------|
| 1 | Execute grant agreement |
| 2 | Set up grant fund codes in ERP |
| 3 | Establish reporting calendar |
| 4 | Notify department leads |

### 5. Implementation

| # | Step |
|---|------|
| 1 | Procure goods/services per grant terms |
| 2 | Track expenditures against budget |
| 3 | Submit progress reports |
| 4 | Monitor compliance |

### 6. Closeout

| # | Step |
|---|------|
| 1 | Complete final expenditure report |
| 2 | Submit final performance report |
| 3 | Return unused funds |
| 4 | Archive documentation |

## Status definitions

| Status | Meaning | Appears in budget tracking? |
|--------|---------|-----------------------------|
| application_submitted | Filed with the grantor; no decision returned | No |
| pending_award | Decision expected; grant agreement not executed | No |
| active | Awarded and executing; funds may be spent and encumbered | Yes |

Budget tracking covers `active` grants unless a specific grant id is named.
Application status covers `pending_award` and `application_submitted` only.

## Budget categories

| Category | Description |
|----------|-------------|
| Personnel | Salaries, wages, and fringe benefits |
| Contractual | Professional services and subcontracts |
| Equipment | Capital equipment over $5,000 |
| Supplies | Office and operational supplies |
| Travel | Staff travel and training |
| Indirect | Indirect cost allocation |
| Other | Miscellaneous direct costs |

The $5,000 threshold is the only numeric line between Equipment and Supplies in
this reference. Allowability of any specific cost is a grants manager call, not
an agent call.

## Financial formulas

| Measure | Formula |
|---------|---------|
| Available (per grant) | `amount - spent - encumbered` |
| Burn rate | `(spent + encumbered) / amount`, rounded to one decimal percent |
| Local match obligation | `amount * match_required` |
| Portfolio available | `total awards - total spent - total encumbered` |

Local match is a jurisdiction obligation held outside the award. It is never
subtracted from available and never added to the award amount. Match in this
portfolio ranges from 10% (LG-2025-003) to 50% (LG-2025-005).
