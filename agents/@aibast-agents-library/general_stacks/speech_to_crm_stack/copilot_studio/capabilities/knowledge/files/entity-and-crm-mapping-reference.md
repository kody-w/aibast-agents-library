# Entity Extraction and CRM Mapping Reference

> SYNTHETIC — DEMO DATA. Every entity, contact, amount, and CRM field value in
> this document is fictional and derived from the synthetic CALL-T001
> transcript. This file exists so the agent has a working world to answer from
> on day one. In production, replace this file with tools that read your real
> NLP extraction service and CRM schema (see the README's production section).

## Extracted entities — CALL-T001

| Type | Value | Confidence | Context |
|------|-------|------------|---------|
| person | Jennifer Walsh | 0.99 (99%) | Primary contact, VP Operations |
| person | Mark Davidson | 0.97 (97%) | CEO, economic buyer, wants proposal by Dec 15 |
| person | Sam Patel | 0.98 (98%) | IT Director, technical evaluator |
| organization | TechVantage Solutions | 0.99 (99%) | Prospect account |
| money | $200,000 | 0.98 (98%) | Approved budget for initiative |
| money | $50,000 | 0.95 (95%) | Annual cost of manual reporting |
| date | December 15 | 0.97 (97%) | CEO deadline for proposal |
| date | December 12 | 0.96 (96%) | Proposed review meeting date |
| pain_point | 20 hours/week manual reporting | 0.94 (94%) | 150 people affected across ops and finance |
| action_item | Send proposal by Dec 10 | 0.97 (97%) | Alex committed to deliver proposal |
| action_item | Schedule Dec 12 review meeting | 0.95 (95%) | Include Sam Patel for technical evaluation |

Counts by type, in first-appearance order: Person 3, Organization 1, Money 2,
Date 2, Pain_Point 1, Action_Item 2. Total entities: 11.

## CRM mapping — opportunity

| Field | Source | Mapped Value |
|-------|--------|--------------|
| name | organization + context | TechVantage Solutions - Enterprise Platform |
| amount | money entity | 200000 |
| close_date | date entity | 2025-12-15 |
| stage | conversation context | Proposal |
| probability | engagement signals | 65 |
| next_step | action_item entity | Send proposal by Dec 10, review meeting Dec 12 |

## CRM mapping — contact

| Field | Source | Mapped Value |
|-------|--------|--------------|
| name | person entity | Jennifer Walsh |
| title | inferred from context | VP of Operations |
| account | organization entity | TechVantage Solutions |

## CRM mapping — activity

| Field | Source | Mapped Value |
|-------|--------|--------------|
| type | call metadata | Phone Call |
| subject | conversation summary | Discovery follow-up - proposal requested |
| description | full transcript | Discussed reporting challenges, 150 users affected. Budget approved up to $200K. CEO Mark Davidson wants proposal by Dec 15. Technical review with IT Director Sam Patel needed. |
| duration_min | call metadata | 31 |

## New contacts to create

| Name | Title | Role | Account |
|------|-------|------|---------|
| Mark Davidson | CEO | Economic Buyer | TechVantage Solutions |
| Sam Patel | IT Director | Technical Evaluator | TechVantage Solutions |

## Rendering notes

- The mapping tables show raw stored values: `amount` is `200000`,
  `probability` is `65`.
- The update preview formats the same values for a human reader: `$200,000`
  and `65%`.
- `duration_min` (31 minutes, activity metadata) is a different field from the
  transcript duration (1847 sec / 30m 47s). Both are correct in their own
  context.
- Nothing in this file is a write. Every mapping is a proposal that ends at
  `Ready to apply | Requires confirmation`.
