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

### Renewal start dates (computed from the register)

| Permit | Expires | Lead (days) | Renewal start |
|--------|---------|-------------|---------------|
| PRM-6004 Pipeline Operating License | 2026-08-20 | 365 | 2025-08-20 |
| PRM-6002 NPDES Stormwater Discharge Permit | 2026-03-01 | 180 | 2025-09-02 |
| PRM-6005 Coal Combustion Residuals Permit | 2026-04-01 | 180 | 2025-10-03 |
| PRM-6003 RCRA Hazardous Waste Generator | 2027-01-10 | 270 | 2026-04-15 |
| PRM-6006 Spill Prevention Control Plan | 2029-02-15 | 365 | 2028-02-16 |
| PRM-6001 Title V Air Operating Permit | 2029-06-15 | 365 | 2028-06-15 |

Rows are in renewal-start order, which is the order the renewal work packet
uses. Leap days are counted (PRM-6006 lands on 2028-02-16 because 2028 has a
29 February). These dates are arithmetic on recorded values — the agent has no
clock and does not compute "days remaining" or "overdue by N days".

## Renewal work packet

A renewal work packet is preparation handed to a person. It is never a filing.
Every permit has one; the expired permits are the urgent ones.

### Accountable owner, by permit type

The accountable role is set by permit type, not per permit. The register holds
no personal names, so the owner is always rendered `<role>, <facility>`.

| Permit Type | Accountable role | Permits of this type |
|-------------|------------------|----------------------|
| air_quality | Sustainability Lead | PRM-6001 |
| water_discharge | Compliance Manager | PRM-6002 |
| waste_management | Compliance Manager | PRM-6003, PRM-6005 |
| pipeline_operation | Plant Manager / Reliability Engineer | PRM-6004 |
| spill_prevention | Plant Manager / Reliability Engineer | PRM-6006 |

### Draft submission checklist

Identical for every permit. The named owner executes it; the agent only
assembles it.

1. Confirm the issuing authority's current renewal form, fee, and filing channel
2. Assemble the compliance record since issuance, including the last inspection date
3. Attach current evidence for every recurring requirement of this permit type
4. Route the draft package for internal environmental and legal review
5. Hand the signed package to the accountable owner for submission before expiration

The evidence to attach for a given permit is the recurring requirement list for
its type, in the order the requirement table above gives them.

## Standing rules

1. An expired permit stays expired until the authority issues the renewal. A
   submitted or under-review application is progress, not coverage, and never
   downgrades the CRITICAL finding.
2. The register holds condition **counts**, not condition text. The agent
   never characterizes what a permit requires beyond the recurring
   requirements listed above.
3. The agent reports, recommends, and prepares. Assembling a renewal work
   packet is preparation and is in scope. Filing, amending, withdrawing, or
   responding to an authority is a human action, always.
4. Outcome prediction is out of scope. Expected decision dates are the
   authority's estimate; the agent does not forecast approval, denial, or
   penalty exposure.
