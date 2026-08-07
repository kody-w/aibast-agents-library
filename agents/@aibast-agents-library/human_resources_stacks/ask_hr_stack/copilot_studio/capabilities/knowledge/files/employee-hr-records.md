# Employee HR Records

> SYNTHETIC — DEMO DATA. Every employee, balance, plan, and email in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real Workday and Benefits Portal records (see the README's production
> section).

Three employees are on record. Any name outside this table has no record — the
agent says so rather than answering for someone else.

## Employee directory

| ID | Name | Title | Department | Manager | Tenure (years) | Email |
|----|------|-------|------------|---------|----------------|-------|
| emp-1001 | Jordan Chen | Senior Product Manager | Product | Sarah Johnson | 3.5 | jordan.chen@contoso.com |
| emp-1002 | Michael Torres | Account Executive | Sales | David Kim | 1.2 | michael.torres@contoso.com |
| emp-1003 | Sarah Williams | Engineering Lead | Engineering | Alex Rivera | 5.0 | sarah.williams@contoso.com |

## Leave balances

| ID | Employee | Vacation (days) | Sick (days) | Personal (days) | Accrual Rate (days/month) |
|----|----------|-----------------|-------------|-----------------|---------------------------|
| emp-1001 | Jordan Chen | 15.5 | 8.0 | 3.0 | 1.25 |
| emp-1002 | Michael Torres | 10.0 | 6.0 | 2.0 | 1.0 |
| emp-1003 | Sarah Williams | 22.0 | 10.0 | 3.0 | 1.5 |

## Health plan enrollment

| ID | Employee | Plan | Monthly Premium | Deductible (Individual) | Deductible (Family) | OOP Max (Individual) | OOP Max (Family) | Dependents |
|----|----------|------|-----------------|-------------------------|---------------------|----------------------|------------------|------------|
| emp-1001 | Jordan Chen | PPO Family Plan | $450 | $500 | $1,500 | $3,000 | $6,000 | Spouse |
| emp-1002 | Michael Torres | HMO Individual | $220 | $750 | none | $4,000 | none | None |
| emp-1003 | Sarah Williams | PPO Family Plan | $450 | $500 | $1,500 | $3,000 | $6,000 | Spouse, Child (age 4) |

Monthly premium is the employee's own contribution. HMO Individual carries no
family deductible and no family out-of-pocket maximum.

## Eligibility flags

| ID | Employee | Parental Leave Eligible | Remote Work Eligible |
|----|----------|-------------------------|----------------------|
| emp-1001 | Jordan Chen | Yes | Yes |
| emp-1002 | Michael Torres | No | Yes |
| emp-1003 | Sarah Williams | Yes | Yes |

These flags are the sole source of eligibility. A `No` renders as
`Not yet eligible (requires 1+ year tenure)` and is never overridden by the
tenure column above.

## Pending time-off requests

| Employee | Dates | Days | Status | Manager | Balance After |
|----------|-------|------|--------|---------|---------------|

The queue starts empty. Requests drafted by the agent are added here at status
`Pending Manager Approval` and stay there until the named manager acts.
