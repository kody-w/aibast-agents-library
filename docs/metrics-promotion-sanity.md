# Metrics promotion sanity check

Use this gate before merging staging into `microsoft/main`, then run it again
against production after Pages and the metrics workflow settle.

## One-command staging gate

```bash
GITHUB_TOKEN="$(gh auth token)" python scripts/verify_metrics_sanity.py \
  --owner kody-w \
  --repo aibast-agents-library \
  --ref easy-mode-copilot-chat-pilot \
  --release-tag agent-downloads-staging \
  --site-base https://kody-w.github.io/aibast-agents-library/ \
  --require-sentinels
```

The command exits nonzero on drift. It verifies the public Pages snapshot,
registry, impact report, GitHub repository API, and immutable release assets.

## Staging sentinels

These public-safe records deliberately make the important write paths nonzero:

| Signal | Staging sentinel |
|---|---|
| Agent download | `account_intelligence__73401dfb32d1_agent.py` |
| Signed-in agent upvote | Account Intelligence Discussion [#2](https://github.com/kody-w/aibast-agents-library/discussions/2) |
| Workshop feedback | Issue [#236](https://github.com/kody-w/aibast-agents-library/issues/236) |
| Achievement progress | Issue [#237](https://github.com/kody-w/aibast-agents-library/issues/237) |
| Verified facilitator cohort | Issue [#238](https://github.com/kody-w/aibast-agents-library/issues/238) with `cohort-verified` |
| Qualified badge module | Issue [#239](https://github.com/kody-w/aibast-agents-library/issues/239) with `badge-qualified` |

Do not delete these records while staging is the production reference. They
contain no private roster, Microsoft identity, customer, test-answer, or token
data.

## What the gate proves

| Metric surface | Authority | Required reconciliation |
|---|---|---|
| Repository reach | GitHub repository and Traffic APIs | Stars, forks, watchers, issues, size, clones, views, paths, and referrers are live and attributed to the requested repository. |
| Agent downloads | `agent-downloads[-staging]` release assets | Every immutable asset maps to one registry agent; versioned assets aggregate by `_install_prefix`; every `agent_metrics[].downloads` value and total reconcile. |
| Repository downloads | Snapshot totals | `downloads = clones + cdn_hits + release_downloads`. |
| Tracked files | jsDelivr file ledger | All tracked files and file-kind totals reconcile with no duplicates, conflicts, invalid rows, or unmapped rows. |
| Signed-in upvotes | Canonical rating Discussions | One Discussion exists per agent, all URLs match the deployment owner, and the staging sentinel survives Discussion synchronization. |
| Workshop adoption | Popular paths, file ledger, and feedback issues | Exactly 51 workshops exist and every workshop total sums from its rows. |
| Achievements | Strict opt-in progress issues | Profiles, points, starts, completion counts, and all 51 workshop rows reconcile. |
| Certification | Reviewer-labeled cohort and qualification issues | Public-safe profiles and totals reconcile; verified cohort and qualified module sentinels are present. |
| Impact exports | `reports/impact-report.json` | Every available metric path equals the value in the current static snapshot. |

`agent_upvotes` is the public engagement signal. Legacy acquisition fields may
remain in historical JSON, but they are not displayed, sorted, promoted, or
accepted as a substitute for agent downloads.

## Production promotion check

1. Run the strict staging command above. It must finish with `PASS`.
2. Merge the validated branch to `microsoft/main`.
3. Wait for `Agent Download Assets`, `Metrics Snapshot`, preflight, and Pages to
   succeed.
4. Run the structural production gate:

   ```bash
   GITHUB_TOKEN="$(gh auth token)" python scripts/verify_metrics_sanity.py \
     --owner microsoft \
     --repo aibast-agents-library \
     --ref main \
     --release-tag agent-downloads \
     --site-base https://microsoft.github.io/aibast-agents-library/
   ```

5. Compare staging and production by invariant, not by absolute traffic totals.
   Production stars, clones, views, issues, and historic downloads naturally
   differ from the fork.
6. Perform one controlled production agent download:
   - record the asset's `download_count`;
   - download its exact `browser_download_url`;
   - wait for GitHub's counter to advance;
   - dispatch `metrics.yml`;
   - confirm that exact agent row advances to the same count on raw `main` and
     deployed Pages JSON.
7. Re-run the production gate. Do not promote if any check is skipped or
   unavailable.

## Useful commands

```bash
# Refresh staging metrics
gh workflow run metrics.yml \
  -R kody-w/aibast-agents-library \
  --ref easy-mode-copilot-chat-pilot

# Inspect the latest staging metrics run
gh run list \
  -R kody-w/aibast-agents-library \
  --workflow metrics.yml \
  --branch easy-mode-copilot-chat-pilot \
  --limit 5

# Compare one release asset with its static agent row
gh api repos/kody-w/aibast-agents-library/releases/tags/agent-downloads-staging
curl -fsSL https://kody-w.github.io/aibast-agents-library/state/metrics.json
```

## Failure handling

- **Release asset differs from the agent row:** rerun metrics only after the
  GitHub asset counter advances; GitHub counters are eventually consistent.
- **Snapshot push loses a race:** the workflow must rebase and retry rather than
  discard the newer snapshot.
- **Traffic is not live:** verify `METRICS_TOKEN` has repository
  `Administration: read`.
- **Discussion coverage is partial:** verify `DISCUSSIONS_TOKEN`, Discussion
  permissions, and the expected deployment owner.
- **Sentinel missing:** inspect its Discussion or issue labels before changing
  the collector. The sentinel is designed to catch write-path regressions.
