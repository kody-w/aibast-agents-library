# IT Service Desk Data

> SYNTHETIC — DEMO DATA. Every ticket, person, and team in this document is
> fictional. This file exists so the agent has a working world to answer from
> on day one. In production, replace this file with tools that read your real
> ITSM system — ServiceNow or Jira Service Management (see the README's
> production section).

## Open ticket queue

| ID | Subject | Category | Severity | Status | Assignee | Team | Created (UTC) | SLA Target | Elapsed | Users Affected |
|----|---------|----------|----------|--------|----------|------|---------------|-----------|---------|----------------|
| TKT-8001 | Email server degradation - 847 users affected | Infrastructure | P1-Critical | In Progress | Sarah Chen | Network Team | 2025-11-14T08:15:00Z | 1h | 0.5h | 847 |
| TKT-8002 | VPN connectivity failure for Finance dept | Network | P1-Critical | In Progress | Mike Torres | Network Team | 2025-11-14T08:30:00Z | 1h | 0.25h | 234 |
| TKT-8003 | CRM system timeout errors | Application | P2-High | Assigned | James Martinez | Application Support | 2025-11-14T09:00:00Z | 4h | 0.1h | 156 |
| TKT-8004 | Password reset - batch of 12 new hires | Access Management | P3-Medium | Open | Lisa Wong | Desktop Support | 2025-11-14T09:15:00Z | 8h | 0h | 12 |
| TKT-8005 | Printer not working on 3rd floor | Hardware | P3-Medium | Open | unassigned | Desktop Support | 2025-11-14T09:30:00Z | 8h | 0h | 35 |
| TKT-8006 | Request for dual monitor setup | Hardware | P4-Low | Open | unassigned | Desktop Support | 2025-11-13T16:00:00Z | 24h | 17h | 1 |
| TKT-8007 | Software license request - Adobe Creative Suite | Software | P4-Low | Pending Approval | Lisa Wong | Desktop Support | 2025-11-13T14:00:00Z | 24h | 19h | 1 |
| TKT-8008 | Conference room AV system not projecting | Hardware | P2-High | In Progress | Mike Chen | Desktop Support | 2025-11-14T08:45:00Z | 4h | 0.3h | 20 |

## Ticket detail

| ID | Description |
|----|-------------|
| TKT-8001 | Exchange server memory at 98%, automatic restart needed |
| TKT-8002 | VPN profile corruption affecting Finance department users |
| TKT-8003 | Dynamics 365 experiencing intermittent timeout errors |
| TKT-8004 | New hire onboarding batch needs initial password setup |
| TKT-8005 | HP LaserJet on 3rd floor showing offline, paper jam cleared |
| TKT-8006 | Employee requesting second monitor for productivity |
| TKT-8007 | Marketing team member needs Adobe CC license |
| TKT-8008 | Board room projector showing no signal, executive meeting at 10 AM |

## Team capacity

The ticket counts below are each team's total work in flight (30 tickets
across the four teams). They are a superset of the 8-ticket queue above and
must never be added to it.

| Team | Members | Tickets | Capacity | Skills |
|------|---------|---------|----------|--------|
| Network Team | 3 | 4 | 72% | Infrastructure, Network, Security |
| Application Support | 4 | 6 | 65% | CRM, ERP, Custom Apps |
| Desktop Support | 5 | 18 | 88% | Hardware, Software, Access Management |
| Database Team | 2 | 2 | 30% | SQL Server, Azure SQL, Performance |

Total: 14 team members, 30 tickets in flight.

## Resolution history

| Period | Resolved | Avg Resolution | SLA Met | FCR | CSAT |
|--------|----------|----------------|---------|-----|------|
| This Week | 89 | 4.2h | 94.2% | 67% | 4.5/5 |
| Last Week | 94 | 4.5h | 91.8% | 62% | 4.3/5 |
| This Month | 312 | 4.3h | 93.1% | 65% | 4.4/5 |

## Top issue categories (this month)

| Category | Count | % of Total | Automation Candidate |
|----------|-------|------------|----------------------|
| Password Resets | 58 | 18.6% | Yes |
| Software Access | 47 | 15.1% | Yes |
| VPN Issues | 38 | 12.2% | No |
| Hardware Requests | 35 | 11.2% | No |
| Email Issues | 29 | 9.3% | No |

These five are the month's top drivers, not the full month. Their shares do
not sum to 100%.

## Standing recommendations

- Automate password resets (18.6% of volume) to save ~22 hours/week.
- Implement a self-service software access portal (15.1% of volume).
- Investigate recurring VPN issues (12.2% of volume) — root cause, not
  automation.
