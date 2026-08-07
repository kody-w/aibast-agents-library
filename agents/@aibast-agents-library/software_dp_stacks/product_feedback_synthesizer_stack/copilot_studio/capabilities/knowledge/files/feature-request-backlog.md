# Feature Request Backlog and Prioritization Policy

> SYNTHETIC — DEMO DATA. Every feature request, vote count, ARR weight, and
> status in this document is fictional. This file exists so the agent has a
> working world to answer from on day one. In production, replace this file
> with tools that read your real product backlog and idea portal (see the
> README's production section).

## Backlog

| ID | Title | Votes | ARR Weight | Status | Effort | Category | Linked Feedback |
|----|-------|-------|------------|--------|--------|----------|-----------------|
| FR-001 | Customizable Dashboard Home View | 87 | $612,000 | under_review | medium | usability | FB-5001 |
| FR-002 | Real-Time Alerting Engine | 134 | $780,000 | planned_q3 | high | feature_gap | FB-5002 |
| FR-003 | Mobile App Enhancements | 62 | $420,000 | in_progress | medium | usability | FB-5003 |
| FR-004 | Large Dataset Export Fix | 41 | $264,000 | in_progress | low | bug_fix | FB-5004 |
| FR-005 | Role-Based Access Controls (RBAC) | 156 | $960,000 | planned_q2 | high | security | FB-5005 |
| FR-006 | Workflow Automation Builder | 203 | $1,140,000 | planned_q3 | high | feature_gap | FB-5006 |

Six requests. Every request traces to exactly one feedback entry.

## Prioritization policy

Priority score is effort-adjusted ARR weight:

`priority_score = round(arr_weight / 1000 / divisor, 1)`

| Effort | Divisor |
|--------|---------|
| high | 3 |
| medium | 2 |
| low | 1 |

Resulting scores and effort-adjusted ranking:

| Rank | ID | Title | Priority Score | ARR Rank |
|------|----|-------|----------------|----------|
| 1 | FR-006 | Workflow Automation Builder | 380.0 | 1 |
| 2 | FR-005 | Role-Based Access Controls (RBAC) | 320.0 | 2 |
| 3 | FR-001 | Customizable Dashboard Home View | 306.0 | 4 |
| 4 | FR-004 | Large Dataset Export Fix | 264.0 | 6 |
| 5 | FR-002 | Real-Time Alerting Engine | 260.0 | 3 |
| 6 | FR-003 | Mobile App Enhancements | 210.0 | 5 |

The two rankings disagree: FR-004 rises from 6th by ARR weight to 4th by
priority score (LOW effort), and FR-002 falls from 3rd to 5th (HIGH effort).

## Vocabularies

| Field | Allowed values |
|-------|----------------|
| status | under_review, planned_q2, planned_q3, in_progress |
| effort | low, medium, high |
| category | usability, feature_gap, bug_fix, security |

Status is read-only for the agent. Changing a status, scheduling a request
into a quarter, or communicating a decision is a human action.
