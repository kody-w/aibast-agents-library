# RAPP Brainstem Frontier

See [`GOLDEN_PATH.md`](GOLDEN_PATH.md) for the guiding product path:
learn AI, teach it back immediately as a working capability, and keep that
portable skill for life.

This opt-in Frontier experience applies the launcher architecture used by Skill Recorder to
RAPP Brainstem:

- chat remains the universal control surface for people and other AIs;
- Frontier composes global and routed single-file agents into an isolated
  worker `AGENTS_PATH`, then invokes them through the unchanged `/chat`;
- the included `BrainstemUiDriver` agent can operate the actual visible
  frontend with an animated cursor, clicks, typing, narration, and waits so the
  user can watch or follow along;
- an Electron desktop window owns the local UI;
- the GitHub Copilot CLI is bundled through `@github/copilot-sdk` and connected
  over stdio with a bounded startup timeout;
- the launcher starts unchanged Brainstem workers on loopback ports with
  content-addressed, hardlinked agent compositions;
- app shutdown disposes the bundled Copilot client and every worker it owns.

Frontier and the regular installer use the same global runtime:

```text
~/.brainstem/
|- src/rapp_brainstem/   shared server, agents, soul, auth, and memories
|- venv/                 shared Python environment
`- beta-launcher/
   |- routing/           RAPPID, stack, egg, object, and composition state
   |- recordings/        captured teaching demos
   `- src/               Frontier-only Electron, Copilot CLI, and launcher source
```

The regular installer may keep serving `http://localhost:7071`. Frontier uses
isolated loopback workers and embeds their unchanged Brainstem UI between a
live Explorer and GitHub Copilot Brain Surgeon.

## What it is for

Use Frontier as a builder-operated rapid proof harness for the customer
question: **"Can AI do this?"**

It is also the teaching path: learn the AI pattern on real work, have Copilot
turn that learning into an agent immediately, inspect and test it visibly, and
keep the resulting skill as a portable RAPP capability.

It is best when the use case is still a transcript, problem statement,
screenshot, sample document, or expected outcome. GitHub Copilot builds and
repairs the code; Brainstem is the visible test UI where you hot-load agents,
inspect tool calls, validate memory, and prove the behavior. A successful proof
produces portable single-file agents, evidence, known production gaps, and a
clear recommendation for Scout, Copilot Studio, Foundry, custom code, or no-go.

Do not position the local prototype as production. Use synthetic or approved
data, validate with a human, and move real identity, connectors, governance,
telemetry, and scale into the selected production platform.

The launcher shows this guidance on first run and keeps it available through
the **What is this?** button.

The product direction is to take the user out of repetitive execution without
taking them out of understanding: the user drives by chatting, the Brainstem
delegates to agents, and visible UI actions show exactly what is being done.

## Brain Surgeon: GitHub Copilot without requiring VS Code

Frontier ports the proven vBrainstem Brain Surgeon pattern into the desktop
client. Open the **GitHub Copilot** tab on the right edge to reveal the full
Copilot coding-agent loop side-by-side with the live Brainstem.

This is not a second Brainstem or a simplified chatbot. It is GitHub Copilot
Agent mode with its normal file, shell, search, edit, and test loop. Frontier
adds RAPP-specific tools so that loop can:

- visibly type into the same Brainstem composer a person uses;
- submit through the same `/chat` and `/chat/stream` contract;
- inspect the same replies and `agent_logs`;
- author a single-file agent and compose it into exactly one isolated chat worker;
- remove that temporary source and bytecode when the request closes;
- operate the visible interface with an animated cursor;
- attach screenshots and recorded WebM demonstrations.

The nontechnical golden path is therefore one window: tell the Brain Surgeon
what outcome you need, watch it build or route the capability, and see the
Brainstem execute it. VS Code and GitHub CLI remain available for experts, but
they are no longer prerequisites for using GitHub Copilot as the Brainstem's
builder.

If the user gets stuck, another AI can visibly take over the same Brain Surgeon
or Brainstem chat, perform the next steps in Frontier, show the evidence,
and hand control back without losing context.

External AIs and CLIs can enter the same visible loop:

```bash
brainstem-surgeon "Build and test the capability I need"
brainstem-walkthrough
```

That command opens the right-hand panel if needed, visibly types the task into
GitHub Copilot, and waits for its answer. The recursive control path is:

```text
external AI / CLI
  -> visible Brain Surgeon chat
  -> full GitHub Copilot coding-agent loop
  -> visible Brainstem chat (/chat)
  -> one-turn routed composition and result
```

