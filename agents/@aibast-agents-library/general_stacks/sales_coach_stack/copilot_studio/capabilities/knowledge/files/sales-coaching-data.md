# Sales Coaching Data

> SYNTHETIC — DEMO DATA. Every rep, prospect, call, and score in this document
> is fictional. This file exists so the agent has a working world to answer
> from on day one. In production, replace this file with tools that read your
> real call recording platform and CRM (see the README's production section).

## Reviewed call library

| ID | Rep | Prospect | Date | Duration | Type | Outcome | Deal Value | Talk Ratio (Rep/Prospect) |
|----|-----|----------|------|----------|------|---------|------------|---------------------------|
| CALL-901 | Alex Rivera | Jennifer Walsh (TechVantage) | 2025-11-12 | 32 min | Discovery | Meeting Scheduled | $185,000 | 58% / 42% |
| CALL-902 | Sarah Kim | David Park (Greenridge Partners) | 2025-11-11 | 45 min | Proposal Review | Verbal Agreement | $72,000 | 45% / 55% |
| CALL-903 | Tom Rivera | Maria Santos (BlueHorizon Health) | 2025-11-10 | 28 min | Renewal Discussion | Expansion Identified | $240,000 | 65% / 35% |

## Call skill scores

Scores are per-call, 0-100. The overall column is the rubric-weighted sum
(see the rubric document), rounded to the nearest whole number.

| ID | Opening | Discovery Questions | Active Listening | Value Articulation | Next Steps | Objection Handling | Weighted Overall |
|----|---------|---------------------|------------------|--------------------|------------|--------------------|------------------|
| CALL-901 | 85 | 72 | 90 | 68 | 95 | 60 | 77 |
| CALL-902 | 92 | 88 | 85 | 91 | 88 | 82 | 88 |
| CALL-903 | 78 | 65 | 82 | 75 | 70 | 55 | 70 |

## Call highlights and improvement areas

### CALL-901 — Alex Rivera

Highlights:
- Strong rapport building in first 3 minutes
- Identified 3 key pain points
- Secured next meeting with VP

Areas for improvement:
- Ask more open-ended discovery questions
- Missed opportunity to quantify business impact
- Did not address competitor mention

### CALL-902 — Sarah Kim

Highlights:
- Excellent value quantification with ROI numbers
- Handled pricing objection confidently
- Clear mutual action plan

Areas for improvement:
- Could have involved more stakeholders
- Missed upsell opportunity for Analytics Pro

### CALL-903 — Tom Rivera

Highlights:
- Customer mentioned expansion plans
- Good understanding of healthcare compliance needs

Areas for improvement:
- Rushed through opening - no personal connection
- Failed to probe deeper on expansion timeline
- Weak close - no specific next meeting date
- Did not handle budget concern effectively

## Rep skill assessments

Assessment skill names are the short forms below. They are the rep-level
vocabulary and are deliberately distinct from the call rubric's names.

| Rep | Overall | Tenure | Quota Attainment | Trend | Team Rank | Opening | Discovery | Listening | Value | Closing | Objections |
|-----|---------|--------|------------------|-------|-----------|---------|-----------|-----------|-------|---------|------------|
| Sarah Kim | 88/100 | 36 months | 115% | Consistent | #1 | 92 | 88 | 85 | 91 | 88 | 82 |
| Alex Rivera | 78/100 | 18 months | 92% | Improving | #3 | 85 | 72 | 90 | 68 | 82 | 60 |
| Tom Rivera | 71/100 | 12 months | 78% | Needs Improvement | #5 | 78 | 65 | 82 | 75 | 70 | 55 |

Team rank is an org-wide stored value, which is why this three-rep roster
holds ranks #1, #3, and #5. Do not renumber the ranks to match row order.

## Focus areas (two lowest skills per rep)

| Rep | Weakest | Second weakest |
|-----|---------|----------------|
| Sarah Kim | Objections 82/100 | Listening 85/100 |
| Alex Rivera | Objections 60/100 | Value 68/100 |
| Tom Rivera | Objections 55/100 | Discovery 65/100 |

## Team rollup

| Metric | Value |
|--------|-------|
| Team Size | 3 |
| Avg Score | 79/100 |
| Avg Quota Attainment | 95% |
| Calls Reviewed | 3 |
