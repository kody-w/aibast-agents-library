# Underwriting Criteria and Document Requirements

> SYNTHETIC — DEMO DATA. These thresholds and checklists are fictional demo
> guidelines, not any lender's real credit policy. This file exists so the
> agent has a working world to answer from on day one. In production, replace
> this file with tools that read your real credit policy and condition matrix
> (see the README's production section).

## Approval criteria by product

| Product | Min Credit | Max DTI | Min Down % | Max LTV | Min DSCR |
|---------|------------|---------|------------|---------|----------|
| conventional_30yr | 620 | 45% | 5 | 95% | — |
| fha_30yr | 580 | 50% | 3.5 | 96.5% | — |
| va_30yr | 580 | 60% | 0 | 100% | — |
| commercial_5yr | 0 (no gate) | 0 (no gate) | 20 | 80% | 1.25 |

Reading the table:

- A threshold of 0 means **the gate does not run**. For `commercial_5yr` both
  the credit score and the DTI thresholds are 0, so commercial files are gated
  on LTV and DSCR only. A commercial DTI is computed and displayed, but nothing
  tests it.
- All comparisons are inclusive. A value exactly at the limit passes:
  LTV 96.5% against the FHA 96.5% ceiling is a Pass.
- `Min Down %` is recorded policy context; the gates actually evaluated are
  credit score, DTI, LTV, and DSCR.

## Decision rule

Applied after the gates produce an issue list:

| Condition | Recommendation | Rationale |
|-----------|----------------|-----------|
| No issues | Approve | All underwriting criteria met |
| Exactly one issue AND DTI <= 50 | Conditional Approve | Minor condition: `<the issue>` |
| Two or more issues, or one issue with DTI > 50 | Refer to Senior UW | All issues, joined with `; ` |

There is no Deny outcome. Files that cannot clear are referred to a senior
underwriter.

## Document requirements

Every application gets the four base categories. Exactly one product category
is appended, matched in this order: FHA, then VA, then commercial. A
conventional file gets no product category.

### Base categories

| Category | Documents |
|----------|-----------|
| Income | W-2 forms (last 2 years); Pay stubs (last 30 days); Tax returns (last 2 years); Employment verification letter |
| Assets | Bank statements (last 2 months); Investment account statements; Gift letter (if applicable) |
| Property | Purchase agreement; Appraisal report; Title search; Homeowners insurance quote |
| Identity | Government-issued photo ID; Social Security verification |

### Product-specific categories

| Category | Applies to | Documents |
|----------|-----------|-----------|
| FHA Specific | fha_30yr | FHA case number assignment; HUD-1 settlement statement |
| VA Specific | va_30yr | Certificate of Eligibility (COE); DD-214 or active duty proof |
| Commercial Specific | commercial_5yr | Business tax returns (3 years); Profit & loss statement; Rent roll; Environmental Phase I |

### Item counts

| Product | Base | Product-specific | Total |
|---------|------|------------------|-------|
| conventional_30yr | 13 | 0 | 13 |
| fha_30yr | 13 | 2 | 15 |
| va_30yr | 13 | 2 | 15 |
| commercial_5yr | 13 | 4 | 17 |

Receipt status is not tracked in this data. The checklist states what is
required, never what has been received or cleared.
