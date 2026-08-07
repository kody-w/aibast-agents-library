# Supplier Risk Scoring and Sourcing Policy

> SYNTHETIC — DEMO DATA. A fictional manufacturer's policy, included so the
> agent's thresholds and guardrails are grounded in a citable document rather
> than only in its instructions. In production, replace this file with your
> own governance document and the tools that enforce it.

## Why the model is fixed

Supplier risk decisions move real money and real production schedules. If the
weights or the bands can be argued with, two buyers reach two answers from the
same data. The scoring model is therefore arithmetic, applied identically to
every supplier, every time.

## Composite health score

Composite health is a 0-100 measure, higher is healthier:

`composite = quality x 0.30 + delivery x 0.25 + financial x 0.25 + geopolitical x 0.20`

rounded to one decimal place. Quality carries the largest weight because a
quality escape reaches the customer; geopolitical carries the smallest because
it is the slowest-moving dimension.

## Dimension status bands

Applied identically to quality, delivery, financial, and geopolitical scores.

| Score | Status |
|-------|--------|
| >= 80 | Good |
| 60 - 79 | Watch |
| < 60 | At Risk |

## Overall risk tiers

Overall risk is a separate 0-10 measure, higher is riskier. It is not derived
from the composite health score and must never be presented as one.

| Overall risk | Tier |
|--------------|------|
| >= 7.0 | CRITICAL |
| 5.0 - 6.9 | HIGH |
| 3.0 - 4.9 | MODERATE |
| < 3.0 | LOW |

## Spend-at-risk threshold

Annual spend with any supplier scoring `>= 5.0` overall risk is counted as
spend at elevated risk. The threshold is 5.0 and is not adjusted per category,
per region, or per quarter.

## Sourcing recommendation rule

1. Only an alternative whose qualification status is `Qualified` may be
   recommended for activation. `In Progress` and `Not Started` sources are
   never recommended for activation regardless of lead time or urgency.
2. Among qualified alternatives, the lowest cost premium wins. Lead time does
   not override cost premium at this step.
3. If no alternative is qualified, the recommendation is to accelerate
   qualification of the shortest-lead-time option.
4. The cost of full diversification is modelled as the incumbent's annual
   spend multiplied by the lowest available premium for that incumbent.

## Authority boundary

The agent recommends. Only a buyer or category manager activates a backup,
moves volume, cancels or reprices a contract, opens a corrective action, or
notifies a supplier. The agent never states or implies that any of those
things have happened.
