# HEDIS Measure and Segment Data

> SYNTHETIC — DEMO DATA. Every measure population, segment, and channel figure
> in this document is fictional. This file exists so the agent has a working
> world to answer from on day one. In production, replace this file with tools
> that read your real quality measure engine, member risk stratification, and
> outreach platform (see the README's production section).
>
> Everything here is aggregate. There are no patient records in this data set —
> no names, no member IDs, no contact details, no clinical values.

## HEDIS measures

| ID | Measure | Definition | Eligible | Compliant | Gap Rate | Revenue per Closure | National Benchmark | Star Impact |
|----|---------|------------|----------|-----------|----------|---------------------|--------------------|-------------|
| BCS | Breast Cancer Screening | Women 50-74 with mammogram in past 2 years | 4,280 | 3,210 | 25.0% | $45 | 78.2% | 4-star threshold at 76% |
| CDC-HBA1C | Diabetes HbA1c Testing | Diabetic patients 18-75 with HbA1c test in past year | 6,120 | 5,202 | 15.0% | $62 | 88.5% | 5-star threshold at 90% |
| COL | Colorectal Cancer Screening | Adults 45-75 with appropriate colorectal screening | 8,940 | 5,810 | 35.0% | $38 | 72.1% | 4-star threshold at 68% |
| CBP | Controlling Blood Pressure | Hypertensive patients 18-85 with BP adequately controlled | 7,650 | 5,355 | 30.0% | $55 | 65.8% | 4-star threshold at 64% |
| AWC | Adolescent Well-Care Visits | Adolescents 12-21 with at least one well-care visit | 3,200 | 1,920 | 40.0% | $28 | 58.4% | 3-star threshold at 54% |

Derived from this table (the agent computes these; they are not stored):

| ID | Measure | Open Gaps | Compliance Rate | vs Benchmark | Revenue Opportunity |
|----|---------|-----------|-----------------|--------------|---------------------|
| CBP | Controlling Blood Pressure | 2,295 | 70.0% | +4.2% | $126,225 |
| COL | Colorectal Cancer Screening | 3,130 | 65.0% | -7.1% | $118,940 |
| CDC-HBA1C | Diabetes HbA1c Testing | 918 | 85.0% | -3.5% | $56,916 |
| BCS | Breast Cancer Screening | 1,070 | 75.0% | -3.2% | $48,150 |
| AWC | Adolescent Well-Care Visits | 1,280 | 60.0% | +1.6% | $35,840 |

Total revenue opportunity across all five measures: **$386,071**.

## Patient segments

| Segment | Count | Description | Avg Risk Score | Preferred Outreach | Response Rate |
|---------|-------|-------------|----------------|--------------------|---------------|
| Multi Gap High Risk | 1,842 | Patients with 3+ open gaps and chronic conditions | 3.8 | phone_call | 42% |
| Unreachable | 890 | Patients with no valid contact info or repeated no-shows | 2.9 | mail | 8% |
| Single Gap Engaged | 5,610 | Patients with 1 open gap and recent visit history | 1.4 | patient_portal | 68% |
| Recently Compliant | 3,420 | Patients who closed gaps in last 90 days | 1.1 | none | 0% |

Segments are listed in risk-score order, which is the order the agent
prioritizes them in. Segment counts are a different slice of the population
than the per-measure gap counts and must never be summed with them.

## Outreach channels

| Channel | Cost per Contact | Avg Response Rate | Avg Conversion Rate |
|---------|------------------|-------------------|---------------------|
| phone_call | $4.50 | 38% | 22% |
| patient_portal | $0.25 | 52% | 31% |
| sms | $0.15 | 45% | 18% |
| mail | $2.80 | 12% | 6% |
| email | $0.08 | 28% | 14% |

Campaign planning selects the single highest-converting channel across this
table — `patient_portal` at 31% conversion, $0.25 per contact — and applies it
to every measure.
