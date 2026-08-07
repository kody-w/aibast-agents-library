# CRM Intake Templates and Rules

> SYNTHETIC — DEMO DATA. Every template, field, rule, and intake record in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real intake forms, validation configuration, and duplicate detection
> rules (see the README's production section).

## Intake templates

| Template | Display Name | Entity | Fields | Required | Optional | Auto-assign rule |
|----------|--------------|--------|--------|----------|----------|------------------|
| new_lead | New Lead Intake | lead | 8 | 5 | 3 | Round-robin by territory |
| new_account | New Account Intake | account | 7 | 4 | 3 | Territory-based assignment |
| support_case | Support Case Intake | incident | 5 | 5 | 0 | Priority-based queue routing |

### new_lead — New Lead Intake (entity: lead)

| Label | Field Name | Type | Required | Details |
|-------|------------|------|----------|---------|
| First Name | first_name | text | Yes | max: 50 |
| Last Name | last_name | text | Yes | max: 50 |
| Email | email | email | Yes | max: 100 |
| Company | company | text | Yes | max: 160 |
| Phone | phone | phone | No | max: 20 |
| Lead Source | source | picklist | Yes | Website, Referral, Trade Show, Cold Call, LinkedIn |
| Product Interest | interest | picklist | No | Platform, Analytics, Integration, Support |
| Notes | notes | textarea | No | max: 2000 |

### new_account — New Account Intake (entity: account)

| Label | Field Name | Type | Required | Details |
|-------|------------|------|----------|---------|
| Company Name | company_name | text | Yes | max: 160 |
| Industry | industry | picklist | Yes | Technology, Healthcare, Finance, Manufacturing, Retail |
| Annual Revenue | revenue | currency | No | |
| Number of Employees | employees | number | No | |
| Website | website | url | No | max: 200 |
| City | city | text | Yes | max: 80 |
| State/Province | state | text | Yes | max: 50 |

### support_case — Support Case Intake (entity: incident)

| Label | Field Name | Type | Required | Details |
|-------|------------|------|----------|---------|
| Contact Email | contact_email | email | Yes | max: 100 |
| Subject | subject | text | Yes | max: 200 |
| Description | description | textarea | Yes | max: 5000 |
| Priority | priority | picklist | Yes | Critical, High, Medium, Low |
| Category | category | picklist | Yes | Technical, Billing, Feature Request, General |

## Validation rules

| Rule | Pattern | Error Message |
|------|---------|---------------|
| email | contains @ and valid domain | Invalid email format |
| phone | 10-15 digits with optional country code | Invalid phone number |
| url | starts with http:// or https:// | Invalid URL format |
| currency | numeric, non-negative | Invalid currency value |
| required | non-empty value | Required field cannot be empty |
| max_length | within character limit | Value exceeds maximum length |

## Duplicate detection rules

### lead — action on duplicate: Flag for review

| Rule | Fields | Match Type | Confidence |
|------|--------|------------|------------|
| Email Match | email | exact | High |
| Name + Company | first_name, last_name, company | fuzzy | Medium |
| Phone Match | phone | exact | High |

### account — action on duplicate: Merge suggestion

| Rule | Fields | Match Type | Confidence |
|------|--------|------------|------------|
| Company Name | company_name | fuzzy | Medium |
| Website Domain | website | domain_match | High |
| Name + City | company_name, city | fuzzy | Low |

### incident — action on duplicate: Link to existing case

| Rule | Fields | Match Type | Confidence |
|------|--------|------------|------------|
| Subject + Contact | subject, contact_email | fuzzy | Medium |

## Sample intake batch (5 records)

| First Name | Last Name | Email | Company | Source | Status | Import Action |
|------------|-----------|-------|---------|--------|--------|---------------|
| Elena | Kowalski | elena.k@techstart.io | TechStart Inc | LinkedIn | Valid | Create |
| Marcus | Thompson | marcus.t@healthpro.com | HealthPro Solutions | Trade Show | Valid | Create |
| Rachel | Chen | rachel.chen@existing-customer.com | Existing Customer LLC | Referral | Duplicate Detected | Review |
| David | | david@newcorp.com | NewCorp | Website | Validation Error: Last name required | Skip |
| Sarah | Williams | sarah.w@summit.com | Summit Partners | Cold Call | Valid | Create |

Batch totals: 3 valid, 1 duplicate, 1 error. Duplicate match:
rachel.chen@existing-customer.com by Email Match (exact, High confidence).
Estimated import time 2 seconds; auto-assignment Round-robin by territory.
