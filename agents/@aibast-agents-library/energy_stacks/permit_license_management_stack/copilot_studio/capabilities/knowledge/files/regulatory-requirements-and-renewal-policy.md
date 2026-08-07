# Regulatory Requirements and Renewal Policy

> SYNTHETIC — DEMO DATA. A fictional operator's requirement list and policy,
> included so the agent's guardrails are grounded in a citable document rather
> than only in its instructions. In production, replace this file with tools
> that read your real requirement matrix and compliance calendar.

## Recurring requirements by permit type

Every permit carries a `type`. The type determines the recurring obligations
the operator must keep performing for as long as the permit is in force.

| Permit Type | Recurring Requirements | Permits of this type |
|-------------|------------------------|----------------------|
| air_quality | Continuous emissions monitoring; Annual stack testing; Quarterly compliance reports | PRM-6001 |
| water_discharge | Monthly effluent sampling; Annual DMR submission; Stormwater pollution prevention plan | PRM-6002 |
| waste_management | Biennial hazardous waste report; Manifest tracking; Land disposal restrictions compliance | PRM-6003, PRM-6005 |
| pipeline_operation | Integrity management program; Operator qualification records; Emergency response plan | PRM-6004 |
| spill_prevention | Annual SPCC plan review; Integrity testing of containers; Discharge prevention briefings | PRM-6006 |

The requirement order in this table is the order the agent reports gaps in.

## How compliance gaps are derived

The gap rule set is deterministic and narrow. It produces exactly two kinds of
finding:

1. **expired_permit — CRITICAL.** Raised for any permit whose status is
   `expired`. The detail line names the authority-issued permit number and the
   expiration date.
2. **requirement_at_risk — HIGH.** Raised only for a `water_discharge` permit
   that is `expired`, once per recurring requirement of that type. The
   rationale: discharge monitoring obligations depend on an in-force NPDES
   permit, so an expiration puts each recurring obligation at risk
   simultaneously.

Nothing else is a gap under this rule set. Active permits produce no findings
regardless of inspection date or condition count, and overdue inspections,
unmet conditions, and slipped decision dates are not evaluated. If the
compliance team needs those checked, that is a rule-set change, not an
inference the agent makes.

## Renewal lead time

Each permit carries `renewal_lead_days`, set by its issuing authority. It is
the number of days before expiration that renewal work must begin.

`renewal start = expiration_date - renewal_lead_days`

Worked example: Pipeline Operating License (PRM-6004) expires 2026-08-20 with a
365-day lead, so renewal work must start by 2025-08-20.

Lead times are per permit, not per facility or per type. Two permits of the
same type can carry different lead times — PRM-6003 (waste_management) is 270
days and PRM-6005 (waste_management) is 180.

## Standing rules

1. An expired permit stays expired until the authority issues the renewal. A
   submitted or under-review application is progress, not coverage, and never
   downgrades the CRITICAL finding.
2. The register holds condition **counts**, not condition text. The agent
   never characterizes what a permit requires beyond the recurring
   requirements listed above.
3. The agent reports and recommends. Filing, amending, withdrawing, or
   responding to an authority is a human action, always.
4. Outcome prediction is out of scope. Expected decision dates are the
   authority's estimate; the agent does not forecast approval, denial, or
   penalty exposure.
