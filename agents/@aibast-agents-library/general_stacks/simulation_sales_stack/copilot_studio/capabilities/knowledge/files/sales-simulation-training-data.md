# Sales Simulation Training Data

> SYNTHETIC — DEMO DATA. Every scenario, buyer persona, and objection in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that
> read your real LMS scenario catalog, persona library, and CRM objection
> history (see the README's production section).

## Scenario catalog

Three scenarios exist. There are no others.

| ID | Name | Difficulty | Industry | Deal Size | Stage | Time Limit |
|----|------|------------|----------|-----------|-------|------------|
| SCN-001 | Enterprise Discovery Call | Intermediate | Financial Services | $250,000 | Discovery | 30 min |
| SCN-002 | Competitive Displacement | Advanced | Healthcare | $180,000 | Proposal | 45 min |
| SCN-003 | Renewal with Expansion | Beginner | Technology | $95,000 | Negotiation | 25 min |

### SCN-001 — Enterprise Discovery Call

**Context:** First meeting with VP of Operations at a mid-size bank. They
reached out after seeing a case study about a competitor.

**Objectives:**
1. Identify top 3 pain points
2. Qualify budget and timeline
3. Map decision-making process
4. Secure follow-up with technical team

### SCN-002 — Competitive Displacement

**Context:** The prospect is using Competitor B and their contract ends in 60
days. They are evaluating alternatives due to poor support.

**Objectives:**
1. Position against Competitor B
2. Address migration concerns
3. Present ROI over 3 years
4. Get verbal commitment to move forward

### SCN-003 — Renewal with Expansion

**Context:** Existing customer for 2 years. Happy with the product but budget
is tight. They need 50 additional licenses.

**Objectives:**
1. Secure renewal commitment
2. Present expansion pricing
3. Handle budget objection
4. Agree on implementation timeline

## Buyer personas

All three personas are available in every scenario.

| Persona | Role | Personality | Priorities | Communication Style |
|---------|------|-------------|------------|---------------------|
| The Analytical CFO | Chief Financial Officer | Data-driven, skeptical, asks for ROI proof | Cost reduction, Compliance, Risk mitigation | Formal, numbers-focused, wants written proposals |
| The Visionary CTO | Chief Technology Officer | Innovation-focused, technical depth, future-looking | Scalability, Integration capabilities, Technical architecture | Technical, whiteboard sessions, wants demos |
| The Pragmatic VP Ops | VP of Operations | Results-oriented, implementation-focused, timeline-driven | Time to value, Ease of deployment, Team adoption | Direct, agenda-driven, wants implementation plans |

### Common objections by persona

| Persona | Objections they raise |
|---------|-----------------------|
| The Analytical CFO | "Show me the ROI data" / "What's the total cost of ownership?" / "How does this compare to building in-house?" |
| The Visionary CTO | "Can it handle our scale?" / "What about vendor lock-in?" / "How does the API compare?" |
| The Pragmatic VP Ops | "What's the implementation timeline?" / "How much training does my team need?" / "What if adoption is low?" |

### Decision factor weights

Each persona weighs the decision differently. Weights sum to 1.00 per persona.

| Persona | Factor weights |
|---------|----------------|
| The Analytical CFO | price 0.35, roi 0.30, risk 0.20, references 0.15 |
| The Visionary CTO | technology 0.35, scalability 0.25, integration 0.25, support 0.15 |
| The Pragmatic VP Ops | implementation 0.30, adoption 0.25, support 0.25, price 0.20 |

## Objection library

| Key | Category | Frequency | Success Rate | Framework |
|-----|----------|-----------|--------------|-----------|
| price | Price | Very Common | 65% | Acknowledge > Quantify Value > Reframe as Investment |
| competitor | Competition | Common | 55% | Validate > Differentiate > Offer Proof |
| timing | Timing | Common | 42% | Acknowledge > Probe Trigger > Quantify Cost of Inaction |
| authority | Authority | Very Common | 72% | Validate > Map Stakeholders > Offer Support |

Success rate is the recorded historical rate for the framework, not a forecast
for any individual rep.

### Price

- **Buyer says:** "Your solution is too expensive compared to alternatives."
- **Recommended response:** I understand budget is important. Let me walk
  through the total value - our customers typically see 3.2x ROI within 18
  months. When you factor in the cost of the problem you're solving ($X/month
  in lost productivity), the investment pays for itself in Q2.

### Competition

- **Buyer says:** "We're already evaluating [Competitor] and they seem to have
  similar features."
- **Recommended response:** It's smart to evaluate options. Many of our
  current customers evaluated [Competitor] as well. What they found is that
  our platform offers significantly better [specific differentiator]. Would it
  be helpful if I connected you with a customer who made that exact switch?

### Timing

- **Buyer says:** "This isn't a priority for us right now."
- **Recommended response:** I completely understand. Can I ask what would need
  to change for this to become a priority? The reason I ask is that our
  customers who waited reported the problem costing them approximately $X per
  quarter.

### Authority

- **Buyer says:** "I'd need to get buy-in from several other stakeholders."
- **Recommended response:** That makes sense for a decision of this magnitude.
  Who else would be involved? I'd be happy to prepare tailored materials for
  each stakeholder's perspective - whether that's the technical team, finance,
  or executive sponsor.

Placeholders such as `[Competitor]`, `[specific differentiator]`, and `$X` are
stored deliberately. The rep substitutes the real name or figure; the agent
never fills them in with a guess.