`brainstem-walkthrough` runs the complete autonomous five-minute teaching path:
it opens the Explorer, guides Brain Surgeon through identity and stack
orientation, records the shell, hotloads a one-turn teaching agent through the
center Brainstem chat, verifies cleanup, checks GitHub updates, captures the
evidence, and reports the saved WebM and screenshot. Every run is fully decoded,
sampled at five points, and added to
`~/.brainstem/beta-launcher/walkthroughs/index.html`, including failed and
historical recordings, so improvements can be watched in order.

To decode and add recordings created before this evidence index existed:

```bash
npm run walkthrough:ingest
```

## Show Mode — describe it, or show it

Some customers can describe their process; some would rather show it. **Show
Mode** (Frontier-tagged) turns a live recording, a video, a set of screenshots,
or a transcript into a single-file agent you hotload and **test in your own
Brainstem first**, then promote into Copilot Studio, Scout, Cowork, Foundry, or
custom Azure code — the tested bytes are the bytes that ship.

Open it from the **Show Mode: click-through preview** pill in the Brain Surgeon,
from the first-run intro card, or as a shareable page at `/beta/show-mode.html`.
The step-by-step walkthrough with screenshots is in
[`docs/show-mode/`](docs/show-mode/README.md).

An AI can drive the whole loop for a user through chat and let them watch. Ask
the Brain Surgeon (or the center Brainstem) to "use AI force mode" to operate the
Brainstem for you, or to `show_mode_click_through` — while it drives, the window
edges glow and a tag reads *AI force mode · an AI is driving this Brainstem —
you're watching*, so it is always clear an AI, not a hand, is at the controls.
`npm run show-mode:capture` walks the preview and saves one screenshot per step
(add `-- --force` to light force mode for a live demo).

## Install

The dedicated Download Center-style GitHub Pages installer is published at
`/beta/`. It provides platform bootstrap downloads, copyable install commands,
release metadata, requirements, and installation guidance. The page resolves
the latest `brainstem-beta-v*` release from the fork serving it, so staging and
production remain separate. If that release includes packaged `.exe` or `.dmg`
assets, the page lists them automatically ahead of the source bootstrap.

### Windows 11 x64

Run this in PowerShell:

```powershell
irm https://microsoft.github.io/aibast-agents-library/beta/frontier.ps1 | iex
```

Published Windows binaries are x64, per-user NSIS installers. They launch
Frontier without elevation; first launch provisions the shared Brainstem under
the user's `BRAINSTEM_HOME`, then waits for compatible backend and agent-load
evidence before showing chat as ready.

Windows ARM64 is not claimed as a native target. The source bootstrap fails
with guidance rather than mixing ARM64 Node with x64-only Electron or media
binaries. Use an x64 Windows 11 device or x64 virtual machine for this preview.

### macOS or Linux

```bash
curl -fsSL https://microsoft.github.io/aibast-agents-library/beta/frontier.sh | bash
```

The same one-liner is used every time: first install, update, repair, and launch.
The bootstrap resolves the latest published Frontier release to its immutable
40-character commit before running the platform installer.

After the first install, launch **RAPP Brainstem Frontier** from Applications,
Launchpad, the Linux app menu, the Windows Desktop/Start Menu, or run:

```bash
brainstem-frontier
```

### Packaged app first run

A published `.dmg` or `.exe` no longer assumes `~/.brainstem` already exists.
The package carries the root Brainstem installers plus a manifest that binds
their SHA-256 hashes, repository, and runtime source to the package's full
40-character release commit. On launch, Frontier:

1. verifies the existing `BRAINSTEM_HOME` source, Python environment, and
   required imports without changing a ready installation;
2. automatically provisions only when the entire target `BRAINSTEM_HOME` is
   absent; an old, partial, dirty, or incompatible home fails closed with manual
   repair guidance and is never reset;
3. runs the existing root installer in `--runtime-only --no-launch` mode against
   the package's immutable commit inside a unique versioned sibling stage;
4. verifies the staged source, fresh venv, Python 3.11+, required memory-agent
   files, soul, dependencies, and `brainstem.py` syntax;
5. atomically creates a no-replace directory link from the still-absent target
   to that verified stage (a Windows junction on Windows), then requires
   compatible `/health` evidence before starting the rest of Frontier.

Failures remove the stage, preserve the prior target, remain visible, and name
the sanitized installer log plus the next action. Frontier never asks the
installer to authenticate. Launcher and worker log boundaries redact known
token, secret, authorization-header, credential-URL, quoted-assignment, and
nested JSON fields; route response/agent-log previews use the same sanitizer.
Raw child output is not claimed safe or written directly.

Compatibility is also fail-closed: Frontier requires Brainstem 0.6.16 or newer,
a present soul, loaded-agent evidence, the routed `ContextMemory` and
`ManageMemory` agents, and an empty quarantine/load-error list before it shows
chat as ready. `BRAINSTEM_HOME` remains authoritative even when it differs from
`HOME` or `USERPROFILE`.

