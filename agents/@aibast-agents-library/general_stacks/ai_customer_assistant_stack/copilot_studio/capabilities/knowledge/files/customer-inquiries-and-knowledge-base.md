# Customer Inquiries and Knowledge Base

> SYNTHETIC — DEMO DATA. Every customer, contact, inquiry, and article in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real CRM, ticketing system, and knowledge base (see the README's
> production section).

## Inquiry queue

| ID | Customer | Account Tier | Contact | Email | Channel | Category | Priority | Sentiment | Created | Status |
|----|----------|--------------|---------|-------|---------|----------|----------|-----------|---------|--------|
| INQ-4001 | Acme Corp | Enterprise | Lisa Park | lisa.park@acmecorp.com | Live Chat | Technical Issue | High | Frustrated | 2025-11-14T09:23:00Z | Open |
| INQ-4002 | Bright Solutions | Professional | Tom Reyes | tom.reyes@brightsol.com | Email | Billing & Pricing | Medium | Neutral | 2025-11-14T10:05:00Z | Open |
| INQ-4003 | Greenfield Inc | Enterprise | Maria Santos | maria.santos@greenfield.io | Phone | Technical Issue | Critical | Urgent | 2025-11-14T08:12:00Z | Open |
| INQ-4004 | Summit Partners | Professional | Jake Miller | jake.miller@summitpartners.com | Support Portal | Feature Request | Low | Positive | 2025-11-13T16:30:00Z | Open |

### Inquiry detail

| ID | Subject | Description |
|----|---------|-------------|
| INQ-4001 | Unable to generate monthly usage report | The export button on the analytics dashboard returns a 500 error when selecting date ranges longer than 30 days. |
| INQ-4002 | Pricing for additional user seats | We are expanding our team by 15 people next quarter and need pricing for additional seats on the Professional plan. |
| INQ-4003 | SSO configuration not working after IdP migration | After migrating from Okta to Azure AD, SSO login redirects to a blank page. SAML assertion looks correct in dev tools. |
| INQ-4004 | Feature request: bulk user import via CSV | Currently we have to add users one at a time. We need CSV import capability for onboarding 200+ users. |

## Knowledge base catalog

| ID | Title | Category | Relevance | Last Updated | Views | Helpful Votes |
|----|-------|----------|-----------|--------------|-------|---------------|
| KB-101 | How to Export Analytics Reports | Analytics | 95% | 2025-10-20 | 1,247 | 892 |
| KB-102 | SSO Configuration Guide (SAML 2.0) | Authentication | 92% | 2025-11-01 | 2,034 | 1,567 |
| KB-103 | User Management and Seat Licensing | Billing | 88% | 2025-09-15 | 3,421 | 2,890 |
| KB-104 | Known Issue: Report Export Timeout for Large Date Ranges | Analytics | 97% | 2025-11-10 | 456 | 398 |

Relevance is a stored property of the article, not a similarity computed
against a query. It is used only to rank the articles that matched.

### KB-101 — How to Export Analytics Reports

Summary: Step-by-step guide for exporting usage and analytics reports in CSV,
PDF, and Excel formats.

1. Navigate to Analytics > Reports
2. Select date range (max 90 days per export)
3. Choose format (CSV, PDF, Excel)
4. Click Export and wait for download link via email

### KB-102 — SSO Configuration Guide (SAML 2.0)

Summary: Complete guide for configuring SAML-based SSO with supported identity
providers.

1. Go to Admin > Security > SSO Settings
2. Upload IdP metadata XML or enter values manually
3. Set Assertion Consumer Service URL to https://app.example.com/sso/callback
4. Map attributes: email, firstName, lastName, groups
5. Test with SSO debug mode enabled before enforcing

### KB-103 — User Management and Seat Licensing

Summary: Overview of seat-based licensing, adding users, and managing
subscriptions.

1. View current seat count in Admin > Billing > Subscription
2. Click Add Seats to purchase additional licenses
3. New seats are prorated for the current billing cycle
4. Bulk provisioning available via SCIM for Enterprise plans

### KB-104 — Known Issue: Report Export Timeout for Large Date Ranges

Summary: Export fails with 500 error for date ranges exceeding 60 days.
Workaround and fix timeline available.

1. Split export into 30-day segments as a workaround
2. Engineering fix scheduled for v3.8.2 (target: Dec 2025)
3. Contact support if you need a one-time bulk export

## How an inquiry finds its articles

The subject line is lowercased and split on whitespace. Tokens of 3 characters
or fewer are discarded. An article matches when any remaining token appears as a
substring of the article's lowercased title. Matches are ranked by relevance
descending. If nothing matches, KB-101 is returned as a fallback.

| Inquiry | Tokens used | Matches (ranked) |
|---------|-------------|------------------|
| INQ-4001 | unable, generate, monthly, usage, report | KB-104 (97%), KB-101 (95%) |
| INQ-4002 | pricing, additional, user, seats | KB-103 (88%) |
| INQ-4003 | configuration, working, after, migration | KB-102 (92%) |
| INQ-4004 | feature, request:, bulk, user, import | KB-103 (88%) |
