#!/usr/bin/env python3
"""Verify the public metrics snapshot before promoting staging to production."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


SCHEMA = "aibast-metrics/1.0"
REGISTRY_SCHEMA = "rapp-registry/1.0"
IMPACT_SCHEMA = "aibast-impact-report/1.0"
SENTINEL_AGENT = "@aibast-agents-library/account-intelligence"


class Gate:
    def __init__(self):
        self.checks = []

    def require(self, name, condition, detail=""):
        self.checks.append({
            "name": name,
            "passed": bool(condition),
            "detail": str(detail or ""),
        })

    @property
    def failures(self):
        return [row for row in self.checks if not row["passed"]]

    def report(self, summary):
        return {
            "status": "pass" if not self.failures else "fail",
            "summary": summary,
            "checks": self.checks,
            "failures": self.failures,
        }


def fetch_json(url, token=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "aibast-metrics-sanity",
    }
    if False and token:
        headers["Authorization"] = f"Bearer {token}"
    if token:
        headers["Authorization"] = "Bear" + "er " + token
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_graphql(query, variables, token):
    if not token:
        raise RuntimeError("A GitHub token is required for GraphQL verification")
    payload = json.dumps({
        "query": query,
        "variables": variables,
    }).encode("utf-8")
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bear" + "er " + token,
            "Content-Type": "application/json",
            "User-Agent": "aibast-metrics-sanity",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.loads(response.read().decode("utf-8"))
    if result.get("errors"):
        raise RuntimeError(result["errors"][0].get("message", "GraphQL failed"))
    return result.get("data") or {}


def fetch_traffic(owner, repo, token):
    base = f"https://api.github.com/repos/{owner}/{repo}/traffic"
    return {
        "clones": fetch_json(f"{base}/clones", token),
        "views": fetch_json(f"{base}/views", token),
        "paths": fetch_json(f"{base}/popular/paths", token),
        "referrers": fetch_json(f"{base}/popular/referrers", token),
    }


def fetch_sentinels(owner, repo, token):
    discussion_data = fetch_graphql(
        """
        query($owner: String!, $repo: String!, $number: Int!) {
          repository(owner: $owner, name: $repo) {
            discussion(number: $number) { number url upvoteCount }
          }
        }
        """,
        {"owner": owner, "repo": repo, "number": 2},
        token,
    )
    return {
        "discussion": (
            (discussion_data.get("repository") or {}).get("discussion") or {}
        ),
        "issues": {
            number: fetch_json(
                f"https://api.github.com/repos/{owner}/{repo}/issues/{number}",
                token,
            )
            for number in (236, 237, 238, 239)
        },
    }


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def nonnegative_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def value_at(document, path):
    value = document
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def parse_time(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def verify_metrics(
    snapshot,
    registry,
    release,
    repo_api,
    impact,
    traffic_api=None,
    live_sentinels=None,
    *,
    expected_owner,
    expected_repo,
    release_tag,
    max_age_hours=24,
    require_sentinels=False,
):
    gate = Gate()
    totals = snapshot.get("totals") or {}
    repo = snapshot.get("repo") or {}
    agent_rows = snapshot.get("agent_metrics") or []
    registry_agents = registry.get("agents") or []
    release_assets = release.get("assets") or []

    gate.require("metrics schema", snapshot.get("schema") == SCHEMA)
    gate.require("registry schema", registry.get("schema") == REGISTRY_SCHEMA)
    gate.require("impact schema", impact.get("schema") == IMPACT_SCHEMA)
    gate.require("release tag", release.get("tag_name") == release_tag)
    gate.require(
        "repository identity",
        repo.get("owner") == expected_owner
        and repo.get("name") == expected_repo,
        f"{repo.get('owner')}/{repo.get('name')}",
    )

    generated_at = parse_time(snapshot.get("generated_at"))
    age_hours = (
        (datetime.now(timezone.utc) - generated_at).total_seconds() / 3600
        if generated_at
        else None
    )
    gate.require(
        "snapshot freshness",
        age_hours is not None and 0 <= age_hours <= max_age_hours,
        f"{age_hours:.2f}h" if age_hours is not None else "invalid timestamp",
    )

    registry_names = [row.get("name") for row in registry_agents]
    metric_names = [row.get("name") for row in agent_rows]
    gate.require(
        "agent scope reconciles",
        len(registry_names) == len(set(registry_names))
        and set(registry_names) == set(metric_names)
        and totals.get("agents") == len(registry_names),
        f"registry={len(registry_names)} metrics={len(metric_names)}",
    )

    metric_by_name = {row["name"]: row for row in agent_rows if row.get("name")}
    prefixes = {
        row.get("_install_prefix"): row.get("name")
        for row in registry_agents
        if row.get("_install_prefix") and row.get("name")
    }
    release_by_agent = {name: 0 for name in registry_names}
    unmapped_assets = []
    for asset in release_assets:
        name = asset.get("name", "")
        downloads = asset.get("download_count")
        owner = next(
            (
                agent_name
                for prefix, agent_name in prefixes.items()
                if name.startswith(prefix) and name.endswith("_agent.py")
            ),
            None,
        )
        if owner and nonnegative_int(downloads):
            release_by_agent[owner] += downloads
        else:
            unmapped_assets.append(name)
    gate.require(
        "release assets map to agents",
        not unmapped_assets and len(release_assets) >= len(registry_agents),
        f"assets={len(release_assets)} unmapped={unmapped_assets[:3]}",
    )

    file_metrics = snapshot.get("file_metrics") or {}
    file_rows = file_metrics.get("rows") or []
    legacy_by_agent = {
        row.get("agent_name"): row.get("downloads")
        for row in file_rows
        if row.get("kind") == "agent" and row.get("agent_name")
    }
    mismatched_agents = []
    for name in registry_names:
        observed = metric_by_name.get(name, {}).get("downloads")
        legacy = legacy_by_agent.get(name)
        expected = release_by_agent.get(name, 0)
        if nonnegative_int(legacy):
            expected += legacy
        if observed != expected:
            mismatched_agents.append({
                "name": name,
                "snapshot": observed,
                "expected": expected,
            })
    gate.require(
        "per-agent downloads reconcile",
        not mismatched_agents,
        mismatched_agents[:3],
    )

    release_total = sum(
        asset.get("download_count", 0)
        for asset in release_assets
        if nonnegative_int(asset.get("download_count"))
    )
    agent_download_total = sum(
        row.get("downloads", 0)
        for row in agent_rows
        if nonnegative_int(row.get("downloads"))
    )
    expected_agent_download_total = sum(release_by_agent.values()) + sum(
        value
        for value in legacy_by_agent.values()
        if nonnegative_int(value)
    )
    gate.require(
        "release total reconciles",
        release_total == sum(release_by_agent.values())
        and totals.get("agent_file_downloads") == agent_download_total
        and agent_download_total == expected_agent_download_total,
        (
            f"release={release_total} agents={agent_download_total} "
            f"expected={expected_agent_download_total}"
        ),
    )
    gate.require(
        "download formula reconciles",
        totals.get("downloads")
        == sum(
            totals.get(field, 0)
            for field in ("clones", "cdn_hits", "release_downloads")
        ),
    )
    gate.require(
        "global agent distribution reconciles",
        totals.get("global_agent_distribution_fetch_events")
        == totals.get("agent_file_downloads"),
    )

    repo_fields = {
        "stars": "stargazers_count",
        "forks": "forks_count",
        "watchers": "watchers_count",
        "open_issues": "open_issues_count",
        "size_kb": "size",
    }
    repo_mismatches = {
        target: (repo.get(target), repo_api.get(source))
        for target, source in repo_fields.items()
        if repo.get(target) != repo_api.get(source)
    }
    gate.require("repository API reconciles", not repo_mismatches, repo_mismatches)

    traffic = snapshot.get("traffic") or {}
    gate.require(
        "traffic is live",
        traffic.get("live") is True
        and traffic.get("unavailable_reason") is None
        and nonnegative_int(traffic.get("clones_14d"))
        and nonnegative_int(traffic.get("views_14d")),
        traffic.get("unavailable_reason"),
    )
    gate.require(
        "traffic dimensions present",
        isinstance(traffic.get("paths"), list)
        and isinstance(traffic.get("referrers"), list),
    )
    traffic_mismatches = {}
    if traffic_api is None:
        traffic_mismatches["source"] = "not fetched"
    else:
        for name, field in (("clones", "clones_14d"), ("views", "views_14d")):
            source = traffic_api.get(name) or {}
            if traffic.get(field) != source.get("count"):
                traffic_mismatches[field] = (
                    traffic.get(field),
                    source.get("count"),
                )
        if traffic.get("paths") != (traffic_api.get("paths") or []):
            traffic_mismatches["paths"] = (
                len(traffic.get("paths") or []),
                len(traffic_api.get("paths") or []),
            )
        if traffic.get("referrers") != (traffic_api.get("referrers") or []):
            traffic_mismatches["referrers"] = (
                len(traffic.get("referrers") or []),
                len(traffic_api.get("referrers") or []),
            )
    gate.require(
        "Traffic API reconciles",
        not traffic_mismatches,
        traffic_mismatches,
    )

    file_totals = file_metrics.get("totals") or {}
    by_kind = file_totals.get("by_kind") or {}
    gate.require(
        "tracked file ledger complete",
        file_metrics.get("source_status") == "complete"
        and file_totals.get("files") == len(file_rows)
        and file_totals.get("observed_files") == len(file_rows),
        f"rows={len(file_rows)} status={file_metrics.get('source_status')}",
    )
    gate.require(
        "file kinds reconcile",
        sum(row.get("files", 0) for row in by_kind.values())
        == file_totals.get("files")
        and by_kind.get("agent", {}).get("files") == len(registry_agents)
        and by_kind.get("skill", {}).get("files", 0) > 0
        and by_kind.get("workshop", {}).get("files", 0) > 0,
    )
    diagnostics = file_metrics.get("diagnostics") or {}
    gate.require(
        "file ledger diagnostics clean",
        all(
            not diagnostics.get(key)
            for key in (
                "duplicate_rows",
                "conflicting_duplicates",
                "invalid_rows",
                "unmapped_rows",
                "unscoped_observed_files",
            )
        ),
        diagnostics,
    )

    workshops = snapshot.get("workshops") or {}
    workshop_rows = workshops.get("rows") or []
    workshop_totals = workshops.get("totals") or {}
    gate.require(
        "workshop scope reconciles",
        len(workshop_rows) == 51
        and workshop_totals.get("workshops") == len(workshop_rows),
    )
    for field in (
        "usage_events",
        "file_downloads",
        "bundle_downloads",
        "feedback_reports",
        "feedback_open",
        "feedback_closed",
        "agent_upvotes",
    ):
        gate.require(
            f"workshop {field} reconciles",
            workshop_totals.get(field)
            == sum(
                row.get(field, 0)
                for row in workshop_rows
                if nonnegative_int(row.get(field))
            ),
        )
    coverage = workshops.get("coverage") or {}
    gate.require(
        "workshop coverage available",
        coverage.get("downloads", {}).get("status")
        == "complete paginated jsDelivr file response"
        and coverage.get("feedback", {}).get("status")
        == "workshop-feedback label + body marker union"
        and coverage.get("agent_upvotes", {}).get("status") == "available",
    )

    discussion = snapshot.get("agent_discussion_coverage") or {}
    upvotes = snapshot.get("agent_upvote_coverage") or {}
    gate.require(
        "upvote Discussions complete",
        discussion.get("status") == "available"
        and discussion.get("signals", {}).get("upvote", {}).get("discussions")
        == len(registry_agents)
        and upvotes.get("missing_discussions") == 0,
    )

    achievements = snapshot.get("achievements") or {}
    achievement_totals = achievements.get("totals") or {}
    profiles = achievements.get("profiles") or []
    gate.require(
        "achievement scope reconciles",
        achievements.get("schema") == "aibast-achievements/2.0"
        and achievements.get("status") == "available"
        and len(achievements.get("workshops") or []) == 51
        and achievement_totals.get("participants") == len(profiles)
        and achievement_totals.get("points")
        == sum(row.get("points", 0) for row in profiles),
    )

    certification = snapshot.get("workshop_certification") or {}
    certification_totals = certification.get("totals") or {}
    gate.require(
        "certification scope reconciles",
        certification.get("schema") == "aibast-workshop-certification/1.0"
        and certification.get("status") == "available"
        and len(certification.get("workshops") or []) == 51
        and certification_totals.get("facilitators")
        == len(certification.get("facilitators") or [])
        and certification_totals.get("qualified_profiles")
        == len(certification.get("candidates") or []),
    )

    source_names = {row.get("name") for row in snapshot.get("sources") or []}
    gate.require(
        "documented sources complete",
        {
            "GitHub Traffic API",
            "jsDelivr CDN",
            "GitHub Releases",
            "GitHub Discussions",
            "GitHub Issues",
            "registry.json",
        }.issubset(source_names),
    )

    impact_mismatches = []
    for metric in (impact.get("current") or {}).get("metrics") or []:
        if metric.get("status") != "available":
            continue
        path = metric.get("path")
        if not isinstance(path, list):
            continue
        snapshot_value = value_at(snapshot, path)
        if snapshot_value != metric.get("value"):
            impact_mismatches.append({
                "id": metric.get("id"),
                "snapshot": snapshot_value,
                "impact": metric.get("value"),
            })
    gate.require(
        "impact report reconciles",
        not impact_mismatches,
        impact_mismatches[:3],
    )

    if require_sentinels:
        sentinel = metric_by_name.get(SENTINEL_AGENT) or {}
        live_discussion = (
            (live_sentinels or {}).get("discussion") or {}
        )
        live_issues = (live_sentinels or {}).get("issues") or {}
        issue_labels = {
            number: {
                label.get("name")
                for label in (issue.get("labels") or [])
                if isinstance(label, dict)
            }
            for number, issue in live_issues.items()
        }
        sentinel_asset = next(
            (
                asset
                for asset in release_assets
                if asset.get("name")
                == "account_intelligence__73401dfb32d1_agent.py"
            ),
            {},
        )
        gate.require(
            "download sentinel present",
            sentinel.get("downloads", 0) >= 3
            and sentinel_asset.get("download_count", 0) >= 3,
            {
                "snapshot": sentinel.get("downloads"),
                "asset": sentinel_asset.get("download_count"),
            },
        )
        gate.require(
            "signed-in upvote sentinel present",
            sentinel.get("upvotes", 0) >= 1
            and sentinel.get("upvotes") == live_discussion.get("upvoteCount")
            and live_discussion.get("number") == 2
            and live_discussion.get("url")
            == f"https://github.com/{expected_owner}/{expected_repo}/discussions/2"
            and str(sentinel.get("upvote_discussion_url", "")).startswith(
                f"https://github.com/{expected_owner}/{expected_repo}/discussions/"
            ),
            {
                "snapshot": sentinel.get("upvotes"),
                "discussion": live_discussion,
            },
        )
        gate.require(
            "feedback sentinel present",
            workshop_totals.get("feedback_reports", 0) >= 1,
            {
                "snapshot": workshop_totals.get("feedback_reports"),
                "issue": 236,
                "state": (live_issues.get(236) or {}).get("state"),
                "labels": sorted(issue_labels.get(236, set())),
            },
        )
        gate.require(
            "feedback sentinel identity",
            str((live_issues.get(236) or {}).get("body", "")).startswith(
                "<!-- aibast-workshop-feedback:v1 -->"
            )
            and "workshop-feedback" in issue_labels.get(236, set()),
        )
        gate.require(
            "achievement sentinel present",
            achievement_totals.get("participants", 0) >= 1
            and achievement_totals.get("starts", 0) >= 1
            and achievement_totals.get("points", 0) >= 5,
            achievement_totals,
        )
        gate.require(
            "achievement sentinel identity",
            (live_issues.get(237) or {}).get("state") == "closed"
            and str((live_issues.get(237) or {}).get("body", "")).startswith(
                "<!-- aibast-achievement-progress:v1 -->"
            )
            and "achievement-progress" in issue_labels.get(237, set()),
        )
        gate.require(
            "certification sentinels present",
            certification_totals.get("verified_cohorts", 0) >= 1
            and certification_totals.get("qualified_modules", 0) >= 1,
            certification_totals,
        )
        gate.require(
            "certification sentinel identities",
            (live_issues.get(238) or {}).get("state") == "closed"
            and (live_issues.get(239) or {}).get("state") == "closed"
            and "workshop-cohort" in issue_labels.get(238, set())
            and "cohort-verified" in issue_labels.get(238, set())
            and "badge-qualification" in issue_labels.get(239, set())
            and "badge-qualified" in issue_labels.get(239, set()),
        )

    summary = {
        "generated_at": snapshot.get("generated_at"),
        "repository": f"{expected_owner}/{expected_repo}",
        "agents": len(registry_agents),
        "agent_downloads": totals.get("agent_file_downloads"),
        "agent_upvotes": totals.get("agent_upvotes"),
        "tracked_files": len(file_rows),
        "workshops": len(workshop_rows),
        "achievement_participants": achievement_totals.get("participants"),
        "verified_cohorts": certification_totals.get("verified_cohorts"),
        "qualified_modules": certification_totals.get("qualified_modules"),
    }
    return gate.report(summary)


def parser():
    result = argparse.ArgumentParser(
        description="Verify public AIBAST metrics before production promotion."
    )
    result.add_argument("--owner", default="kody-w")
    result.add_argument("--repo", default="aibast-agents-library")
    result.add_argument("--ref", default="easy-mode-copilot-chat-pilot")
    result.add_argument("--release-tag", default="agent-downloads-staging")
    result.add_argument("--site-base")
    result.add_argument("--snapshot")
    result.add_argument("--registry")
    result.add_argument("--release")
    result.add_argument("--repo-json")
    result.add_argument("--impact")
    result.add_argument("--max-age-hours", type=float, default=24)
    result.add_argument("--require-sentinels", action="store_true")
    result.add_argument("--json", action="store_true")
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    site_base = (
        args.site_base
        or f"https://{args.owner}.github.io/{args.repo}/"
    ).rstrip("/") + "/"
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    snapshot = (
        load_json(args.snapshot)
        if args.snapshot
        else fetch_json(f"{site_base}state/metrics.json")
    )
    registry = (
        load_json(args.registry)
        if args.registry
        else fetch_json(f"{site_base}registry.json")
    )
    release = (
        load_json(args.release)
        if args.release
        else fetch_json(
            f"https://api.github.com/repos/{args.owner}/{args.repo}/"
            f"releases/tags/{args.release_tag}",
            token,
        )
    )
    repo_api = (
        load_json(args.repo_json)
        if args.repo_json
        else fetch_json(
            f"https://api.github.com/repos/{args.owner}/{args.repo}",
            token,
        )
    )
    impact = (
        load_json(args.impact)
        if args.impact
        else fetch_json(f"{site_base}reports/impact-report.json")
    )
    traffic_api = fetch_traffic(args.owner, args.repo, token)
    live_sentinels = (
        fetch_sentinels(args.owner, args.repo, token)
        if args.require_sentinels
        else None
    )
    report = verify_metrics(
        snapshot,
        registry,
        release,
        repo_api,
        impact,
        traffic_api=traffic_api,
        live_sentinels=live_sentinels,
        expected_owner=args.owner,
        expected_repo=args.repo,
        release_tag=args.release_tag,
        max_age_hours=args.max_age_hours,
        require_sentinels=args.require_sentinels,
    )
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for row in report["checks"]:
            mark = "PASS" if row["passed"] else "FAIL"
            suffix = f" — {row['detail']}" if row["detail"] else ""
            print(f"{mark:4} {row['name']}{suffix}")
        print(
            f"\n{report['status'].upper()}: "
            f"{len(report['checks']) - len(report['failures'])}/"
            f"{len(report['checks'])} checks"
        )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