The packaged GitHub Copilot platform executable is resolved from
`app.asar.unpacked` (never the logical `app.asar` path passed to `spawn`).
Source and Brainstem fingerprints are computed only after the window exists and
runtime provisioning succeeds, so a missing clean-machine runtime cannot crash
during module evaluation.

## Check for updates

Open the three-dot **RAPP Brainstem Frontier** dropdown in the Brainstem toolbar and
choose **Check for updates**. The native application menu also exposes
**Check for Updates...**. The launcher compares its installed commit with the
latest commit on the configured GitHub branch (`main` by default).

When an update is available, **Update and Restart** runs the existing Frontier
installer against that exact commit. This refreshes both the desktop launcher
and the shared Brainstem source, runs the Frontier checks, and reopens the app.
Tracked local changes in the Frontier checkout block the update instead of being
discarded.

That updater applies only to source-managed Frontier checkouts. A packaged app
does not try to rewrite `app.asar`; its update panel fails closed with a link to
download and install a newer signed package. Replacing the app preserves the
existing `BRAINSTEM_HOME`.

## Drive Frontier through chat

The source checkout includes `scripts/brainstem_ui_driver_agent.py`. The
`drive:e2e` harness sends that source through the visible GitHub Copilot Brain
Surgeon chat. Brain Surgeon supplies it to `delegate_to_brainstem` as a one-turn
ephemeral agent, and `BetaRouteManager` materializes it beside the selected
RAPPID stack without changing the shared Brainstem kernel. The agent does not
expose arbitrary JavaScript; it uses a token-authenticated loopback bridge with
bounded actions such as inspect, click, type, press, wait, read, and screenshot.

Run the update-control E2E demonstration while Frontier is open:

```bash
npm run drive:e2e
```

The harness visibly asks Brain Surgeon to hot-load the driver, type its
instruction into the Brainstem chat, send it through `/chat`, and watch the
agent animate the real dropdown. The temporary routed worker records the
window, attaches the playable WebM plus a final screenshot to chat, then is
stopped and removed in a guaranteed cleanup path.

For any workflow, the agent can use the same three-stage pattern:

1. `start_recording`
2. `run` the visible clicks, typing, waits, and reads
3. `stop_recording`

The recording is saved under `~/.brainstem/beta-launcher/recordings/` and shown
with playback controls in the agent activity attached to the chat response.

## Download boundary

The global runtime clone uses a shallow partial sparse checkout restricted to
`rapp_brainstem/`. Frontier uses a second shallow partial sparse checkout
restricted to `beta/` plus the small `tools/rapp1` conformance fixture needed
by its release tests. Neither checkout downloads `solutions/`.

Both installers default to:

```text
https://github.com/microsoft/aibast-agents-library.git
```

Binary packaging runs `npm run prepare:bootstrap` before electron-builder. The
preparation step refuses dirty tracked source, records the exact checkout HEAD,
and copies the matching root installers into the packaged resources. Release
mode is the default and requires
`https://github.com/microsoft/aibast-agents-library.git`. A fork build must set
`BRAINSTEM_BETA_PACKAGE_MODE=development` and carries the distinct
`rapp-brainstem-frontier-development` provenance identity. Runtime environment
variables cannot replace packaged provenance.

The `BRAINSTEM_BETA_REPO_URL` and `BRAINSTEM_BETA_REF` environment variables
exist only for fork staging and release-candidate verification.

Release procedure and source-only publication rules are documented in
[`RELEASING.md`](RELEASING.md).

## Frontier limitations

- This is an unsigned source-built Frontier preview, not an officially supported Microsoft
  desktop application. Managed-device controls may block Electron or downloaded
  source.
- Initial source installation still needs network access and may open a console
  while dependencies are assembled. Normal chat launch uses the desktop app and
  does not require a terminal.
- Brainstem's in-app GitHub device-code flow remains the authentication fallback.
  The launcher never stores GitHub or Copilot tokens itself.

## Uninstall the launcher

Removing Frontier does not remove the shared Brainstem or user data.

The Windows NSIS uninstaller is per-user and intentionally leaves Electron
profile data and `%USERPROFILE%\.brainstem` intact. Remove those separately
only when you explicitly want to delete agents, memories, recordings, and
authentication state.

```bash
rm -rf ~/.brainstem/beta-launcher
rm -f ~/.local/bin/brainstem-frontier ~/.local/bin/brainstem-beta
rm -rf "$HOME/Applications/RAPP Brainstem Frontier.app"
rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/applications/rapp-brainstem-frontier.desktop"
```

On Windows, remove the two **RAPP Brainstem Frontier** shortcuts and delete:

```text
%USERPROFILE%\.brainstem\beta-launcher
```
