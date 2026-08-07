#!/bin/bash
# One workshop attendee, simulated: twin mission -> Copilot CLI executes.
set -u
SLUG="$1"; NAME="$2"
S=/private/tmp/claude-501/-Users-kodywildfeuer-Documents-GitHub-aibast-agents-library/7eb12ce0-32d0-420f-b8c4-eb9929a298e0/scratchpad
R=/Users/kodywildfeuer/Documents/GitHub/aibast-agents-library
PAYLOAD=$(cd "$R" && AIBAST_REPO=kody-w/aibast-agents-library AIBAST_REF=feature/field-service-dispatch-copilot-studio python3 -c "
import sys
sys.path.insert(0,'agents/@aibast-agents-library/templates')
sys.path.insert(0,'agents/@aibast-agents-library/general_stacks/sales_specialist_twin_stack')
from sales_specialist_twin_agent import SalesSpecialistTwinAgent
print(SalesSpecialistTwinAgent().perform(operation='mission', request='deploy the $NAME agent to copilot studio'))")
if ! echo "$PAYLOAD" | grep -q "MISSION BRIEFING"; then
  echo "MISSION RESULT: FAILURE — twin returned no briefing for $SLUG"; exit 1
fi
# Guard: the briefing must be about the agent we asked for (live defect: a
# fuzzy-match miss once routed win-loss to the deal-progression suite).
SLUG_DIR=$(echo "$SLUG" | tr '-' '_')
if ! echo "$PAYLOAD" | grep -q "Scaffold base URL"; then
  echo "MISSION RESULT: FAILURE — no scaffold context for $SLUG"; exit 1
fi
if ! echo "$PAYLOAD" | grep "Scaffold base URL" | grep -q "$SLUG_DIR"; then
  echo "MISSION RESULT: FAILURE — briefing routed to the wrong stack for $SLUG"; exit 1
fi
DIRECTIVE="Operator directives for this run (they override PERSON pauses — the operator has pre-approved):
- Target environment GUID: 35fb6ec1-10b0-e529-8c78-2c48a93fd517 (skip auto-detection).
- Use project folder ~/CopilotStudioAgents/batch/$SLUG (add -2 suffix if it exists).
- Publish is PRE-CONFIRMED by the operator: do not pause before publishing.
- pac auth already exists on this machine; never run pac auth create.
- Runtime chat verification is known-blocked by a Copilot Studio service outage; SKIP opening any browser or test pane. The mission is complete at published-with-components.
- Your FINAL line of output must be exactly: MISSION RESULT: SUCCESS — <schemaName> published  (or)  MISSION RESULT: FAILURE — <one-line reason>."
copilot -p "$DIRECTIVE

$PAYLOAD" --allow-all 2>&1
