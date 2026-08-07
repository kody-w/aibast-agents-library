# Simulation Scoring Rubric

> SYNTHETIC — DEMO DATA. The rubric weights and the sample performance record
> below are fictional training data. This file exists so the agent has a
> working world to answer from on day one. In production, replace this file
> with tools that read your real scoring rubric and call-recording assessments
> (see the README's production section).

## Skill weights

Six skills. Weights sum to 1.00; max points sum to 100.

| Skill | Weight | Max Points | Criteria |
|-------|--------|------------|----------|
| Opening | 10% | 10 | Professional opening, agenda, time check |
| Discovery | 25% | 25 | Open questions, pain identification, qualification |
| Value Prop | 20% | 20 | Customer-specific benefits, ROI, differentiation |
| Objection Handling | 20% | 20 | Framework usage, empathy, evidence-based |
| Closing | 15% | 15 | Clear next steps, mutual commitment, urgency |
| Professionalism | 10% | 10 | Tone, active listening, adaptability |

## Scoring formula

For each skill: `contribution = points x weight / max_points x 100`.
Overall score is the sum of the six contributions, rounded to a whole number.

Because every skill's `weight / max_points x 100` equals 1 in this rubric, the
weighted total equals the raw point total.

**Default for unobserved skills:** `max_points x 0.7` (70% of maximum). When a
default is used, the agent says so — a defaulted skill was not measured.

## Grade bands

| Score | Grade |
|-------|-------|
| 90-100 | A |
| 80-89 | B |
| 70-79 | C |
| 60-69 | D |
| below 60 | F |

## Deal outcome

| Score | Outcome |
|-------|---------|
| 70 or above | Deal Advanced |
| below 70 | Deal Stalled |

There is no third outcome.

## Sample performance record

The stored reference performance used for demonstration.

| Skill | Points | Percentage | Contribution |
|-------|--------|------------|--------------|
| Opening | 8/10 | 80% | 8 |
| Discovery | 18/25 | 72% | 18 |
| Value Prop | 14/20 | 70% | 14 |
| Objection Handling | 16/20 | 80% | 16 |
| Closing | 11/15 | 73% | 11 |
| Professionalism | 9/10 | 90% | 9 |

**Overall: 76/100 — Grade C — Deal Advanced.**

Weakest skill: Value Prop at 70%. Strongest: Professionalism at 90%.

### Feedback attached to this record

- Strong opening and professionalism throughout
- Discovery was thorough but missed budget qualification
- Objection handling was effective on price, needs work on timing
- Clear next steps established

### Improvement plan attached to this record

- Focus on value proposition delivery (scored 70%)
- Practice objection handling frameworks daily
- Review top performer call recordings for closing techniques

**Next simulation:** retry at higher difficulty.
