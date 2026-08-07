# Competitive Intel and Intervention Catalog

> SYNTHETIC — DEMO DATA

This file is the synthetic competitor profile set, buyer-quote library, and
intervention catalog the agent answers from. In production it is removed and
replaced with tools reading the competitive intelligence repository, the
win/loss survey platform, and the funded program plan. Nothing here is a real
competitor, customer, or budget.

## Competitor profiles

| Competitor | Strength | Weakness |
|---|---|---|
| CompetitorX | Enterprise security certs (FedRAMP, ISO 27001) | Poor UX, slow implementation |
| CompetitorY | Low price point, bundled analytics | Limited API, weak support |
| CompetitorZ | Industry-specific templates | No multi-cloud, small team |

Standing competitive facts used in the security and reference deep dives:

- CompetitorX holds FedRAMP certification; we do not.
- CompetitorX leads with SOC 2 Type II + ISO 27001 in every proposal.
- Enterprise buyers require those certifications for procurement approval.
- CompetitorX has 12 Fortune 500 logos available for reference; we have 3
  enterprise references currently available.

## Buyer quotes by loss reason

| Loss reason | Representative buyer quote |
|---|---|
| Security certifications | "We loved the product but couldn't get past security review" |
| Enterprise references | "We need peer validation from companies our size before we commit" |
| Pricing | "The total cost was above our budget threshold for this category" |
| Feature gaps | "Missing capabilities we consider table-stakes for our use case" |
| Relationship/trust | "We had stronger rapport and trust with the competing vendor team" |

Win/loss interview insight: 8 of 10 lost buyers said they preferred our UX but
could not justify the security/reference risk.

## Intervention catalog

Recovery rate is the fraction of applicable lost pipeline the model treats as
recoverable. Cost and timeline are fixed catalog values.

| Intervention | Cost | Recovery rate | Timeline | Mapped loss reasons |
|---|---|---|---|---|
| Security Positioning Refresh | $25,000 | 0.35 | Immediate | security_certs |
| FedRAMP Certification | $85,000 | 0.55 | 6 months | security_certs |
| Enterprise Reference Program | $30,000 | 0.40 | 30 days | enterprise_references, relationship |
| Pricing & Packaging Adjustment | $15,000 | 0.30 | Immediate | pricing |
| ISO 27001 Certification | $25,000 | 0.20 | 4 months | (none) |

`feature_gaps` and `no_decision` have no mapped intervention. Total catalog
cost is $180,000.

## Modeled recovery, Q3 losses

| Intervention | Applicable deals | Applicable pipeline | Recoverable value | Deal band | ROI |
|---|---|---|---|---|---|
| FedRAMP Certification | 12 | $7,450,000 | $4,097,500 | 4-7 | 48.2:1 |
| Security Positioning Refresh | 12 | $7,450,000 | $2,607,500 | 2-4 | 104.3:1 |
| Enterprise Reference Program | 16 | $5,245,000 | $2,098,000 | 4-7 | 69.9:1 |
| Pricing & Packaging Adjustment | 20 | $4,628,000 | $1,388,400 | 4-6 | 92.6:1 |
| ISO 27001 Certification | 0 | $0 | $0 | 1-1 | 0.0:1 |

Total recoverable $10,191,400 on $180,000 investment = 56.6:1. The security
positioning and FedRAMP rows both claim the same 12 deals, so the total is not
a clean sum of distinct pipeline.

## Intervention action lists

**Security Positioning Refresh** ($25,000, Immediate)
- Lead with SOC 2 Type II (currently underutilized in sales materials)
- Create Security Architecture one-pager for enterprise buyers
- Offer security team direct access during evaluation period
- Bridge messaging: FedRAMP in progress, SOC 2 + ISO active now

**Enterprise Reference Program** ($30,000, 30 days)
- Activate 3 enterprise customers for reference calls
- Produce 2 video testimonials from Fortune 1000 logos
- Offer reference incentives (extended support, discounts)
- Build enterprise customer advisory board

**Pricing & Packaging Adjustment** ($15,000, Immediate)
- Enterprise tier: bundle security features at no extra cost
- Offer 90-day pilot with success-based conversion
- Match competitor payment terms flexibility
- Introduce volume discount for multi-year commits

**FedRAMP Certification** ($85,000, 6 months)
- Engage FedRAMP 3PAO for readiness assessment
- Assign dedicated compliance engineering team
- Target FedRAMP Moderate authorization

**ISO 27001 Certification** ($25,000, 4 months)
- Engage certification body for gap assessment
- Implement required ISMS controls
- Complete Stage 1 and Stage 2 audits

## Updated talk track

"We're the secure choice for enterprises who want modern UX. Here's our SOC 2
Type II, and our FedRAMP is in progress. Let us connect you with 3 enterprise
references in your industry."

## Classification rules

Impact tier by frequency within the competitor's losses: `>= 25%` High,
`>= 10%` Medium, below 10% Low.

Addressability lookup:

| Loss reason | Addressable? |
|---|---|
| security_certs | Yes (6 months) |
| enterprise_references | Yes (3 months) |
| pricing | Yes (immediate) |
| feature_gaps | Roadmap item |
| no_decision | Partially (nurture) |
| relationship | Yes (engagement plan) |

Forecast constants: 62% of recoverable pipeline is treated as realizable in Q4;
the Q4 win-rate lift is `15% of (recoverable / total lost value)` in points;
each subsequent quarter adds 4.0 points.
