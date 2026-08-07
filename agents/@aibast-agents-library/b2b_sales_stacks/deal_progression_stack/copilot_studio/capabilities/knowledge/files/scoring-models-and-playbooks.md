# Scoring Models and Playbooks

> SYNTHETIC — DEMO DATA. Every threshold, weight, benchmark and playbook in
> this document is fictional demo configuration. This file exists so the agent
> has a working world to answer from on day one. In production, replace this
> file with tools that read your real scoring configuration, playbooks and
> benchmark data (see the README's production section).

## Stage benchmarks and deal classification

Average days a healthy deal spends in each stage:

| Stage | Benchmark Days |
|-------|----------------|
| Qualification | 14 |
| Discovery | 18 |
| Proposal | 16 |
| Negotiation | 12 |
| Contract | 10 |

Classification rule for every active deal, using
`ratio = days_in_stage / stage_benchmark`:

| Classification | Rule |
|----------------|------|
| Stalled | ratio >= 1.25 |
| At risk | ratio >= 1.0, or last contact >= 10 days |
| On track | everything else |

Benchmark close cycle for velocity comparison: 45 days.

## Stall detection thresholds

| Stage | Warning | Stalled | Critical |
|-------|---------|---------|----------|
| Qualification | 12d | 18d | 25d |
| Discovery | 15d | 22d | 30d |
| Proposal | 14d | 20d | 28d |
| Negotiation | 10d | 16d | 24d |
| Contract | 8d | 14d | 20d |

Activity trend, using `change = (activities_last_14d - activities_prior_14d) / activities_prior_14d`:
change <= -0.5 sharp decline, change < 0 declining, change > 0.5 increasing,
otherwise stable. No prior activity means no baseline.

Stall probability: start at 50, add 20 if last contact >= 14 days, add 15 if
champion status is Silent or Disengaged, add 10 if activity trend is declining
or sharp decline, add 10 if next step is "None scheduled". Cap at 95.

## Deal health scoring

Composite = round(engagement x 0.25 + stakeholder x 0.30 + velocity x 0.25 +
sentiment x 0.20), clamped to 0-100.

| Component | Formula |
|-----------|---------|
| engagement | round(email_rate x 30 + touch_score x 0.3 + meeting_score x 0.4) where email_rate = emails_opened / emails_sent, touch_score = max(0, 25 - days_since_last_touch) x 4, meeting_score = min(meetings x 8, 30) |
| stakeholder | round(coverage x 40 + 15 if champion active + 10 if exec sponsor) where coverage = engaged / total |
| velocity | 100 if days_in_stage <= benchmark, else max(0, round(100 - (ratio - 1) x 50)); then subtract 15 per stage regression, floor 0 |
| sentiment | tone score + round(email_responsiveness x 25) + max(0, (positive_signals - objections_raised) x 8) |

Tone scores: very_positive 25, positive 20, neutral 10, cautious 5, negative 0.

Health grades: A >= 80, B >= 65, C >= 50, D >= 35, F below 35.

Health trend: compare the last two periods. Delta > +3 improving, delta < -3
declining, otherwise stable.

Health quartile benchmarks:

| Quartile | Health Score | Engagement Rate | Stakeholder Coverage | Velocity Ratio |
|----------|--------------|-----------------|----------------------|----------------|
| Top quartile | 82 | 0.85 | 0.80 | 0.90 |
| Median | 62 | 0.60 | 0.55 | 1.10 |
| Bottom quartile | 38 | 0.35 | 0.30 | 1.60 |

Health alert rules: CRITICAL when score < 35 or no contact for >= 14 days;
WARNING when the last-period decline is <= -5, when no champion is active, or
when days in stage > 1.5x benchmark; INFO when objections raised >= 3.

## Risk scoring

Composite risk = round(sum of factor score x weight):

| Factor | Weight |
|--------|--------|
| champion_risk | 0.25 |
| competitive_risk | 0.20 |
| budget_risk | 0.15 |
| timeline_risk | 0.15 |
| decision_risk | 0.15 |
| technical_risk | 0.10 |

Severity labels: CRITICAL >= 70, HIGH >= 50, MODERATE >= 30, LOW below 30.

Risk matrix quadrants use a value threshold of $500,000 and a risk threshold of
50/100: Quadrant 1 high value + high risk (immediate action), Quadrant 2 high
value + low risk (protect and accelerate), Quadrant 3 low value + high risk
(evaluate ROI of effort), Quadrant 4 low value + low risk (monitor).

Mitigation plans are generated only for deals with composite risk >= 40, and
cover that deal's top 3 factors by score. A factor at score >= 60 uses the high
playbook, below 60 the medium playbook.

Risk trend direction over 6 weeks: change > +5 worsening, change < -5
improving, otherwise stable.

## Win probability scoring

Win probability = round(sum of factor value x factor weight, 1) x 100.

| Factor | Weight | Avg (Won) | Avg (Lost) | Discriminative Power |
|--------|--------|-----------|------------|----------------------|
| Stage Progression | 0.20 | 85% | 42% | 75% |
| Champion Strength | 0.18 | 82% | 28% | 92% |
| Stakeholder Coverage | 0.12 | 74% | 31% | 82% |
| Activity Momentum | 0.12 | 78% | 35% | 78% |
| Competitive Position | 0.10 | 72% | 38% | 70% |
| Deal Velocity | 0.10 | 70% | 40% | 65% |
| Executive Access | 0.10 | 76% | 22% | 88% |
| Budget Confidence | 0.08 | 80% | 45% | 62% |

Top factor = highest value x weight contribution. Biggest gap = highest
(1 - value) x weight. Probability trend over 6 periods: overall change > +0.05
improving, < -0.05 declining, otherwise stable.

## Stakeholder engagement scoring

Contact score = min(100, email_score + meeting_score + recency_score +
sentiment_score) where email_score = min(emails x 5, 30), meeting_score =
min(meetings x 15, 30), recency_score = max(0, 25 - last_touch_days) x 1.5,
sentiment_score = sentiment signal score x 0.2.

Deal engagement = influence-weighted average of contact scores, weights
very_high 3, high 2, medium 1.5, low 1. Grades A >= 75, B >= 55, C >= 40,
D below 40.

| Sentiment | Score | Label | Risk |
|-----------|-------|-------|------|
| very_positive | 90 | Strong advocate | low |
| positive | 70 | Favorable | low |
| neutral | 50 | Undecided | medium |
| cautious | 35 | Hesitant | medium |
| frustrated | 30 | Frustrated but engaged | high |
| negative | 15 | Opposed | critical |
| unknown | 40 | No signal | medium |

Relationship gap rules: no contact with support level champion, no Executive
Sponsor or Economic Buyer touched within 14 days, no Technical Evaluator with
positive or very_positive sentiment, any high or very_high influence contact
with no contact for >= 21 days, and fewer than 3 contacts mapped.

Engagement plan rules per contact: score < 40 means re-engagement outreach;
otherwise last touch >= 14 days means schedule a touchpoint; otherwise support
level unknown means sentiment discovery. Deal-level sentiment risk is HIGH with
2 or more high/critical risk contacts, MEDIUM with 1, LOW with none.

## Stage activity requirements

| Stage | Min Completion | Activities |
|-------|----------------|------------|
| Qualification | 80% | Q1-Q5 |
| Discovery | 75% | D1-D6 |
| Proposal | 70% | P1-P6 |
| Negotiation | 80% | N1-N5 |
| Contract | 90% | C1-C4 |

| ID | Activity | Weight | Description |
|----|----------|--------|-------------|
| Q1 | Initial discovery call | 3 | 30-min intro call with prospect |
| Q2 | BANT qualification | 3 | Budget, Authority, Need, Timeline assessed |
| Q3 | Pain point documentation | 2 | Documented business pain points |
| Q4 | Stakeholder identification | 2 | Key decision makers mapped |
| Q5 | ICP fit assessment | 1 | Ideal customer profile scoring |
| D1 | Technical deep-dive | 3 | Technical requirements session with IT |
| D2 | Business case outline | 3 | Initial ROI and value framework |
| D3 | Champion identified | 3 | Internal champion confirmed and engaged |
| D4 | Competitive landscape | 2 | Competitors evaluated and positioned |
| D5 | Multi-thread contacts | 2 | 3+ contacts engaged across departments |
| D6 | Demo or POC delivered | 2 | Product demonstration completed |
| P1 | Formal proposal sent | 3 | Customized proposal delivered to prospect |
| P2 | Pricing presented | 3 | Pricing discussed with decision maker |
| P3 | Executive sponsor meeting | 3 | Meeting with VP+ level stakeholder |
| P4 | Reference calls provided | 2 | Customer references shared |
| P5 | Security/compliance review | 2 | IT security questionnaire completed |
| P6 | Implementation plan shared | 1 | Deployment timeline presented |
| N1 | Terms negotiation call | 3 | Contract terms discussed with procurement |
| N2 | Legal redline review | 3 | Legal review of contract terms |
| N3 | Final pricing approved | 3 | Discount/pricing approved internally |
| N4 | Champion reconfirmed | 2 | Champion commitment validated |
| N5 | Go-live date agreed | 2 | Implementation start date confirmed |
| C1 | Final contract sent | 3 | Executed contract sent for signature |
| C2 | Signature obtained | 3 | Contract signed by authorized signer |
| C3 | PO received | 2 | Purchase order issued |
| C4 | Onboarding handoff | 2 | Customer success team introduced |

26 activities in total. Weight 3 means high priority and CRITICAL severity when
missing; weight 2 medium; weight 1 low.

Gap risk categories:

| Category | Severity | Impact | Blocks Stage |
|----------|----------|--------|--------------|
| champion_missing | critical | 40% lower win rate without active champion | yes |
| executive_access | critical | Deals without exec sponsor close 35% less often | yes |
| pricing_not_discussed | high | Late pricing surprises cause 25% of deal losses | no |
| single_thread | high | Single-threaded deals have 50% higher churn risk | yes |
| no_business_case | high | Deals without ROI justification stall 2x more | yes |
| legal_not_started | high | Legal review adds 8-15 days; late start compounds | no |
| no_references | medium | Reference calls increase win rate by 18% | no |
| security_incomplete | medium | IT security delays add avg 12 days to cycle | no |

## Competitors

| Competitor | Type | Market Share | Funding | Pricing | Avg Discount | Recent Moves |
|-----------|------|--------------|---------|---------|--------------|--------------|
| Vendara Solutions | Direct | 22.4% | $180M Series D | Per-user, $45/mo | 18% | Launched AI add-on Q4 2025; acquired DataSync for integrations |
| Nextera Platform | Direct | 18.7% | $320M Series E | Platform license, $120K/yr base | 12% | Price increase 15% in Jan 2026; lost 3 Fortune 500 accounts |
| CloudFirst Systems | Indirect | 11.2% | $85M Series C | Usage-based, ~$60K/yr avg | 22% | Expanded to EMEA; hired ex-Salesforce CRO |
| Legacy Corp ERP | Incumbent | 31.5% | Public (NYSE - LCE) | Enterprise agreement, $200K+/yr | 8% | Announced cloud migration path; partnership with Accenture |

| Competitor | Strengths | Weaknesses |
|-----------|-----------|------------|
| Vendara Solutions | Lower price point; Fast implementation; Strong SMB presence | Limited enterprise features; No AI/ML capability; Weak integrations |
| Nextera Platform | Strong enterprise features; Gartner leader quadrant; Large partner ecosystem | High total cost; Complex implementation; 18-month avg deployment |
| CloudFirst Systems | Cloud-native architecture; Developer-friendly API; Modern UI | Young company (4 years); Limited customer success team; No on-prem option |
| Legacy Corp ERP | Installed base loyalty; Full ERP suite; Global support | Outdated UX; Slow innovation; Lock-in contracts |

Head-to-head record:

| Competitor | Wins Against | Losses To | Win Rate | Cycle Delta | Key Win Factor | Key Loss Factor |
|-----------|--------------|-----------|----------|-------------|----------------|-----------------|
| Legacy Corp ERP | 18 | 6 | 75.0% | +12 days | Modern platform vs legacy stack | Switching cost fear and executive relationships |
| CloudFirst Systems | 12 | 5 | 70.6% | -3 days | Enterprise maturity and support | Developer mindshare in cloud-native shops |
| Vendara Solutions | 14 | 8 | 63.6% | -5 days | Enterprise feature depth and AI | Price sensitivity in SMB deals |
| Nextera Platform | 9 | 11 | 45.0% | +8 days | Implementation speed and modern UX | Brand recognition and analyst positioning |

Threat score = clamp(10, 95, round(50 + strength_matches x 10 - weakness_matches
x 8 + (50 - our_win_rate_against_them) x 0.3)) where a match counts a
competitor strength or weakness phrase that shares a word with one of the deal's
prospect priorities. Levels CRITICAL >= 70, HIGH >= 50, otherwise MODERATE.

## Next best action library

| Action ID | Name | Effort | Impact | Applicable Stages | Applicable Blockers | Success Rate | Days to Impact | Stage Advance |
|-----------|------|--------|--------|-------------------|---------------------|--------------|----------------|---------------|
| executive_outreach | Executive Sponsor Outreach | 2.0h | 85 | Proposal, Negotiation | executive_change, no_champion, stakeholder_alignment | 72% | 5 | 45% |
| champion_reengagement | Champion Re-engagement | 1.5h | 78 | Discovery, Proposal, Negotiation | executive_change, competitor_eval | 65% | 3 | 35% |
| roi_business_case | ROI Business Case Delivery | 4.0h | 82 | Proposal, Negotiation | budget_hold | 68% | 7 | 40% |
| competitive_differentiation | Competitive Differentiation Session | 3.0h | 75 | Discovery, Proposal | competitor_eval, technical_validation | 62% | 5 | 30% |
| legal_fast_track | Legal Fast-Track Package | 1.0h | 70 | Negotiation, Contract | legal_review, procurement_process | 80% | 4 | 55% |
| reference_call | Customer Reference Call | 1.5h | 72 | Discovery, Proposal | competitor_eval, technical_validation, timeline_uncertainty | 70% | 3 | 28% |
| technical_deep_dive | Technical Deep-Dive Workshop | 3.0h | 68 | Discovery, Proposal | technical_validation | 66% | 5 | 32% |
| multi_thread_outreach | Multi-Thread Outreach Campaign | 2.5h | 65 | Qualification, Discovery | no_champion, stakeholder_alignment | 55% | 7 | 20% |
| contract_negotiation | Contract Terms Negotiation | 2.0h | 80 | Negotiation, Contract | legal_review, procurement_process | 78% | 5 | 50% |
| value_workshop | Value Realization Workshop | 3.5h | 74 | Proposal, Negotiation | budget_hold, timeline_uncertainty | 64% | 8 | 38% |

Action descriptions: Executive Sponsor Outreach is VP-to-VP outreach to
establish executive alignment. Champion Re-engagement is personalized outreach
to a silent or disengaged champion. ROI Business Case Delivery is a CFO-ready
business case with 3-year TCO analysis. Competitive Differentiation Session is
a head-to-head comparison with proof points and references. Legal Fast-Track
Package is a pre-approved contract template with flexible terms. Customer
Reference Call arranges a reference with a similar customer in the same
vertical. Technical Deep-Dive Workshop is a hands-on session with the prospect
engineering team. Multi-Thread Outreach Campaign engages 3+ contacts across
departments simultaneously. Contract Terms Negotiation addresses outstanding
terms with procurement and legal. Value Realization Workshop is an on-site
workshop demonstrating business value and the implementation plan.

Priority score = impact_score x 0.4 + success_rate x 100 x 0.3 +
(100 - days_to_impact x 10) x 0.3, rounded to one decimal.
Expected value impact = deal value x success rate x stage advance rate.
Urgency label: risk >= 60 IMMEDIATE, risk >= 40 THIS WEEK, otherwise STANDARD.

## Blocker playbooks — week 1 and week 2

| Blocker | Diagnosis | Resource |
|---------|-----------|----------|
| executive_change | Champion disengaged, economic buyer changed | exec alignment specialist |
| legal_review | Process bottleneck, not relationship issue | legal team fast-track review |
| competitor_eval | Active competitive evaluation in progress | competitive intelligence team |
| budget_hold | Budget approval stalled or deprioritized | value engineering team |
| no_champion | No internal champion identified or engaged | senior AE for relationship building |

- **executive_change** — Week 1: Day 1 research new executive background
  (LinkedIn, news); Day 2 call existing champion to acknowledge the gap and
  request an intro; Day 3 send executive-tailored ROI analysis; Day 5 executive
  sponsor outreach (your VP to their exec). Week 2: schedule executive meeting
  with business case; re-present proposal with finance lens; establish new
  champion relationship. (7 tasks)
- **legal_review** — Week 1: Today call champion to acknowledge legal delay;
  Tomorrow send pre-approved contract template (removes 80% of redlines); Day 3
  offer 30-day out clause to reduce perceived risk; Day 5 legal-to-legal call
  to resolve remaining items. Week 2: follow up on outstanding redline items;
  escalate any remaining blockers to VP Legal. (6 tasks)
- **competitor_eval** — Week 1: Day 1 request competitive landscape details
  from champion; Day 2 prepare head-to-head comparison deck; Day 3 schedule
  technical deep-dive vs competitor capabilities; Day 5 deliver customer
  reference calls in the same vertical. Week 2: provide proof-of-value pilot
  offer; executive peer reference call; submit best-and-final with
  differentiated terms. (7 tasks)
- **budget_hold** — Week 1: Day 1 confirm budget timeline with champion; Day 2
  build CFO-ready business case with 3-year TCO; Day 3 offer phased
  implementation to reduce upfront cost; Day 5 provide flexible payment terms
  proposal. Week 2: schedule CFO meeting with ROI walkthrough; share peer
  company case study with hard ROI numbers. (6 tasks)
- **no_champion** — Week 1: Day 1 map org chart and identify 3 potential
  champions; Day 2 multi-thread outreach via LinkedIn and email; Day 3 offer
  executive briefing or lunch-and-learn; Day 5 ask existing contacts for warm
  introductions. Week 2: host on-site workshop to build relationships; provide
  industry insights to create value before selling; identify and cultivate
  power sponsor. (7 tasks)

## Intervention playbooks — day by day

| Blocker | Day 1 | Day 2 | Day 3 | Day 5 | Day 7 | Day 10 | Day 14 |
|---------|-------|-------|-------|-------|-------|--------|--------|
| executive_change | Research new executive via LinkedIn, company announcements | Contact existing champion for intel on new leadership priorities | Prepare executive-tailored value proposition | VP-to-VP outreach to new executive | Send industry insight piece to build credibility | Schedule executive briefing meeting | Present revised business case to new stakeholders |
| legal_review | Send pre-approved contract template to reduce redlines | Schedule legal-to-legal call | Offer 30-day out clause to reduce perceived risk | Follow up on outstanding redline items | Escalate remaining items to VP Legal | Present final contract for signature | - |
| competitor_eval | Request competitive landscape details from champion | Prepare head-to-head comparison deck | Schedule technical deep-dive vs competitor | Deliver customer reference calls in same vertical | Offer differentiated proof-of-value pilot | Submit best-and-final with differentiated terms | - |
| budget_hold | Confirm budget timeline with champion | Build CFO-ready business case with 3-year TCO | Offer phased implementation to reduce upfront cost | Provide flexible payment terms proposal | Schedule CFO meeting with ROI walkthrough | Share peer company case study with hard ROI | - |
| no_champion | Map org chart and identify 3 potential champions | Multi-thread outreach via LinkedIn and email | Offer executive briefing or lunch-and-learn | Ask existing contacts for warm introductions | Host on-site workshop to build relationships | Provide industry insights to create value | Evaluate deal viability if no champion emerges |

## Root cause taxonomy

| Root Cause | Category | Severity | Description | Recovery Probability | Avg Recovery Days |
|-----------|----------|----------|-------------|----------------------|-------------------|
| executive_change | Organizational | critical | Executive leadership change disrupted buying process | 45% | 18 |
| legal_review | Process | high | Legal and contract review creating bottleneck | 75% | 10 |
| competitor_eval | Competitive | high | Active competitive evaluation extended decision timeline | 55% | 14 |
| budget_hold | Financial | high | Budget approval stalled or deprioritized | 60% | 20 |
| no_champion | Relationship | critical | No internal champion to drive deal forward | 35% | 22 |

## Mitigation playbooks

High playbooks (factor score >= 60) run 4 steps; medium playbooks (below 60)
run 3 steps.

- **champion_risk high**: identify 3 alternative champion candidates in the org
  chart; multi-thread outreach via LinkedIn, email and mutual connections;
  offer an executive briefing or value workshop; escalate to your VP for
  peer-level executive outreach. **Medium**: weekly touchpoints with the
  current champion; identify a backup champion; share exclusive industry
  insights.
- **budget_risk high**: build a CFO-ready business case with 3-year TCO and
  ROI; offer phased implementation; provide flexible payment terms or a
  subscription model; connect the champion with finance for internal advocacy.
  **Medium**: confirm budget cycle timing and approval process; share peer ROI
  case studies; offer bridge pricing or a pilot.
- **competitive_risk high**: prepare a head-to-head comparison with proof
  points; arrange customer reference calls in the same vertical; offer a
  differentiated proof-of-value engagement; accelerate the timeline to shrink
  the evaluation window. **Medium**: monitor competitive activity through the
  champion; reinforce differentiators; share the battle card internally.
- **decision_risk high**: map the complete buying committee and decision
  process; secure an executive sponsor meeting within 5 business days; provide
  a decision framework to the champion; address individual stakeholder
  concerns. **Medium**: validate decision criteria and timeline; ensure all
  decision makers received value messaging; schedule a group demo or workshop.
- **timeline_risk high**: reset the mutual action plan with new target dates;
  identify and address the specific bottleneck; offer implementation
  accelerators or quick-start packages; escalate internally for resource
  prioritization. **Medium**: review and update the mutual action plan;
  schedule weekly checkpoints; pre-stage next-step resources.
- **technical_risk high**: schedule a technical deep-dive with a solutions
  architect; provide security and compliance documentation proactively; offer
  an extended POC or pilot; connect the prospect technical team with
  engineering leadership. **Medium**: share technical documentation and
  architecture overview; answer open technical questions in writing; offer
  technical office hours.

All critical mitigations begin within 48 hours and are reviewed in the weekly
pipeline meeting.

## Pipeline velocity model

Pipeline velocity = round(deal count x avg deal value x avg win rate /
avg cycle days).

| Transition | Conversion Rate | Avg Days | Benchmark Days |
|-----------|-----------------|----------|----------------|
| Qualification to Discovery | 72% | 12 | 14 |
| Discovery to Proposal | 58% | 16 | 18 |
| Proposal to Negotiation | 65% | 15 | 16 |
| Negotiation to Contract | 78% | 11 | 12 |
| Contract to Closed Won | 88% | 7 | 10 |

| Stage | Target Days | Median | P75 | P90 |
|-------|-------------|--------|-----|-----|
| Qualification | 14 | 11 | 16 | 22 |
| Discovery | 18 | 14 | 20 | 28 |
| Proposal | 16 | 12 | 18 | 26 |
| Negotiation | 12 | 9 | 14 | 20 |
| Contract | 10 | 6 | 10 | 15 |

Deal timing status: ratio <= 1.0 ON TRACK, ratio <= 1.5 SLOW, above 1.5
STALLED. A stage is a bottleneck when a deal's days in its current stage exceed
that stage's target days.

| Quarter | Avg Cycle | Pipeline Value | Deals Closed | Velocity Index |
|---------|-----------|----------------|--------------|----------------|
| Q1 2025 | 58d | $8,200,000 | 14 | $1,980,000/day |
| Q2 2025 | 54d | $9,100,000 | 16 | $2,700,000/day |
| Q3 2025 | 51d | $10,400,000 | 18 | $3,670,000/day |
| Q4 2025 | 48d | $11,200,000 | 21 | $4,900,000/day |

Acceleration target = round(current average cycle x 0.78), a 22% reduction.

Stage acceleration actions: Qualification — automated BANT scoring, discovery
call within 48h of lead assignment, 14-day SLA with escalation. Discovery —
multi-threading by day 10, champion identification before stage exit, POC or
demo in the first week. Proposal — pre-stage the executive sponsor meeting,
include competitive differentiation in every proposal, 16-day stage SLA with
weekly reviews. Negotiation — pre-approved contract templates on day 1,
legal-to-legal call within 3 business days, flexible payment terms. Contract —
deal desk support for all contracts over $200K, e-signature with 48-hour
reminder cadence, pre-scheduled onboarding kickoff.

## Revenue forecast model

Weighted forecast = sum of deal value x probability.

| Setting | Value |
|---------|-------|
| Q1 2026 quota | $5,200,000 |
| Team size | 5 |
| Per-rep quota | $1,040,000 |
| Seasonal adjustment Q1 | 0.92x |
| Seasonal adjustment Q2 | 1.05x |
| Seasonal adjustment Q3 | 0.98x |
| Seasonal adjustment Q4 | 1.12x |

Scenario multipliers applied per forecast category:

| Scenario | commit | best_case | upside | pipeline |
|----------|--------|-----------|--------|----------|
| Best Case | 0.95 | 0.80 | 0.50 | 0.25 |
| Expected | 0.85 | 0.55 | 0.25 | 0.10 |
| Worst Case | 0.70 | 0.30 | 0.10 | 0.05 |

The expected scenario carries 72% confidence based on historical patterns.

| Quarter | Forecast | Actual | Accuracy | Variance |
|---------|----------|--------|----------|----------|
| Q1 2025 | $3,200,000 | $3,450,000 | 92.8% | +7.8% |
| Q2 2025 | $3,800,000 | $3,620,000 | 95.3% | -4.7% |
| Q3 2025 | $4,100,000 | $4,280,000 | 95.8% | +4.4% |
| Q4 2025 | $4,900,000 | $5,100,000 | 96.1% | +4.1% |

Expected accuracy for the current quarter = min(4-quarter average + 0.5, 98.0).
Confidence range = weighted forecast x (1 -/+ (100 - expected accuracy) / 100).
Historical conversion: commit category accuracy 94%, best case 62%, upside 28%.
