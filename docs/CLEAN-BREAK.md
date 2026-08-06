# Clean break — link audit dispositions (v1 gate)

Full-repo scan (378 files, 742 unique external URLs, 39 internal links) on
2026-08-04, enforced continuously by test section **T-CLEAN**. The rule:
this repository points at itself; references into the personal kody-w
estate exist only where the succession model requires them.

## Fixed (now self-contained)

- **Tier-2 (Hippocampus)**: installer pages, README, docs → the in-repo
  cloud function app `rapp_cloud/` (one-liners, guide links, footer links).
- **ARM templates** (`azuredeploy.json`, `rapp_cloud/azuredeploy.json`): the
  generated setup scripts clone THIS repository and run from `rapp_cloud/`
  (were: kody-w/CommunityRAPP, kody-w/EntraCopilotAgent365 — the latter a
  404, i.e. deploys were broken).
- **`rapp_cloud` installers**: self-source from this repo (were: 404 raw URLs
  on kody-w/m365-agents-for-python).
- **`rapp_cloud/agents/agent_library_manager.py`**: discovers/installs from
  this library's registry (was: a third-party personal repo).
- **Deploy-to-Azure buttons**: this repo's `azuredeploy.json` (were:
  kody-w/rapp-installer).
- **vBrainstem**: tether scripts ported in-repo and repointed to this
  repo's installers; soul/onboarding links in-family; library panel +
  ratings on this repo (zero RAR references).
- **rapp_cloud docs sweep**: every kody-w/CommunityRAPP issues/discussions/
  releases/security link → this repository; dead fork links de-linked.
- **docs pages internal links** → valid targets (GitHub blob URLs where the
  file isn't served as HTML).
- **Generated `state/` + `api/`**: regenerated canonical — zero kody-w
  references (T-CLEAN enforces).

## Kernel-locked (intentionally NOT patched here)

`rapp_brainstem/**` and the root installers are stable kernel content,
shape-locked at the fork point (`rapp/BRAINSTEM-LOCK.json`, test T-LOCK).
Their remaining upstream references (support-issue URLs, the retired
registry-browser URL, soul onboarding link) are kernel bugs/content: the
fix lands upstream and arrives via a sanctioned sync PR — never as a
downstream patch. Tracked in `rapp/ALIGNMENT.md`.

## Documented functional exception

- `vbrainstem/brainstem_web.py` → `https://rapp-auth.kwildfeuer.workers.dev`
  — the CORS proxy for GitHub device-code sign-in (github.com sends no CORS
  headers; something must proxy those two endpoints for a browser runtime).
  **Override without a code change: set `VB_AUTH_WORKER`.** Standing action:
  deploy an MS-owned worker and flip the default (rapp/ALM.md §6).

## Pending upstream sync (MS-PENDING)

~119 URLs point at `microsoft.github.io/aibast-agents-library/...` paths
that exist in this tree but not yet on the microsoft `main` — they resolve
the moment the sync PR lands. The live suite passes against the staging
Pages today.

## Not defects

Placeholder/example hosts (`contoso.sharepoint.com`, `YOUR-APP`,
`localhost:*`, template variables), POST-only endpoints that 404 on GET
(`github.com/login/device/code`), bot-blocked-but-alive hosts (405/403/429),
and schema identifier URLs (`schema.org/extensions`) were classified and
left as-is.
