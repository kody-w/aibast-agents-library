# Mission: remove the agent I deployed

Outcome: the agent below no longer exists in the person's environment, and
they know exactly what was deleted. Teardown is deliberately boring.

{{STACK_CONTEXT}}

## Steps

1. Confirm which agent and which environment — repeat both back before
   touching anything. **PERSON**: deletion is permanent; get an explicit yes
   after naming the agent.
2. In the Copilot Studio portal (Agents list → the agent → … menu → Delete)
   — this is the supported path and takes seconds. There is no pac delete
   verb; do not improvise one.
3. The local project folder (~/CopilotStudioAgents/…) is the person's copy of
   versioned YAML — leave it unless they ask; it is what makes redeploying
   later a five-minute job, and it costs nothing.
4. Verify honestly: reload the Agents list and confirm the agent is gone.
   Report what was deleted and what was kept.
