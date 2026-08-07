#!/bin/bash
# Hotload the twin into the running brainstem and prove /chat reaches it.
set -eu
REPO="${AIBAST_REPO:-microsoft/aibast-agents-library}"; REF="${AIBAST_REF:-main}"
curl -fsSL -o ~/.brainstem/src/rapp_brainstem/agents/sales_specialist_twin_agent.py \
  "https://raw.githubusercontent.com/$REPO/$REF/agents/%40aibast-agents-library/general_stacks/sales_specialist_twin_stack/sales_specialist_twin_agent.py"
RESP=$(curl -s -X POST localhost:7071/chat -H "Content-Type: application/json" \
  -d '{"user_input":"What missions can the sales specialist twin run?"}')
echo "$RESP" | python3 -c "
import json,sys
r = json.load(sys.stdin).get('response','')
assert 'Deploy a library agent' in r or 'Copilot Studio' in r, 'twin not reached: '+r[:200]
print('hotload_chat_test: PASS')"
