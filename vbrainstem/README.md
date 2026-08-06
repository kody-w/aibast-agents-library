# vBrainstem — the brainstem, running 100% in your browser

Open [`index.html`](https://microsoft.github.io/aibast-agents-library/vbrainstem/)
and you are running a RAPP brainstem — real CPython via
[Pyodide](https://pyodide.org) in a Web Worker, zero install, no admin rights.
Same engine, same chat UI, same agent loop as the on-device brainstem
(`rapp_brainstem/`), with agents, `soul.md` and memories persisted to
IndexedDB so they survive reloads.

This is the enterprise-hosted edition of the RAPP vBrainstem (engine v0.6.16).
What's different here:

- **The agent library is this repository's static API.** The in-app browser
  panel, `rapp.agents()` console listing, and one-click agent install all read
  `registry.json` and raw agent files from
  `microsoft/aibast-agents-library` (with a jsDelivr CDN mirror as fallback) —
  not the public RAR registry. Install integrity still verifies the SHA-256 of
  the downloaded bytes against the library catalog.
- **Upvotes, install tallies and run tallies land on this repository's
  Discussions** — the same threads the [metrics dashboard](../metrics.html)
  reads, so browser usage counts in the library's public numbers.
- **The theme is the site's theme.** The page reads the AIBAST tokens defined
  at the top of `index.html`; light is the default because the rest of the
  site is light, and the toggle swaps the token set. There is no second
  stylesheet to keep in sync.

## What the numbers mean

This is a public interactive demo, so loading and running a library agent here
counts the same way it counts anywhere else — and by exactly the mechanism the
rest of the library already uses (`scripts/discussion_ratings.py`). GitHub
Discussions is the backend; there is no server and there must not be one.

| Number | Recorded as | Reads as |
|---|---|---|
| **↓ installs** | 👍 on the thread's `<!-- aibast:download-tally -->` comment | unique GitHub accounts that loaded this agent's `agent.py` |
| **▷ runs** | 👍 on `<!-- aibast:vbrainstem-run-tally -->` | unique GitHub accounts that have actually executed it in this browser brainstem |
| **▲ upvotes** | 👍 on the discussion itself | unique GitHub accounts that liked it |

One reaction per account, so every count is *people*, never clicks — running an
agent fifty times is still one. **A signed-out visitor is never counted**: a web
page has no credential to react with and must not pretend to. Signed in, this
page adds the reaction for you; signed out, it hands you a link straight to the
tally comment so you can add it yourself. Every number here is therefore a
floor — real, and smaller than reality.

Counts come from published snapshots (`state/discussion_ratings.json`,
`state/vbrainstem_usage.json`), so they move when the library rebuilds, not
instantly. The run tally is owned by `scripts/vbrainstem_usage.py`:

```bash
GITHUB_TOKEN=... python3 scripts/vbrainstem_usage.py tally   # provision run tallies
GITHUB_TOKEN=... python3 scripts/vbrainstem_usage.py fetch   # snapshot installs + runs
```

Until `tally` has run, agents have no run tally comment and the page shows no
run number for them rather than a zero it cannot stand behind.

## Files

| File | Role |
|------|------|
| `index.html` | The brainstem UI + boot block (open this) |
| `vbrainstem-boot.js` | Patches `window.fetch` so brainstem routes hit the worker |
| `vbrainstem-worker.js` | Web Worker hosting Pyodide + the engine |
| `brainstem_web.py` | Route-for-route port of `rapp_brainstem/brainstem.py` |
| `local_storage.py` | Storage shim (memory persistence) |
| `agents/` | Seed agents (basic, context memory, manage memory) |
| `soul.md` | Default personality — edit in-app, survives reloads |
| `burrow-tether.js`, `surgeon.js`, `pair-crypto.js` | Optional device-pairing layer |

## Disclaimer

Public preview, provided "AS IS" — see the repository
[DISCLAIMER](../DISCLAIMER.md). AI outputs require human review.

## Auth

GitHub device-code sign-in is brokered by a CORS proxy, because github.com
sends no CORS headers for the device-code endpoints. The Copilot token
exchange and chat completions are attempted **direct** to GitHub first, and
**fall back to that same proxy — sending your GitHub token in the request —
when the direct call is unreachable or rejected.**

The default proxy (`https://rapp-auth.kwildfeuer.workers.dev`) is operated by
the upstream RAPP maintainer, not by Microsoft. Point `VB_AUTH_WORKER` at a
proxy you control to keep the token inside your own trust boundary; a
Microsoft-operated default is a tracked pre-GA action (`rapp/ALIGNMENT.md`).
Your conversations, agents and memories stay on your device.
