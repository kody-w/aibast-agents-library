# Mission: install this library agent into the local brainstem

Outcome: the agent below is running in the person's local brainstem and
answered its first request. No restart is needed — the brainstem discovers
agents from disk on every message.

{{STACK_CONTEXT}}

## Step 1 — Find the brainstem's agents folder

The running brainstem loads agents from its `agents/` directory. Locate it:
the standard install is `~/.brainstem/src/rapp_brainstem/agents/`; if the
`AGENTS_PATH` environment variable is set in `rapp_brainstem/.env`, that wins.
If no brainstem is installed at all, switch to the "Set up this machine"
mission first.

## Step 2 — Download the agent file

Download the agent.py from its raw URL in the context block (encode `@` as
`%40` in the path) into the agents folder, keeping its filename ending in
`_agent.py` — discovery only matches `*_agent.py` files in the flat directory.

## Step 3 — Prove it, honestly

Send the brainstem a request that exercises the new agent (POST /chat on
localhost:7071, or just ask in this conversation — the reply arrives in the
`response` field). Confirm the answer clearly comes from the new agent's data,
then show the person that first real answer. If the agent needs environment
variables (`requires_env` in its manifest), list them and where to set them
(`rapp_brainstem/.env`) instead of pretending it worked.
