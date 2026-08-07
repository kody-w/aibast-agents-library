# Customer 360 Account Data

> SYNTHETIC -- DEMO DATA. Every customer, contact, contract, and interaction in
> this document is fictional. This file exists so the agent has a working world
> to answer from on day one. In production, replace this file with tools that
> read your real CRM, support, billing, and product-usage systems (see the
> README's production section).

## Account book

| ID | Name | Segment | Industry | ARR | MRR | Primary Contact | Contact Email | Account Manager | CSM | Contract Start | Contract End |
|----|------|---------|----------|-----|-----|-----------------|---------------|-----------------|-----|----------------|--------------|
| CUST-3001 | TechVantage Solutions | Enterprise | Technology | $185,000 | $15,417 | Jennifer Walsh | jennifer.walsh@techvantage.com | Sarah Chen | Mike Torres | 2023-06-15 | 2026-06-14 |
| CUST-3002 | Greenridge Partners | Mid-Market | Financial Services | $72,000 | $6,000 | David Park | david.park@greenridge.com | Tom Rivera | Lisa Wong | 2024-01-10 | 2025-01-09 |
| CUST-3003 | BlueHorizon Health | Enterprise | Healthcare | $240,000 | $20,000 | Dr. Maria Santos | maria.santos@bluehorizon.org | Sarah Chen | Mike Torres | 2022-03-01 | 2025-02-28 |

## Products and license usage

| ID | Products | Product Count | Employees Using | Licenses Purchased | Utilization |
|----|----------|---------------|-----------------|--------------------|-------------|
| CUST-3001 | Enterprise Platform, Analytics Pro, Integration Hub, Premium Support | 4 | 420 | 500 | 84% |
| CUST-3002 | Core Platform, Analytics Standard | 2 | 85 | 100 | 85% |
| CUST-3003 | Enterprise Platform, Analytics Pro, Security Suite, Integration Hub, Premium Support, Training Package | 6 | 1200 | 1500 | 80% |

## CRM data

| ID | Lead Source | Deal Cycle (days) | Original Deal Size |
|----|-------------|-------------------|--------------------|
| CUST-3001 | Partner Referral | 62 | $145,000 |
| CUST-3002 | Website | 45 | $72,000 |
| CUST-3003 | Conference | 120 | $180,000 |

## Billing data

| ID | Payment Method | Payment Terms | Last Payment | Outstanding Balance | Lifetime Value |
|----|----------------|---------------|--------------|---------------------|----------------|
| CUST-3001 | ACH | Net 30 | 2025-11-01 | $0 | $462,500 |
| CUST-3002 | Credit Card | Net 15 | 2025-10-15 | $6,000 | $72,000 |
| CUST-3003 | ACH | Net 45 | 2025-11-05 | $0 | $720,000 |

## Support data

| ID | Total Tickets | Open Tickets | Avg Resolution (hours) | CSAT Avg | Escalations |
|----|---------------|--------------|------------------------|----------|-------------|
| CUST-3001 | 47 | 2 | 4.2 | 4.6 | 3 |
| CUST-3002 | 18 | 4 | 8.7 | 3.8 | 2 |
| CUST-3003 | 92 | 1 | 3.1 | 4.8 | 1 |

## Interaction log -- CUST-3001 TechVantage Solutions

| Date | Type | Channel | Summary | Sentiment |
|------|------|---------|---------|-----------|
| 2025-11-12 | Support Ticket | Portal | Dashboard loading timeout - resolved with cache clear | Neutral |
| 2025-11-08 | QBR Meeting | Teams | Quarterly business review - discussed expansion to APAC team | Positive |
| 2025-10-25 | Support Ticket | Email | SSO integration issue post-update - escalated and resolved | Frustrated |
| 2025-10-15 | Product Feedback | In-App | Requested advanced filtering in analytics module | Positive |
| 2025-10-01 | Billing | Portal | Added 50 user licenses for Q4 onboarding | Positive |

## Interaction log -- CUST-3002 Greenridge Partners

| Date | Type | Channel | Summary | Sentiment |
|------|------|---------|---------|-----------|
| 2025-11-10 | Support Ticket | Portal | Report export failing for large date ranges | Frustrated |
| 2025-11-05 | Support Ticket | Email | User access permissions not syncing with AD | Frustrated |
| 2025-10-28 | CSM Check-in | Phone | Discussed adoption challenges, team training needed | Concerned |
| 2025-10-20 | Billing | Portal | Late payment notice - payment received Oct 22 | Neutral |

## Interaction log -- CUST-3003 BlueHorizon Health

| Date | Type | Channel | Summary | Sentiment |
|------|------|---------|---------|-----------|
| 2025-11-14 | Renewal Discussion | Teams | Renewal meeting - expanding from 1500 to 2000 licenses | Positive |
| 2025-11-01 | Executive Sponsor | In-Person | CIO dinner - strong relationship, considering additional modules | Positive |
| 2025-10-20 | Product Feedback | Email | Requested HIPAA compliance reporting enhancements | Positive |
