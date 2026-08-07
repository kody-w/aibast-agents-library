# Fee Schedule, Zoning Standards, and Review Checklists

> SYNTHETIC — DEMO DATA. This fee schedule, these zoning standards, and these
> checklist templates are fictional and are not any jurisdiction's adopted
> code. This file exists so the agent has a working world to answer from on
> day one. In production, replace this file with tools that read your adopted
> fee resolution, your zoning ordinance, and your plan review templates (see
> the README's production section).

## Fee schedule

Every fee category is computed as:

`amount = base + (valuation / 1000) x per_thousand_rate`, rounded to the cent.

| Fee Category | Rendered | Base | Per $1,000 of Valuation |
|---|---|---|---|
| plan_review | Plan Review | $250.00 | $4.50 |
| building_permit | Building Permit | $150.00 | $8.75 |
| electrical | Electrical | $75.00 | $1.25 |
| plumbing | Plumbing | $75.00 | $1.25 |
| mechanical | Mechanical | $75.00 | $1.00 |
| fire_review | Fire Review | $200.00 | $2.00 |
| technology_surcharge | Technology Surcharge | $25.00 | $0.50 |
| **All categories** | **Total** | **$850.00** | **$19.25** |

All seven categories apply to every permit type. There is no exemption,
minimum, cap, or valuation tier.

### Worked totals for the permits on file

| Permit ID | Valuation | Plan Review | Building Permit | Electrical | Plumbing | Mechanical | Fire Review | Technology Surcharge | Total |
|---|---|---|---|---|---|---|---|---|---|
| BP-2025-0101 | $4,200,000 | $19,150.00 | $36,900.00 | $5,325.00 | $5,325.00 | $4,275.00 | $8,600.00 | $2,125.00 | $81,700.00 |
| BP-2025-0102 | $185,000 | $1,082.50 | $1,768.75 | $306.25 | $306.25 | $260.00 | $570.00 | $117.50 | $4,411.25 |
| BP-2025-0103 | $320,000 | $1,690.00 | $2,950.00 | $475.00 | $475.00 | $395.00 | $840.00 | $185.00 | $7,010.00 |
| BP-2025-0104 | $6,800,000 | $30,850.00 | $59,650.00 | $8,575.00 | $8,575.00 | $6,875.00 | $13,800.00 | $3,425.00 | $131,750.00 |

These are estimates from the declared valuation, not invoices and not payment
records.

## Zoning standards

| Zoning District | Max Height | Front Setback | Side Setback | Rear Setback | Lot Coverage | Parking |
|---|---|---|---|---|---|---|
| R-1 (Single Family Residential) | 35 ft / 2.5 stories | 25 ft | 5 ft | 20 ft | 40% | 2 spaces per unit |
| MU-2 (Mixed Use) | 55 ft / 4 stories | 0 ft | 0 ft | 10 ft | 80% | 1 space per unit + 1 per 500 sq ft commercial |
| I-1 (Light Industrial) | 45 ft / 3 stories | 20 ft | 10 ft | 15 ft | 60% | 1 per 1,000 sq ft |
| PF (Public Facilities) | 50 ft / 3 stories | 30 ft | 15 ft | 20 ft | 50% | Per use determination |

Standards are quoted as written. Variances, exceptions, and compliance
determinations are made by the plans examiner, not by the agent.

## Review checklist templates

### Common items — every permit type

1. Verify application completeness
2. Confirm property ownership / authorization
3. Zoning compliance verification
4. Setback and height compliance
5. Parking requirement verification

### Type-specific items — appended after the common five

| Permit Type | Additional Items | Count | Total Items |
|---|---|---|---|
| new_construction | Structural engineering review; Fire and life safety review; Accessibility (ADA) compliance; Stormwater management plan; Utility connection approvals; Environmental review (CEQA/NEPA if applicable) | 6 | 11 |
| residential_addition | Structural adequacy of existing foundation; Egress requirements met; Energy code compliance (Title 24) | 3 | 8 |
| commercial_alteration | Electrical load calculation review; Fire alarm system impact assessment; Structural load verification | 3 | 8 |
| institutional | Structural engineering review; Fire and life safety review; ADA accessibility compliance; School facility standards (DSA if applicable); Seismic compliance verification; Hazardous materials assessment | 6 | 11 |
