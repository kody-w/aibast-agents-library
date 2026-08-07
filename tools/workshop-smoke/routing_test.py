#!/usr/bin/env python3
"""Every library stack must route from its own display name.

The twin picks a stack from what a person says; the workshop shows them the
display/advertised name. If those two disagree for any stack, a seller
deploys the wrong agent — which happened three times during the first build
(win-loss, Proposal Copilot, Customer 360). This test walks the whole
library so that class of defect cannot come back.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "agents/@aibast-agents-library/templates"))
sys.path.insert(0, str(ROOT / "agents/@aibast-agents-library/general_stacks/sales_specialist_twin_stack"))
from sales_specialist_twin_agent import SalesSpecialistTwinAgent  # noqa: E402

agent = SalesSpecialistTwinAgent()
stacks = {}
for man in ROOT.glob("agents/@aibast-agents-library/*_stacks/*/copilot_studio/manifest.json"):
    d = json.loads(man.read_text())
    stacks[d["stack"]] = (d["display_name"], man.parent.parent.name)

failures = []
for slug, (display, directory) in sorted(stacks.items()):
    ask = display.replace(" Agent", "")
    out = agent.perform(operation="mission",
                        request=f"deploy the {ask} agent to copilot studio")
    if "Scaffold base URL:**" not in out:
        failures.append(f"{slug}: no scaffold context for '{ask}'")
        continue
    url = out.split("Scaffold base URL:**")[1].split()[0]
    got = url.split("/")[-2]
    if got != directory:
        failures.append(f"{slug}: '{ask}' routed to {got}, expected {directory}")

print(f"routing_test: {len(stacks) - len(failures)}/{len(stacks)} stacks route from their own name")
for f in failures:
    print("  FAIL", f)
sys.exit(1 if failures else 0)
