# Fraud Monitoring Data

> SYNTHETIC — DEMO DATA. Every cardholder, account, merchant, transaction, and
> investigation case in this document is fictional. Account numbers are masked
> and no full PAN exists anywhere in this data. This file exists so the agent
> has a working world to answer from on day one. In production, replace this
> file with tools that read your real transaction monitoring feed and case
> management system (see the README's production section).

## Monitored transactions

| TXN ID | Account | Cardholder | Amount | Merchant | Category | Country | Timestamp | Channel | Risk Score |
|--------|---------|------------|--------|----------|----------|---------|-----------|---------|------------|
| TXN-90001 | 4532-XXXX-8891 | James Peterson | $4,850.00 | ElectroMax Dubai | electronics | AE | 2025-03-05T02:15:00 | card_present | 88 |
| TXN-90002 | 4532-XXXX-8891 | James Peterson | $2,100.00 | Gold Souq Trading | jewelry | AE | 2025-03-05T02:42:00 | card_present | 92 |
| TXN-90003 | 4716-XXXX-3304 | Lisa Wang | $12,500.00 | CryptoSwap Exchange | crypto | US | 2025-03-04T18:30:00 | online | 75 |
| TXN-90004 | 4716-XXXX-3304 | Lisa Wang | $9,800.00 | CryptoSwap Exchange | crypto | US | 2025-03-04T18:35:00 | online | 82 |
| TXN-90005 | 5412-XXXX-6678 | Robert Miles | $189.99 | Amazon.com | retail | US | 2025-03-05T10:20:00 | online | 12 |
| TXN-90006 | 5412-XXXX-6678 | Robert Miles | $3,200.00 | WireTransfer-NG | wire_transfer | NG | 2025-03-05T11:05:00 | online | 95 |
| TXN-90007 | 4024-XXXX-1190 | Elena Vasquez | $67.50 | Whole Foods Market | grocery | US | 2025-03-05T09:15:00 | contactless | 5 |

## Investigation cases

| Case ID | Alert Transactions | Rules Triggered | Pattern | Status | Priority | Analyst | Opened |
|---------|--------------------|-----------------|---------|--------|----------|---------|--------|
| INV-2025-301 | TXN-90001, TXN-90002 | RULE-001, RULE-002 | card_cloning | open | high | Karen Wright | 2025-03-05 |
| INV-2025-302 | TXN-90006 | RULE-004 | account_takeover | escalated | critical | David Chen | 2025-03-05 |
| INV-2025-303 | TXN-90003, TXN-90004 | RULE-003 | (none assigned) | under_review | medium | Karen Wright | 2025-03-04 |

## Case notes

| Case ID | Notes |
|---------|-------|
| INV-2025-301 | Cardholder confirmed they are not traveling. Card blocked. Replacement issued. |
| INV-2025-302 | Wire to Nigeria following password reset 90 minutes prior. SAR filing initiated. |
| INV-2025-303 | Customer confirmed crypto purchases. Monitoring for additional activity. |

INV-2025-303 has no pattern assigned. It is reported as Under Analysis in a case
detail view and as TBD in the register. It is not to be inferred from the
transactions, the rule, or the notes.
