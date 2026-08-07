# SLA Targets and Escalation Policy

> SYNTHETIC — DEMO DATA. A fictional service desk's policy, included so the
> agent's guardrails are grounded in a citable document rather than only in
> its instructions. In production, replace this file with tools that read your
> real SLA engine.

## Severity targets

| Severity | Response | Resolution | Escalation | Breach Penalty |
|----------|----------|------------|------------|----------------|
| P1-Critical | 0.25h | 1h | 0.5h | $500 |
| P2-High | 0.5h | 4h | 2h | $200 |
| P3-Medium | 2h | 8h | 6h | $50 |
| P4-Low | 4h | 24h | 20h | $0 |

Response is time to first human contact. Resolution is the SLA clock the
at-risk rule measures against. Escalation is the elapsed point at which the
duty manager is expected to be involved. Breach penalty is charged per
breached ticket.

## The at-risk rule

A ticket is at risk of breach when both hold:

1. Its status is `Open`, `In Progress`, or `Assigned`.
2. `remaining_hours = resolution_hours - elapsed_hours` is less than 30% of
   the severity's resolution window.

Thresholds that follow from that rule:

| Severity | Resolution Window | At risk when remaining is under |
|----------|-------------------|---------------------------------|
| P1-Critical | 1h | 0.3h |
| P2-High | 4h | 1.2h |
| P3-Medium | 8h | 2.4h |
| P4-Low | 24h | 7.2h |

The at-risk list is sorted by remaining hours ascending — least time first.

## Status taxonomy

| Status | On the SLA clock | Meaning |
|--------|------------------|---------|
| Open | Yes | Logged, work not started |
| Assigned | Yes | Owner named, work not started |
| In Progress | Yes | Work under way |
| Pending Approval | No | Waiting on a business approver; the SLA clock does not run |

A ticket in `Pending Approval` never appears in the at-risk list, regardless
of elapsed time. If it is stalled, that is an approval escalation, not an SLA
breach.

## Compliance target

Service desk SLA attainment target is **95%**. Current attainment this week is
94.2% — below target. Report the gap; do not round it away.

## Who acts

1. The agent recommends. Only a service desk lead or duty manager changes a
   priority, assigns or reassigns a ticket, pages on-call, escalates, extends
   an SLA, or closes work.
2. Severity is set by the intake process. The agent may argue a severity is
   wrong and show the evidence (users affected, elapsed time, business impact),
   but never restates a ticket's severity as though it had changed.
3. A team at or above 85% capacity is treated as constrained; routing more work
   to it requires the duty manager's call.
