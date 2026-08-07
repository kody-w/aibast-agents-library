# Tone and Personalization Reference

> SYNTHETIC — DEMO DATA. Every tone setting, field, and sample recipient in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real brand voice guide, CRM contact records, and sender profiles (see the
> README's production section).

## Tone settings

| Tone | Formality | Warmth | Urgency | Use Case |
|------|-----------|--------|---------|----------|
| Professional | High | Medium | Low | Enterprise outreach, formal proposals |
| Consultative | Medium | High | Low | Discovery calls, advisory communications |
| Friendly | Low | High | Low | Follow-ups, relationship maintenance |
| Urgent | Medium | Low | High | Time-sensitive offers, renewal deadlines |
| Executive | High | Low | Medium | C-suite communications, board summaries |

The Use Case column is truncated to the first 40 characters when rendered in the
template library output.

Each template carries its own fixed tone string, which is what a draft reports:

| Template key | Tone reported on the draft |
|--------------|----------------------------|
| cold_outreach | Professional, consultative |
| follow_up_no_reply | Friendly, low-pressure |
| proposal_intro | Formal, value-focused |
| meeting_follow_up | Professional, action-oriented |

## Personalization fields

| Category | Fields |
|----------|--------|
| Recipient | first_name, last_name, title, company_name, industry |
| Context | pain_point, observation, topic, meeting_date, meeting_topic |
| Value | product_name, reference_customer, result, roi_projection, pricing |
| Sender | sender_name, sender_title, sender_email, sender_phone |
| Scheduling | time_slot_1, time_slot_2, proposed_meeting_date |

Any `{token}` in a template body or subject that is not supplied a value renders
literally in the draft. Tokens used by templates but absent from the field
catalog above — `our_product`, `original_subject`, `value_prop_one_liner`,
`project_name`, `executive_summary`, `timeline`, `discussion_points`,
`action_items`, `next_steps` — must be supplied by the sender and are never
invented.

## Sample recipient context

Used when the request supplies no context of its own.

| Field | Value |
|-------|-------|
| first_name | Jennifer |
| last_name | Walsh |
| title | VP of Operations |
| company_name | TechVantage Solutions |
| industry | Technology |
| pain_point | operational efficiency |
| observation | expanding rapidly into new markets |
| topic | digital transformation |
| product_name | Enterprise Platform |
| reference_customer | Meridian Corp |
| result | 35% improvement in operational throughput |
| sender_name | Alex Rivera |
| sender_title | Account Executive |
| meeting_date | November 12 |
| meeting_topic | platform evaluation |
| pricing | $185,000/year |
| roi_projection | 3.2x within 18 months |
| time_slot_1 | Tuesday 2:00 PM |
| time_slot_2 | Thursday 10:00 AM |

The cold outreach draft derives the recipient address from this context as
`jennifer.walsh@techvantage.com` (first name and last name lowercased, joined by
a dot, at `techvantage.com`). No other recipient address exists in this data.
