# Mission: set this machine up for AIBAST agent work

Outcome: everything a library build needs is installed and checked — the
person can immediately say "deploy <agent> to Copilot Studio" or "install
<agent> locally" and it will just run.

## Step 1 — The brainstem (the engine you are running in)

If you are reading this inside a brainstem loop, it is already installed.
Otherwise the person installs it with the one-liner from
https://github.com/{{REPO}} (README, "Install"): it clones the repo, creates
the venv, and starts the server on port 7071. Verify:
`curl -s localhost:7071/health` returns status ok or unauthenticated.

## Step 2 — Power Platform CLI (deploys need it)

Run `pac help`.
- Not installed → `dotnet tool install --global Microsoft.PowerApps.CLI.Tool`
  (macOS without dotnet: `brew install dotnet` first).
- Below version 2.9.3 → `pac install latest`. 2.9.3 is the floor for CLI
  agent authoring.

## Step 3 — One-time sign-in

Run `pac auth list`. If empty → **PERSON**: the person runs `pac auth create`
in a terminal and completes the browser sign-in with their work account. This
is the single interactive step; everything after it is automated. Verify with
`pac auth list` and `pac org list` (their environments should list).

## Step 4 — Optional: the Copilot Studio plugin (for advanced authoring)

For makers who also use Claude Code or Copilot CLI directly, Microsoft's
Copilot Studio plugin adds agent authoring, migration, and live chat testing:

```
/plugin marketplace add microsoft/copilot-studio-plugin
/plugin install mcs-assistant@copilot-studio-plugin
```

Its live-chat command needs a one-time Entra app registration (public client,
delegated `CopilotStudio.Copilots.Invoke` on the Power Platform API) — the
plugin walks through it on first use. Not required for deploying library
agents.

## Step 5 — Confirm the library is reachable

Fetch {{RAW}}/registry.json — it should return JSON with the agent catalog.
This is the public source everything else pulls from; no token, no VPN.

Report the checklist to the person with a ✅/❌ per step and what, if
anything, remains for them to do.
