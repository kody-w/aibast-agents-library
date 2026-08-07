# Mission: deploy this agent to Copilot Studio, end to end

Outcome: the agent below is live in the person's Copilot Studio environment and
has passed its verification questions. Every step here has been executed live;
the friction notes are real failures and their real fixes.

{{STACK_CONTEXT}}

## Step 1 — Machine readiness (fix, don't ask)

Run `pac help`.
- **Not installed** → install it yourself: `dotnet tool install --global Microsoft.PowerApps.CLI.Tool`
  (if `dotnet` is missing on macOS: `brew install dotnet`; on Windows suggest winget `Microsoft.DotNet.SDK.8`).
- **Version below 2.9.3** → `pac install latest`. Versions below 2.9.3 do not have
  the CLI agent-authoring commands this mission uses.

Run `pac auth list`.
- **No profile** → **PERSON**: ask the person to run `pac auth create` in a
  terminal and finish the browser sign-in. This is the one interactive setup
  step in the whole mission. Wait, then re-check.

## Step 2 — Pick the environment (auto-detect, offer override)

Run `pac org list`. Use the row marked `*` (the active environment): take its
Environment ID (a GUID). Tell the person which environment you are deploying to
and continue — they can name a different one if they want.

## Step 3 — Create (or reconnect) the project

Choose a fresh folder, e.g. `~/CopilotStudioAgents/<agent-slug>` (add `-2`,
`-3`… if it exists). Then:

```
pac copilot init \
  --name "<Agent display name>" \
  --publisher-prefix aibast \
  --authoring-mode cli-copilot \
  --project-dir <folder> \
  --environment <ENVIRONMENT-GUID>
```

Friction, seen live:
- **`403 … prvReadbot`** → the person has no security role in that environment.
  Tell them plainly: an admin must give them a role (Environment Maker is
  enough) — or pick another environment from step 2 and retry.
- **`already exists (ID: <guid>)`** → this agent was deployed before. Do not
  fight it: reconnect and update instead —
  `pac copilot clone --bot <guid> --environment <ENVIRONMENT-GUID> --output-dir <folder>`
  (pac creates a subfolder named after the agent; use that as the project).

Done when: the project folder contains `settings.mcs.yml`. Never hand-edit
`.mcs/` — it is CLI-managed state.

## Step 4 — Sync BEFORE editing

```
pac copilot pull --project-dir <folder>
```

Order matters, proven live: pull rewrites `settings.mcs.yml` from the service,
so pulling AFTER you set the instructions silently erases them. Pull first,
edit second.

## Step 5 — Install the components

Download every component file listed in the context block above into the
project at its listed path (create directories as needed). These are public
raw URLs — no auth. Remember to encode `@` as `%40` in the URL path or the
fetch 404s.

## Step 6 — Set the instructions

Download the instructions file (context block above). Open
`<project>/settings.mcs.yml` and set the instructions segment so the file
contains, under the existing `configuration:` → `agentSettings:` keys
(replace `instructions: {}` if present):

```yaml
    instructions:
      segments:
        - kind: StaticSegment
          value: |
            <the FULL instructions text, every line indented to match>
```

Keep every other generated field (schemaName, model, template, language)
exactly as pac wrote it. Verify by re-reading the file: the rules text must
actually be present under `value:` — an empty `instructions: {}` remaining in
the file means this step did not happen.

## Step 7 — Push

```
pac copilot push --project-dir <folder>
```

Friction, seen live:
- **`Remote changes conflict with local changes`** → run
  `pac copilot pull --project-dir <folder>`, then REDO step 6 (pull just reset
  the instructions — this is the clobber warned about in step 4), then push
  again.
- **`No local changes detected`** when you expected changes → your edits did
  not land (usually step 6). Re-verify the file, fix, push.

Done when: push reports N change(s) pushed.

## Step 8 — Publish (the go-live moment)

**PERSON**: confirm with the person before this step — publishing makes the
agent live for everyone it is shared with. On their yes:

Read `schemaName:` from `<project>/settings.mcs.yml`, then:

```
pac copilot publish --bot <schemaName> --environment <ENVIRONMENT-GUID>
```

Friction, seen live:
- **CLI crashes with `CopilotPublishStatus` / `ArgumentException`** → known
  pac 2.9.3 defect: the publish JOB was submitted and lands anyway; only the
  status read crashed. Verify in the portal (next step) instead of retrying
  in a loop.

## Step 9 — Verify, honestly

Open `https://copilotstudio.microsoft.com/environments/<ENVIRONMENT-GUID>/bots`,
confirm the agent shows a recent **Last published** time, open it, and check
the Build page shows the skills and knowledge from step 5 and the instructions
from step 6 (an empty instructions pane = step 6 failed — go back).

Then put the verification questions from the context block to the agent in the
Test pane and compare each answer against its expected result. Report each as
pass or fail with what the agent actually said. If the gate questions fail,
the mission is NOT complete — say so and fix before anyone demos this.
