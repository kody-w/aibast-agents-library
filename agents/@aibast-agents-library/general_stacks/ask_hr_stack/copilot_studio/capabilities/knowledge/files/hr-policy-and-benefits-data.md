# HR Policy and Benefits Data

> SYNTHETIC — DEMO DATA. Every policy, plan, premium, and dollar figure in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real HR policy portal and benefits administration system (see the
> README's production section).

## Policy directory

| Policy Key | Title | Category | Effective Date | Approver |
|---|---|---|---|---|
| remote_work | Remote Work Policy | Workplace Flexibility | 2025-01-15 | Direct Manager |
| pto | Paid Time Off Policy | Time Off | 2025-01-01 | Direct Manager |
| expense_reimbursement | Expense Reimbursement Policy | Finance | 2025-03-01 | Direct Manager / VP (over $2,500) |
| code_of_conduct | Code of Conduct | Compliance | 2024-06-01 | HR Department |

### remote_work — Remote Work Policy

**Summary:** Employees may work remotely up to 3 days per week with manager
approval.

| # | Detail |
|---|---|
| 1 | Eligible after 90-day probation period |
| 2 | Core hours: 10 AM - 3 PM local time zone |
| 3 | Home office stipend: $750 one-time for equipment |
| 4 | Internet reimbursement: $50/month |
| 5 | Must maintain secure VPN connection |
| 6 | Quarterly in-office week required for all remote staff |

### pto — Paid Time Off Policy

**Summary:** PTO accrual based on tenure: 15 days (0-2 yr), 20 days (3-5 yr),
25 days (6+ yr).

| # | Detail |
|---|---|
| 1 | Accrual begins on first day of employment |
| 2 | Maximum carryover: 5 days per calendar year |
| 3 | Requests of 5+ consecutive days require 2 weeks notice |
| 4 | Holiday blackout: Dec 20 - Jan 2 requires VP approval |
| 5 | Unused PTO above carryover limit forfeited Dec 31 |
| 6 | Payout of accrued PTO upon separation |

### expense_reimbursement — Expense Reimbursement Policy

**Summary:** Business expenses reimbursed within 30 days of submission with
valid receipts.

| # | Detail |
|---|---|
| 1 | Submit via Concur within 60 days of expense |
| 2 | Meals: $75/day domestic, $100/day international |
| 3 | Flights: Economy class for trips under 6 hours |
| 4 | Hotel: Up to $250/night domestic, $350/night international |
| 5 | Manager approval for expenses over $500 |
| 6 | VP approval for expenses over $2,500 |

### code_of_conduct — Code of Conduct

**Summary:** Standards of professional behavior, ethics, and compliance for all
employees.

| # | Detail |
|---|---|
| 1 | Annual acknowledgment required by all employees |
| 2 | Conflicts of interest must be disclosed to HR |
| 3 | Gifts from vendors limited to $100 value |
| 4 | Confidential information protected under NDA |
| 5 | Harassment-free workplace with zero tolerance policy |
| 6 | Report violations via ethics hotline or HR portal |

## Medical plans

| Plan Key | Name | Employee Premium | Family Premium | Deductible (Ind/Fam) | OOP Max (Ind/Fam) | Copay (PCP/Spec) | Network |
|---|---|---|---|---|---|---|---|
| medical_ppo | Medical PPO Plan | $185/mo | $520/mo | $500 / $1,500 | $3,500 / $7,000 | $25 / $50 | Blue Cross Blue Shield National |
| medical_hdhp | High Deductible Health Plan | $95/mo | $310/mo | $1,600 / $3,200 | $5,000 / $10,000 | $0 / $0 | Blue Cross Blue Shield National |

The HDHP carries an employer HSA contribution of $750.

## Dental plan

| Field | Value |
|---|---|
| Name | Dental Plan |
| Employee Premium | $28/mo |
| Family Premium | $85/mo |
| Deductible | $50 |
| Annual Maximum | $2,000 |
| Preventive Coverage | 100% |
| Basic Coverage | 80% |
| Major Coverage | 50% |
| Orthodontia Lifetime Max | $1,500 |

## Vision plan

| Field | Value |
|---|---|
| Name | Vision Plan |
| Employee Premium | $12/mo |
| Family Premium | $35/mo |
| Exam Copay | $10 |
| Frames Allowance | $200 |
| Contacts Allowance | $150 |
| Frequency | Every 12 months |

## Retirement plan

| Field | Value |
|---|---|
| Name | 401(k) Retirement Plan |
| Employer Match | 100% of first 4%, 50% of next 2% |
| Max Match Percent | 5 |
| Vesting Schedule | 3-year graded (33%/66%/100%) |
| 2025 Contribution Limit | $23,500 |
| Catch-up (over 50) | $7,500 |

## Estimated employer contribution value

Modeled on a $100,000 salary assumption and the Medical PPO Plan. This is an
illustration, not a payroll figure.

| Component | Formula | Annual Value |
|---|---|---|
| Medical | 185 x 12 x 0.75 | $1,665 |
| Dental | 28 x 12 x 0.80 | $269 |
| Vision | 12 x 12 x 1.00 | $144 |
| 401(k) match | 100,000 x 5 / 100 | $5,000 |
| **Total** | | **$7,078** |
