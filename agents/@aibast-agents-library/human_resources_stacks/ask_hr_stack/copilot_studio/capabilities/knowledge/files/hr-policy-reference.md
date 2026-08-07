# HR Policy Reference

> SYNTHETIC — DEMO DATA. Every policy value, holiday, and dollar figure in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real HR Policy Portal and Benefits Portal (see the README's production
> section).

Policy values are identical for every employee. Only the eligibility flags in
`employee-hr-records.md` vary per person.

## Company holidays

| Holiday | Date |
|---------|------|
| Memorial Day | May 26 |
| Independence Day | Jul 4 |
| Labor Day | Sep 1 |
| Thanksgiving | Nov 27-28 |
| Year-End | Dec 24-25, Dec 31-Jan 1 |

## Time-off policy

| Rule | Value |
|------|-------|
| Minimum notice for requests of 5+ days | 2 weeks |
| Holiday period restriction | Dec 15 - Jan 5 requires manager pre-approval |
| Rollover cap | Max 5 days carry to next year |
| Request status on submission | Pending Manager Approval |

Remaining balance is computed as `vacation balance - days requested`.

## Parental leave policy

| Benefit | Value |
|---------|-------|
| Paternity leave | 8 weeks fully paid |
| Maternity leave | 16 weeks fully paid |
| Minimum tenure | 1 year |
| Family care stipend | $2,000 one-time |
| Backup childcare | 6 months included |
| Filing deadline | Submit the form 30 days before the due date |

Additional support: flexible return-to-work schedule, Parent Employee Resource
Group, lactation room access.

## Remote work policy

| Benefit | Value |
|---------|-------|
| Standard allowance | 3 days/week remote |
| New-parent bonus | +2 days/week |
| New-parent bonus duration | 6 months |
| Core hours | 10 AM - 3 PM local |
| Equipment stipend | $1,000 one-time |
| Internet reimbursement | $50/month |

Additional support: virtual ergonomic assessment, same-day IT support. New
parents also get a gradual return (part-time for 4 weeks) and 10 days/year of
emergency childcare.

## Health insurance policy

| Rule | Value |
|------|-------|
| Enrollment window | 30 days from qualifying event |
| Dependent premium increase | +$125/month |
| Coverage effective date | Date of the qualifying event |
| Well-baby care | 100% covered |
| Immunizations | 100% covered |
| Pediatric visit copay | $20 |
| Dependent life insurance | $10,000, automatic |

## Benefits valuation constants

Used to compute the estimated package value in the benefits summary.

| Line | Rule | Applies when |
|------|------|--------------|
| Parental Leave | 8 weeks x $2,500/week = $20,000 | Parental leave eligible |
| Family Stipend | $2,000 | Parental leave eligible |
| Childcare Benefit | $3,000 | Parental leave eligible |
| Equipment Stipend | $1,000 | Always |

The $2,500 weekly figure is a fixed estimate used for valuation only. It is not
any employee's salary. Total estimated value is the sum of the lines that apply:
$26,000 for a parental-eligible employee, $1,000 for one who is not.
