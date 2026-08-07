# Time Entries and Rate Cards

> SYNTHETIC — DEMO DATA. Every consultant, time entry, project, and rate in
> this document is fictional. This file exists so the agent has a working world
> to answer from on day one. In production, replace this file with tools that
> read your real time entry system and rate card master (see the README's
> production section).

## Time entry log

Twelve entries covering 2026-03-10 through 2026-03-12. Nothing outside that
window exists in this data — if asked about another period, say so.

| Entry ID | Consultant | Project | Date | Hours | Rate | Category | Description | Approved |
|----------|------------|---------|------|-------|------|----------|-------------|----------|
| TE-9001 | Elena Vasquez | TechCorp Transformation | 2026-03-10 | 8.0 | $275 | billable | Cloud architecture design workshop | yes |
| TE-9002 | Elena Vasquez | TechCorp Transformation | 2026-03-11 | 9.5 | $275 | billable | Azure landing zone implementation | yes |
| TE-9003 | Michael Chen | Apex Analytics Platform | 2026-03-10 | 7.5 | $260 | billable | Data pipeline development | yes |
| TE-9004 | Michael Chen | Apex Analytics Platform | 2026-03-11 | 8.0 | $260 | billable | *(none)* | no |
| TE-9005 | Priya Sharma | Pinnacle Energy ERP | 2026-03-10 | 10.0 | $310 | billable | Program status review and steering committee | yes |
| TE-9006 | Priya Sharma | Pinnacle Energy ERP | 2026-03-11 | 8.0 | $310 | billable | Sprint planning and backlog grooming | yes |
| TE-9007 | Lisa Tanaka | Atlas Security Audit | 2026-03-10 | 6.0 | $290 | billable | Identity and access management review | yes |
| TE-9008 | Lisa Tanaka | Atlas Security Audit | 2026-03-11 | 8.5 | $290 | billable | Penetration test coordination | yes |
| TE-9009 | Amanda Foster | Metro Transit Portal | 2026-03-10 | 8.0 | $165 | billable | User research session facilitation | yes |
| TE-9010 | Amanda Foster | Metro Transit Portal | 2026-03-11 | 4.0 | $165 | non_billable | Internal design review | yes |
| TE-9011 | Elena Vasquez | TechCorp Transformation | 2026-03-12 | 11.0 | $412 | billable | Weekend migration cutover | no |
| TE-9012 | David Okafor | Internal Training | 2026-03-10 | 8.0 | $0 | non_billable | Power BI certification prep | yes |

Notes the agent should carry:

- TE-9004 has an empty description and is not approved.
- TE-9011 was logged at the overtime rate for a weekend cutover, runs 11.0
  hours, and is not approved.
- `Internal Training` is not a client project and has no budget record.

## Consultant rate cards

| Consultant | Standard Rate | Overtime Rate | Max Daily Hours |
|------------|---------------|---------------|-----------------|
| Elena Vasquez | $275 | $412 | 10 |
| Michael Chen | $260 | $390 | 10 |
| Priya Sharma | $310 | $465 | 10 |
| Lisa Tanaka | $290 | $435 | 10 |
| Amanda Foster | $165 | $248 | 10 |

**David Okafor has no rate card.** Rate and daily-limit compliance cannot be
verified for his entries; report that rather than reporting them as clean.
