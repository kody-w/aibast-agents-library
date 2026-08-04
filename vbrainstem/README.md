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
- **Upvotes and install tallies land on this repository's Discussions** — the
  same threads the [metrics dashboard](../metrics.html) reads, so browser
  usage counts in the library's public numbers.

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
