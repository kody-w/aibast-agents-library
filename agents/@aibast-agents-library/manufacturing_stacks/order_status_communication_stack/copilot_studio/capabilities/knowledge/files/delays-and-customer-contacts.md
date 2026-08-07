# Delays and Customer Contacts

> SYNTHETIC — DEMO DATA. A fictional manufacturer's delay register and account
> contact list, included so the agent's communication rules are grounded in a
> citable document rather than only in its instructions. In production, replace
> this file with tools that read your real exception log and CRM account
> records (see the README's production section).

## Delay register

An order is "at risk" only if its status is `delayed` or it appears in this
register. Nothing else earns the DELAYED flag.

| Order | Customer | Reason | Original Date | Revised Date | Days Delayed | Cost Impact |
|-------|----------|--------|---------------|--------------|--------------|-------------|
| ORD-7813 | John Deere | Raw material shortage -- alloy steel bar stock delayed from supplier | 2026-03-28 | 2026-04-08 | 11 | $14,200.00 |

### ORD-7813 recovery actions

1. Alternate supplier qualified; first shipment arriving 2026-03-19
2. Weekend overtime shifts approved for CNC cell
3. Partial shipment of 200 units by 2026-03-28

Cost impact is the financial exposure of the delay ($14,200.00). It is not the
order value ($231,000.00) and the two are never merged.

## Customer contacts

| Customer | Account Manager | Escalation Contact | Preferred Channel | SLA Response |
|----------|-----------------|--------------------|-------------------|--------------|
| Ford Motor Company | Sarah Lin | Tom Bradley, Plant Manager | email | 4 hours |
| Caterpillar Inc. | Robert Kim | VP Supply Chain | EDI | 8 hours |
| Tesla Inc. | Sarah Lin | Logistics Director | portal | 2 hours |
| John Deere | Robert Kim | Procurement Director | email | 4 hours |

## Communication policy

1. Customer status messages are **drafts**. The agent prepares them; the named
   account manager reviews and sends them. The agent never sends, queues, or
   confirms delivery of a message.
2. A revised delivery date may only be quoted from the delay register. The
   agent never estimates, rounds, or negotiates a date.
3. Contact the customer through their recorded preferred channel, inside their
   recorded SLA response window. Escalate to the recorded escalation contact
   only when the account manager asks for it.
4. Cost impact, internal reason codes, and account notes stay internal. The
   recorded delay reason is the only internal detail that appears in a
   customer-facing draft.
5. If a customer is not in this contact list, the draft is signed "Account
   Team", the missing contact record is called out, and no channel or SLA is
   assumed beyond the default of email.
