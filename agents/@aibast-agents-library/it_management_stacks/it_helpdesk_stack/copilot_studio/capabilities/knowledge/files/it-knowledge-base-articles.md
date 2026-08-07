# IT Knowledge Base Articles and Diagnostic Thresholds

> SYNTHETIC - DEMO DATA. Every article ID and remediation figure in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real knowledge base and remote management platform.

## Knowledge base articles

| Article ID | Title | Applies when |
|------------|-------|--------------|
| KB-IT-2341 | Slow laptop troubleshooting | Disk free < 20% OR memory used > 80% |
| KB-IT-1890 | VPN connection troubleshooting | Default article when no performance issue is detected |
| KB-IT-2100 | Email sync issues | Outlook / Exchange sync complaints |

### KB-IT-2341 - Slow laptop troubleshooting

1. Clear temp files and browser cache
2. End unnecessary background processes
3. Check disk space (keep >20% free)
4. Restart device if uptime >3 days
5. Run Windows Update

### KB-IT-1890 - VPN connection troubleshooting

1. Verify network connectivity
2. Restart VPN client
3. Clear DNS cache
4. Check VPN certificate expiration

### KB-IT-2100 - Email sync issues

1. Check Outlook connection status
2. Repair Outlook profile
3. Clear Outlook cache
4. Verify Exchange connectivity

## Self-service tips (issued with every knowledge answer)

- Restart weekly (prevents performance buildup)
- Keep 20%+ disk space free
- Close unused apps and tabs
- Check for updates regularly

## Diagnostic thresholds

These are the exact rules the diagnostics apply. A check only appears when its
condition is true.

| Check | Condition | Status | Finding rendered |
|-------|-----------|--------|------------------|
| Disk space | disk_free_pct < 20 | Critical | Only N% free |
| Memory usage | memory_used_pct > 85 | Warning | N% utilized |
| Running processes | running_processes > 100 | Warning | N active |
| Last restart | last_restart_days > 3 | Warning | N days ago |
| Updates pending | pending_updates > 0 | Info | N updates ready |
| All systems | no condition above fired | OK | No issues detected |

## Remediation rules and projected results

| Trigger | Actions offered | Projected effect |
|---------|-----------------|------------------|
| disk_free_pct < 30 | Clear temp files (4.2 GB freed); Clear browser cache (1.8 GB freed) | disk free +12 percentage points (capped at 100) |
| memory_used_pct > 80 | End background processes (12 processes closed) | memory used -22 percentage points (floored at 0) |
| running_processes > 100 | Pause OneDrive sync (15% CPU freed) | no disk or memory change |

If none of the three triggers fire, no remediation is offered - the device is
healthy.
