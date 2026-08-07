# Product Catalog Data

> SYNTHETIC — DEMO DATA. Every product, limit, feature, and price in this
> document is fictional. This file exists so the agent has a working catalog to
> answer from on day one. In production, replace this file with tools that read
> your real PIM and pricing systems (see the README's production section).

## Products

| ID | Name | Category | Description | Max Users | Storage (GB) | API Calls / month | Support |
|----|------|----------|-------------|-----------|--------------|-------------------|---------|
| CORE | Core Platform | Platform | Essential CRM and workflow automation for growing teams | 100 | 50 | 10,000 | Standard |
| ENT | Enterprise Platform | Platform | Full-featured platform with advanced analytics and enterprise controls | 10,000 | 500 | Unlimited | Premium |
| ANLYT-STD | Analytics Standard | Analytics | Business intelligence and reporting for data-driven decisions | 50 | 25 | 5,000 | Standard |
| ANLYT-PRO | Analytics Pro | Analytics | Advanced analytics with predictive insights and custom models | 500 | 200 | 50,000 | Premium |
| INTGR | Integration Hub | Integration | Connect your tech stack with pre-built and custom integrations | Unlimited | 100 | 100,000 | Standard |
| SECUR | Security Suite | Security | Enterprise-grade security, compliance, and data protection | Unlimited | 50 | Unlimited | Premium |

`Unlimited` is stored in the catalog as -1.

## Features by product

Feature lists are literal and ordered. Lines beginning with "Everything in"
are rollup entries: the tier inherits the lower tier's features but does not
restate them, and they are excluded from side-by-side comparison tables.

| Product | Features (in catalog order) |
|---------|-----------------------------|
| Core Platform (CORE) | Contact Management; Deal Pipeline; Task Automation; Basic Reporting; Email Integration; Mobile App |
| Enterprise Platform (ENT) | Everything in Core; Advanced Analytics; Custom Dashboards; Role-Based Access; Audit Logging; SSO/SAML; API Unlimited; Custom Objects; Workflow Builder |
| Analytics Standard (ANLYT-STD) | Pre-built Reports; Dashboard Builder; Data Export (CSV/PDF); Scheduled Reports; Basic Visualizations |
| Analytics Pro (ANLYT-PRO) | Everything in Standard; Predictive Analytics; Custom Models; Data Warehouse Connect; Real-time Dashboards; Embedded Analytics; AI-Powered Insights |
| Integration Hub (INTGR) | 200+ Pre-built Connectors; Custom API Builder; Webhook Support; Data Sync Engine; Transformation Rules; Error Handling & Retry |
| Security Suite (SECUR) | Data Encryption (AES-256); IP Allowlisting; MFA Enforcement; DLP Policies; Compliance Reports (SOC2, HIPAA); Threat Detection; Backup & Recovery |

## Pricing tiers

| Product | Monthly | Annual | Annual savings |
|---------|---------|--------|----------------|
| Core Platform (CORE) | $29/user | $24/user | 17% |
| Enterprise Platform (ENT) | $79/user | $65/user | 18% |
| Analytics Standard (ANLYT-STD) | $19/user | $15/user | 21% |
| Analytics Pro (ANLYT-PRO) | $49/user | $40/user | 18% |
| Integration Hub (INTGR) | $1,500 flat | $15,000 flat | 17% |
| Security Suite (SECUR) | $1,250 flat | $12,500 flat | 17% |

Per-seat rates are per user per month in both columns. Flat rates are per
month in the Monthly column and per year in the Annual column.

## Categories

| Category | Products | Comparison table? |
|----------|----------|-------------------|
| Platform | Core Platform, Enterprise Platform | Yes — 2 products |
| Analytics | Analytics Standard, Analytics Pro | Yes — 2 products |
| Integration | Integration Hub | No — single product |
| Security | Security Suite | No — single product |
