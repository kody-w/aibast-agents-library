# Customer 360 Profiles and Interaction Log

> SYNTHETIC — DEMO DATA. Every customer, order, email address, phone number,
> and interaction in this document is fictional. This file exists so the agent
> has a working world to answer from on day one. In production, replace this
> file with tools that read your real CRM, order system, and contact-center
> interaction log (see the README's production section).

## Customer profiles

| ID | Name | Email | Phone | Segment | Lifetime Value | Member Since | Preferred Channel |
|----|------|-------|-------|---------|----------------|--------------|-------------------|
| C360-001 | Jessica Alvarez | j.alvarez@example.com | (555) 234-5678 | premium | 12450 | 2019-06-15 | mobile_app |
| C360-002 | Brian O'Connell | b.oconnell@example.com | (555) 876-1234 | standard | 3280 | 2022-01-10 | website |
| C360-003 | Mei Lin Zhang | m.zhang@example.com | (555) 445-9012 | at_risk | 5890 | 2020-09-22 | phone |

Total lifetime value across the book: **$21,620**.

## Purchase history summary

| ID | Total Orders | Avg Order Value | Last Order | Return Rate |
|----|--------------|-----------------|------------|-------------|
| C360-001 | 47 | 264.89 | 2025-02-28 | 4.2% |
| C360-002 | 15 | 218.67 | 2025-01-15 | 8.0% |
| C360-003 | 28 | 210.36 | 2024-10-05 | 12.5% |

## Preferences

| ID | Categories | Communication | Language |
|----|------------|---------------|----------|
| C360-001 | electronics, home | email | en |
| C360-002 | sports, outdoor | sms | en |
| C360-003 | fashion, beauty | email | en |

## Interaction log — C360-001, Jessica Alvarez

| Date | Channel | Type | Details | Sentiment | Agent |
|------|---------|------|---------|-----------|-------|
| 2025-03-05 | mobile_app | purchase | Order #ORD-88421 — Wireless Speaker | positive | (none) |
| 2025-02-20 | chat | inquiry | Asked about loyalty points redemption | positive | ChatBot |
| 2025-02-10 | email | campaign_click | Clicked spring sale email — viewed 3 products | neutral | (none) |
| 2025-01-28 | phone | support | Delivery delay on order #ORD-87910 | negative | Agent_Kelly |

## Interaction log — C360-002, Brian O'Connell

| Date | Channel | Type | Details | Sentiment | Agent |
|------|---------|------|---------|-----------|-------|
| 2025-01-15 | website | purchase | Order #ORD-85220 — Hiking Boots | positive | (none) |
| 2025-01-02 | email | campaign_open | Opened New Year promotion email | neutral | (none) |

## Interaction log — C360-003, Mei Lin Zhang

| Date | Channel | Type | Details | Sentiment | Agent |
|------|---------|------|---------|-----------|-------|
| 2024-12-15 | phone | complaint | Wrong size shipped on order #ORD-84100 — requested refund | negative | Agent_Marcus |
| 2024-10-05 | website | purchase | Order #ORD-82450 — Fall collection items | neutral | (none) |
| 2024-09-20 | chat | support | Sizing guidance for dresses | positive | ChatBot |
| 2024-08-14 | phone | complaint | Late delivery — order arrived 5 days after estimate | negative | Agent_Kelly |

An interaction with no agent recorded was unattended and is rendered as
`Self-Service` in output.

## Sentiment scoring reference

Values: `positive = +1`, `neutral = 0`, `negative = -1`. The score is the
average across that customer's interactions, rounded to two decimals. The
label is `positive` when the score is greater than 0.30, `negative` when it is
less than -0.30, and `neutral` otherwise.

| ID | Name | Interactions | Sum | Score | Label | Negative Count |
|----|------|--------------|-----|-------|-------|----------------|
| C360-001 | Jessica Alvarez | 4 | +1 | 0.25 | Neutral | 1 |
| C360-002 | Brian O'Connell | 2 | +1 | 0.5 | Positive | 0 |
| C360-003 | Mei Lin Zhang | 4 | -1 | -0.25 | Neutral | 2 |

No customer in this data set carries a `Negative` overall label, so the
at-risk section of the sentiment report is empty. Mei Lin Zhang is the lowest
scorer at -0.25, which sits above the -0.30 negative threshold.
