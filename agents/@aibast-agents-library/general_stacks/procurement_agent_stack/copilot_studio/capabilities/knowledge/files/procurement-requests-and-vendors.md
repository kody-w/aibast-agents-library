# Procurement Requests and Vendors

> SYNTHETIC — DEMO DATA. Every purchase request, purchase order, requester,
> vendor, and dollar figure in this document is fictional. This file exists so the agent has a
> working world to answer from on day one. In production, replace this file
> with tools that read your real ERP purchase requisitions and vendor master
> (see the README's production section).

## Purchase request queue

| ID | Title | Requester | Department | Category | Amount | Priority | Status | Preferred Vendor | Budget Code |
|----|-------|-----------|------------|----------|--------|----------|--------|------------------|-------------|
| PR-5001 | Cloud Infrastructure Upgrade | Sarah Chen | IT | Technology | $125,000 | High | Pending Approval | AWS | IT-INFRA-2025 |
| PR-5002 | Office Furniture - New Floor Build-Out | Tom Rivera | Facilities | Office Supplies | $48,500 | Medium | Vendor Selection | Steelcase | FAC-CAPEX-2025 |
| PR-5003 | Annual Software License Renewal - Salesforce | Mike Torres | Sales | Software | $215,000 | High | Approved | Salesforce | SALES-SW-2025 |
| PR-5004 | Employee Training Program - Leadership Development | Lisa Park | HR | Professional Services | $35,000 | Low | Draft | FranklinCovey | HR-TRAIN-2025 |

### Justifications

| ID | Justification |
|----|---------------|
| PR-5001 | Current infrastructure at 92% capacity, scaling needed for Q1 growth |
| PR-5002 | 5th floor build-out for 30 new employees starting Q2 |
| PR-5003 | Annual enterprise license renewal, 200 seats |
| PR-5004 | Q2 leadership development program for 25 managers |

## Purchase order ledger

A purchase order is drafted against a purchase request. Only a person issues
an order; the ledger records the state a person left it in.

| ID | Source PR | Vendor | Amount | Payment Terms | Issue Status | Receipt Status |
|----|-----------|--------|--------|---------------|--------------|----------------|
| PO-7001 | PR-5003 | Salesforce (VND-002) | $215,000 | Annual Prepay | Issued | Not Received |
| PO-7002 | PR-5002 | Steelcase (VND-003) | $48,500 | Net 45 | Draft | Not Received |
| PO-7003 | PR-5001 | AWS (VND-001) | $125,000 | Net 30 | Draft | Not Received |

### What holds each draft

| ID | Blocked by |
|----|------------|
| PO-7001 | Nothing - the buyer has issued this order |
| PO-7002 | PR-5002 is in Vendor Selection - vendor not yet selected |
| PO-7003 | PR-5001 is Pending Approval - CFO sign-off outstanding |

PR-5004 has no purchase order drafted; it is still a Draft request.

Order amounts and payment terms match their source request and the vendor
catalog entry. Committed spend in the category budget ledger covers both
issued orders and approved-but-unordered requests, so a drafted order does
not add to committed spend a second time.

## Vendor catalog

All catalogued vendors carry an Active contract status.

| ID | Vendor | Category | Contract Status | Tier | Rating | Annual Spend | Payment Terms | Contact |
|----|--------|----------|-----------------|------|--------|--------------|---------------|---------|
| VND-001 | AWS | Cloud Infrastructure | Active | Strategic | 4.7/5 | $890,000 | Net 30 | Enterprise Account Manager |
| VND-002 | Salesforce | CRM Software | Active | Strategic | 4.5/5 | $430,000 | Annual Prepay | Customer Success Manager |
| VND-003 | Steelcase | Office Furniture | Active | Preferred | 4.3/5 | $125,000 | Net 45 | Account Representative |
| VND-004 | Herman Miller | Office Furniture | Active | Approved | 4.6/5 | $85,000 | Net 30 | Regional Sales |
| VND-005 | Azure | Cloud Infrastructure | Active | Strategic | 4.6/5 | $650,000 | Net 30 | Technical Account Manager |
| VND-006 | FranklinCovey | Training Services | Active | Approved | 4.2/5 | $45,000 | Net 30 | Program Director |

## Vendor tiers

| Tier | What it grants |
|------|----------------|
| Strategic | Long-term partners, best pricing, dedicated support |
| Preferred | Competitive pricing, standard support, pre-approved |
| Approved | Vetted and available, standard terms |

## Categories with a head-to-head

| Category | Competing vendors |
|----------|-------------------|
| Cloud Infrastructure | AWS (VND-001), Azure (VND-005) |
| Office Furniture | Steelcase (VND-003), Herman Miller (VND-004) |
| CRM Software | Salesforce (VND-002) only |
| Training Services | FranklinCovey (VND-006) only |

Source systems: Procurement System (requests and orders), Vendor Management
System (catalog).
