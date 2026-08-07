#!/usr/bin/env python3
"""Twin payload smoke: mission matching, mirror chain, context assembly."""
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "agents/@aibast-agents-library/templates"))
sys.path.insert(0, str(ROOT / "agents/@aibast-agents-library/general_stacks/sales_specialist_twin_stack"))
from sales_specialist_twin_agent import SalesSpecialistTwinAgent

a = SalesSpecialistTwinAgent()
r = a.perform(operation="mission", request="deploy the field service dispatch agent to copilot studio")
assert "MISSION BRIEFING" in r, "no harness header"
assert "Scaffold base URL" in r, "no stack context injected"
assert "fsd101" in r, "component list missing"
assert "Marcus Thompson" in r, "verification facts missing"
assert "sales-specialist-twin" not in r.split("**Agent:**")[1][:120], "twin matched itself"
m = a.perform(operation="list_missions")
assert "Deploy a library agent" in m
print("twin_payload_test: PASS")

# mutation layer: directive appended only when a system of record is named
r2 = a.perform(operation="mission",
               request="deploy the deal progression agent to copilot studio for our salesforce org")
assert "MUTATION — adapt for Salesforce" in r2, "salesforce mutation missing"
r3 = a.perform(operation="mission",
               request="deploy the deal progression agent to copilot studio")
assert "MUTATION — adapt for" not in r3, "mutation appended without being asked"
print("mutation_layer_test: PASS")

# architecture mission: WAF review with concessions, stack-adapted
r4 = a.perform(operation="mission",
               request="give me the architecture review for the field service dispatch agent")
assert "Well-Architected" in r4 and "Concede" in r4 and "Field Service" in r4, "architecture mission broken"
print("architecture_mission_test: PASS")

# matcher: exact-name stacks beat rich multi-agent haystacks (live defect)
import json as _json
r5 = a.perform(operation="mission", request="deploy the Win/Loss Analysis agent to copilot studio")
assert "win_loss" in r5.split("**Scaffold base URL:**")[1][:200], "win-loss matched wrong stack"
r6 = a.perform(operation="mission", request="deploy the deal progression agent to copilot studio")
assert "deal_progression" in r6.split("**Scaffold base URL:**")[1][:200], "deal-progression broken"
print("matcher_priority_test: PASS")

# advertised names are what sellers see on the workshop card — they must route
for ask, want in [("deploy the Expansion Opportunity agent to copilot studio", "cross_selling"),
                  ("deploy the Account Research agent to copilot studio", "account_intelligence"),
                  ("deploy the Mortgage Origination agent to copilot studio", "loan_origination")]:
    rr = a.perform(operation="mission", request=ask)
    assert want in rr.split("Scaffold base URL:**")[1][:220], f"advertised name misrouted: {ask}"
print("advertised_alias_test: PASS")

# "copilot" must not be stripped as a mission word — it distinguishes stacks
r7 = a.perform(operation="mission", request="deploy the Proposal Copilot agent to copilot studio")
assert "proposal_copilot" in r7.split("Scaffold base URL:**")[1][:220], "Proposal Copilot collided"
r8 = a.perform(operation="mission", request="deploy the Proposal Creation agent to copilot studio")
assert "proposal_generation" in r8.split("Scaffold base URL:**")[1][:220], "Proposal Creation misrouted"
print("phrase_strip_test: PASS")
