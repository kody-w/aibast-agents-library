# Employee Directory and Leave Data

> SYNTHETIC — DEMO DATA. Every employee, contact detail, and leave balance in
> this document is fictional; all records use the contoso.com domain and
> 555-prefixed phone numbers. This file exists so the agent has a working world
> to answer from on day one. In production, replace this file with tools that
> read your real directory service and HRIS time management system (see the
> README's production section).

## Organizational directory

Six entries. The directory is searched by name and department only.

| ID | Name | Title | Department | Location | Manager | Phone | Email |
|---|---|---|---|---|---|---|---|
| emp-2001 | Angela Martinez | Marketing Manager | Marketing | Austin, TX | VP Marketing - Rachel Chen | 512-555-0147 | angela.martinez@contoso.com |
| emp-2002 | Brian Nguyen | Software Engineer II | Engineering | Seattle, WA | Eng Director - Sam Patel | 206-555-0293 | brian.nguyen@contoso.com |
| emp-2003 | Carla Dubois | Senior Financial Analyst | Finance | New York, NY | CFO - David Kim | 212-555-0381 | carla.dubois@contoso.com |
| emp-2004 | Derek Washington | HR Business Partner | Human Resources | Chicago, IL | CHRO - Lisa Park | 312-555-0462 | derek.washington@contoso.com |
| emp-2005 | Elena Kowalski | Sales Director | Sales | Boston, MA | CRO - James Mitchell | 617-555-0518 | elena.kowalski@contoso.com |
| emp-2006 | Frank O'Brien | IT Systems Administrator | IT | Denver, CO | CTO - Maria Santos | 303-555-0674 | frank.obrien@contoso.com |

## Leave balances

Leave records exist for three employees only. emp-2004, emp-2005, and emp-2006
appear in the directory but have no leave record — that absence is reported as
an absence, never filled in from another record.

| Employee ID | Name | Department | Hire Date | Vacation (days) | Sick (days) | Personal (days) | Accrual (days/month) |
|---|---|---|---|---|---|---|---|
| emp-2001 | Angela Martinez | Marketing | 2022-05-16 | 14.5 | 7.0 | 2.0 | 1.67 |
| emp-2002 | Brian Nguyen | Engineering | 2024-01-08 | 8.25 | 5.0 | 1.0 | 1.25 |
| emp-2003 | Carla Dubois | Finance | 2019-09-01 | 22.0 | 10.0 | 3.0 | 2.08 |

## Leave request queue

| Employee ID | Name | Dates | Days | Status |
|---|---|---|---|---|
| emp-2001 | Angela Martinez | Dec 23-27, 2025 | 3 | Approved |
| emp-2002 | Brian Nguyen | (none on file) | - | - |
| emp-2003 | Carla Dubois | Nov 25-29, 2025 | 5 | Pending |
