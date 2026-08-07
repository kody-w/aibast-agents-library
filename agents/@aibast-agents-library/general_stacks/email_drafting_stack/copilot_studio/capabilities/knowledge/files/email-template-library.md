# Email Template Library

> SYNTHETIC — DEMO DATA. Every template, benchmark, and recipient in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real template store, CRM, and email engagement metrics (see the README's
> production section).

## Templates

| Key | Name | Category | Tone | Open Rate | Reply Rate | Body Tokens |
|-----|------|----------|------|-----------|------------|-------------|
| cold_outreach | Cold Outreach | Prospecting | Professional, consultative | 32% | 8% | 10 |
| follow_up_no_reply | Follow-Up (No Reply) | Follow-Up | Friendly, low-pressure | 28% | 12% | 6 |
| proposal_intro | Proposal Introduction | Proposal | Formal, value-focused | 65% | 45% | 10 |
| meeting_follow_up | Post-Meeting Follow-Up | Follow-Up | Professional, action-oriented | 72% | 38% | 6 |

Body tokens count the `{...}` placeholders in the body only. Subject-variant
placeholders are not counted.

## Subject line variants

| Key | Variant order | Subject |
|-----|---------------|---------|
| cold_outreach | 1 (used) | `{company_name} + {our_product} - Quick Question` |
| cold_outreach | 2 | `Idea for {company_name}'s {pain_point}` |
| cold_outreach | 3 | `{first_name}, saw your post on {topic}` |
| follow_up_no_reply | 1 (used) | `Re: {original_subject}` |
| follow_up_no_reply | 2 | `Quick follow-up, {first_name}` |
| follow_up_no_reply | 3 | `Still relevant, {first_name}?` |
| proposal_intro | 1 (used) | `Proposal: {project_name} for {company_name}` |
| proposal_intro | 2 | `{company_name} Partnership Proposal` |
| meeting_follow_up | 1 (used) | `Great meeting, {first_name} - Next steps` |
| meeting_follow_up | 2 | `Summary: {meeting_topic} discussion` |

The first variant is always the one rendered as the subject line.

## Template bodies

### cold_outreach — Cold Outreach

```
Hi {first_name},

I noticed {company_name} has been {observation}. Many {industry} leaders we work with have faced similar challenges around {pain_point}.

We helped {reference_customer} achieve {result} using our {product_name}.

Would you be open to a 15-minute call next week to explore if we could deliver similar results for your team?

Best regards,
{sender_name}
{sender_title}
```

### follow_up_no_reply — Follow-Up (No Reply)

```
Hi {first_name},

I wanted to follow up on my previous email about {topic}. I understand you're busy, so I'll keep this brief.

{value_prop_one_liner}

I have a few times available this week if you'd like to connect:
- {time_slot_1}
- {time_slot_2}

If the timing isn't right, no worries - just let me know and I'll circle back later.

Best,
{sender_name}
```

### proposal_intro — Proposal Introduction

```
Dear {first_name},

Thank you for the productive conversation on {meeting_date}. As discussed, I'm pleased to share our proposal for {project_name}.

**Executive Summary:**
{executive_summary}

**Investment:** {pricing}
**Timeline:** {timeline}
**Expected ROI:** {roi_projection}

The attached document contains the full proposal with technical specifications, implementation plan, and customer references.

I'd welcome the opportunity to walk through this with your team. Would {proposed_meeting_date} work for a review session?

Best regards,
{sender_name}
{sender_title}
```

### meeting_follow_up — Post-Meeting Follow-Up

```
Hi {first_name},

Thank you for your time today discussing {meeting_topic}. Here's a quick recap:

**Key Discussion Points:**
{discussion_points}

**Action Items:**
{action_items}

**Next Steps:**
{next_steps}

Please let me know if I missed anything or if you have questions.

Best,
{sender_name}
```

`meeting_follow_up` is available in the library for reference. There is no
drafting operation that renders it.

## Attachment and cadence guidance

| Template | Guidance |
|----------|----------|
| follow_up_no_reply | Send 3-5 business days after the initial email; keep under 100 words; include specific time slots; provide easy opt-out |
| proposal_intro | Suggested attachments: full proposal PDF; ROI calculator spreadsheet; customer reference one-pager |
