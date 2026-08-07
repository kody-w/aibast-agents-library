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
assert "MUTATION" not in r3, "mutation appended without being asked"
print("mutation_layer_test: PASS")
