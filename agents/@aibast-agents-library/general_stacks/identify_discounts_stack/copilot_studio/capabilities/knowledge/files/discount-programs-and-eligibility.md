# Discount Programs and Eligibility

> SYNTHETIC - DEMO DATA. Every program, threshold, tier, and price in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real pricing engine and CRM (see the README's production section).

## Discount program catalog

| ID | Program | Type | Description | Max Discount | Stackable | Requires Approval | Auto-Apply |
|----|---------|------|-------------|--------------|-----------|-------------------|------------|
| VOL-001 | Volume Discount | Volume | Tiered pricing based on license count | 25% | No | No | Yes |
| MULTI-001 | Multi-Year Commitment | Term | Discount for 2-3 year contract commitments | 20% | Yes | No | Yes |
| EDU-001 | Education Pricing | Segment | Special pricing for accredited educational institutions | 40% | No | Yes | No |
| NPO-001 | Non-Profit Discount | Segment | Reduced pricing for registered non-profit organizations | 35% | No | Yes | No |
| COMP-001 | Competitive Switch | Strategic | Discount for customers switching from competitor platforms | 30% | Yes | Yes | No |
| LOYAL-001 | Loyalty Renewal | Retention | Discount for customers renewing after 3+ years | 15% | Yes | No | Yes |
| BUNDLE-001 | Product Bundle | Bundle | Discount when purchasing 3+ products together | 18% | Yes | No | Yes |

## Eligibility criteria

| ID | Test | Criteria |
|----|------|----------|
| VOL-001 | Automated | Minimum 50 licenses; percentage comes from the volume tier table below |
| MULTI-001 | Automated | Minimum term of 2 years; 2 years = 10%, 3 years = 20% |
| EDU-001 | Document verification | Required documents: Accreditation certificate, Tax-exempt status letter. Institution types: University, College, K-12 School District |
| NPO-001 | Document verification | Required documents: 501(c)(3) determination letter, Organization charter. Org types: Registered Non-Profit, NGO, Foundation |
| COMP-001 | Automated + proof | Deal flagged as a competitive switch from Competitor A, Competitor B, or Competitor C. Proof required: active subscription screenshot or invoice |
| LOYAL-001 | Automated | Minimum tenure 3 years, minimum health score 70, no outstanding balance |
| BUNDLE-001 | Automated | Minimum 3 eligible products. Eligible products: Core Platform, Enterprise Platform, Analytics Standard, Analytics Pro, Integration Hub, Security Suite |

EDU-001 and NPO-001 have no automated eligibility test in this build. They
report **Not Eligible** from deal data alone until the required documents are
verified by a person.

## Volume tier table (VOL-001)

| Tier | Licenses | Discount | Price |
|------|----------|----------|-------|
| Tier 1 | 50-99 | 10% | $90/license |
| Tier 2 | 100-249 | 15% | $85/license |
| Tier 3 | 250-499 | 20% | $80/license |
| Tier 4 | 500-99999 | 25% | $75/license |
