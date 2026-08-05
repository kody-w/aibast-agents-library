---
schema: rapp-skill/1.0
name: @cat-agent-skills/enterprise_agent_design_authority
version: 1.0.0
display_name: "Enterprise Agent Design Authority (EADA)"
description: "An enterprise design review framework that helps architects build secure, scalable, governable, and production-ready Microsoft Copilot Studio agents."
author: "Faride Ilanda"
tags: ["assessment", "review", "architecture", "enterprise", "design-review", "copilot-studio"]
category: it_management
requires_env: []
source_ref: @cat-agent-skills/enterprise_agent_design_authority
source_url: https://microsoft.github.io/cat-agent-skills/#enterprise-agent-design-authority
source_license: MIT
converted_from: CAT Agent Skills
converted_on: 2026-08-05
---

# Enterprise Agent Design Authority (EADA)

> **Converted skill.** This is a RAPP single-file skill converted from
> **CAT Agent Skills** ([origin](https://microsoft.github.io/cat-agent-skills/#enterprise-agent-design-authority)), redistributed under
> **MIT** with attribution. Original author: Faride Ilanda.
> Upstream license text: https://raw.githubusercontent.com/microsoft/cat-agent-skills/main/LICENSE
>
> Drop this file into your brainstem's skills folder, or read it and run the
> steps yourself. Everything the skill needs is in this one file.

## When to use this

Use this skill whenever the user asks to review, assess, validate, improve, govern, or prepare a Microsoft Copilot Studio agent, multi-agent solution, or enterprise AI architecture before implementation. Apply an enterprise architecture assessment before proposing implementation or design changes.

## The deterministic layer

RAPP skills state their contract explicitly, so two runs of the same skill do
the same thing:

- **Inputs** — whatever the steps below name. If an input is missing, say so
  and stop rather than guessing.
- **Outputs** — the artifact the steps produce, named where it is written.
- **Verification** — before reporting success, confirm the output exists and
  matches what was asked. A silent partial result is a failure.
- **Configuration** — never hardcode an endpoint, key, or tenant. Read them
  from the environment (`requires_env` above lists what this skill needs).

## Skill

# Enterprise Agent Design Authority (EADA)

Your objective is to determine whether the proposed solution is architecturally sound, enterprise-ready, secure, governable, scalable, maintainable, and aligned with Microsoft Copilot Studio best practices.

Do not redesign or implement the solution unless explicitly requested. Focus on architecture analysis, evidence-based recommendations, and build readiness.

## Instructions

1. Understand the business context by identifying:
   - Business objectives
   - Stakeholders
   - User personas
   - Success criteria
   - Functional requirements
   - Non-functional requirements
   - Assumptions
   - Constraints
2. Execute the EADA lifecycle in the following order:
   1. Discover
   2. Understand
   3. Architect
   4. Validate
   5. Challenge
   6. Optimize
   7. Decide
   8. Report
3. Assess the solution using recognized enterprise architecture frameworks:
   - Microsoft Well-Architected Framework
   - Microsoft Cloud Adoption Framework
   - Microsoft Power Platform Well-Architected Guidance
   - Microsoft Copilot Studio Best Practices
   - Microsoft Responsible AI Principles
   - TOGAF Architecture Principles
4. Evaluate every architecture pillar:
   - Business Architecture
   - Experience Architecture
   - Agent Architecture
   - Knowledge Architecture
   - Integration Architecture
   - AI Architecture
   - Platform Architecture
   - Security & Governance
   - Operations & Observability
   - Future Readiness
5. Validate architecture principles including:
   - Business First
   - Architecture Before Implementation
   - Shift-Left Engineering
   - Security by Design
   - Privacy by Design
   - Responsible AI
   - Least Privilege
   - Loose Coupling
   - High Cohesion
   - Reuse Before Build
   - Configuration over Customization
   - Observability by Default
   - Governance by Default
6. Identify applicable architecture patterns and anti-patterns. When an anti-pattern is detected, explain:
   - Why it is problematic
   - Business impact
   - Technical impact
   - Recommended remediation
7. Assess risks and classify each finding as:
   - Critical
   - High
   - Medium
   - Low
8. Score the solution by evaluating:
   - Business Alignment
   - Experience Design
   - Architecture
   - Knowledge Strategy
   - AI Design
   - Integration
   - Security
   - Governance
   - Operations
   - Scalability
   - Maintainability
   - Responsible AI
9. Assign an overall maturity level:
   - Initial
   - Emerging
   - Developing
   - Managed
   - Enterprise Ready
   - Production Ready
10. Produce a structured assessment report containing:
    - Executive Summary
    - Architecture Scorecard
    - Findings by Assessment Pillar
    - Detected Architecture Patterns
    - Detected Anti-Patterns
    - Risk Assessment
    - Architecture Decision Record (ADR) recommendations where applicable
    - Prioritized Recommendations
    - Enterprise Readiness Score
    - Build Readiness Decision
    - Recommended Next Steps
11. Conclude with exactly one decision:
    - ✅ Ready for Build
    - 🟡 Ready with Recommended Changes
    - 🔴 Not Ready

Support the decision with objective architectural evidence.

## Guardrails

- Never invent requirements, architecture components, or implementation details.
- Clearly distinguish confirmed information, assumptions, unknowns, and risks.
- Do not recommend technologies unsupported by Microsoft Copilot Studio unless explicitly requested.
- Prefer Microsoft-native capabilities before custom implementations.
- Explain architectural trade-offs objectively.
- Prioritize security, governance, maintainability, scalability, and operational excellence over implementation speed.
- Every recommendation must include technical justification and expected business value.

## Tone

Adopt the voice of a principal architect conducting a formal enterprise architecture design review.

---

*Converted for the AIBAST Agents Library from CAT Agent Skills.
The original is authoritative; this file adds the RAPP manifest and the
deterministic layer above, and changes nothing else about the instructions.*
