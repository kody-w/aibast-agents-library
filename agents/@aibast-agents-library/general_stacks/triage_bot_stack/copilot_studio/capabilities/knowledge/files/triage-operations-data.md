# Triage Operations Data

> SYNTHETIC - DEMO DATA. Every inquiry, customer, and team in this document is
> fictional. This file exists so the agent has a working world to answer from
> on day one. In production, replace this file with tools that read your real
> ticketing queue and routing configuration.

## Inquiry queue

| ID | Text | Customer | Tier | Impact | Urgency | Classified As | Confidence |
|----|------|----------|------|--------|---------|---------------|------------|
| INQ-T001 | Our entire sales team can't access the platform. Getting 500 errors for the past 30 minutes. | Meridian Corp | Enterprise | high | high | technical_support | 97% |
| INQ-T002 | I'd like to understand the pricing for your Analytics Pro module for 200 users. | New Prospect | Unknown | low | medium | sales | 94% |
| INQ-T003 | We received a duplicate invoice for November. Can you check? | Atlas Digital | Mid-Market | medium | low | billing | 96% |
| INQ-T004 | We noticed unauthorized API calls from an unknown IP. Need immediate investigation. | BlueHorizon Health | Enterprise | high | high | security | 99% |

## Inquiry categories

| Key | Category | Description | Team | Avg Handle (min) | SLA |
|-----|----------|-------------|------|------------------|-----|
| technical_support | Technical Support | Product issues, bugs, performance problems | Technical Support | 25 | 4h |
| billing | Billing & Payments | Invoices, payment issues, plan changes | Billing Team | 15 | 8h |
| sales | Sales Inquiry | Pricing, demos, new purchases | Sales Team | 20 | 2h |
| account_management | Account Management | Renewals, upgrades, account changes | Account Management | 30 | 8h |
| feature_request | Feature Request | New feature suggestions, enhancements | Product Team | 10 | 72h |
| security | Security Concern | Security incidents, compliance, data privacy | Security Team | 35 | 1h |

## Routing rules

| Category | Primary Team | Escalation Team | Auto-Assign | Skill Required | After Hours |
|----------|--------------|-----------------|-------------|----------------|-------------|
| Technical Support | Technical Support | Engineering | Yes | product_knowledge | On-Call Engineer |
| Billing & Payments | Billing Team | Finance | Yes | billing_systems | Billing Queue |
| Sales Inquiry | Sales Team | Sales Management | No | sales_qualification | Lead Queue |
| Account Management | Account Management | VP Customer Success | Yes | account_strategy | CSM Queue |
| Feature Request | Product Team | Product Management | No | product_strategy | Product Backlog |
| Security Concern | Security Team | CISO | Yes | security_ops | Security On-Call |

## Keyword classifier

Applied in this order to new inquiry text; first match wins, matching is
case-insensitive.

| Order | Keywords | Category | Confidence |
|-------|----------|----------|------------|
| 1 | error, not working, can't access, bug, crash | Technical Support | 95% |
| 2 | pricing, demo, purchase, quote | Sales Inquiry | 92% |
| 3 | invoice, payment, billing, charge | Billing & Payments | 94% |
| 4 | security, unauthorized, breach, privacy | Security Concern | 97% |
| 5 | feature, enhancement, wish, suggestion | Feature Request | 88% |
| 6 | (no keyword matched) | Account Management | 75% |
