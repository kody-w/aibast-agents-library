import copy
import json
from pathlib import Path

from scripts import verify_metrics_sanity
from scripts.verify_metrics_sanity import verify_metrics


ROOT = Path(__file__).resolve().parent.parent


def fixture():
    snapshot = json.loads((ROOT / "state/metrics.json").read_text())
    registry = json.loads((ROOT / "registry.json").read_text())
    impact = json.loads((ROOT / "reports/impact-report.json").read_text())
    metrics = {
        row["name"]: row for row in snapshot["agent_metrics"]
    }
    release = {
        "tag_name": "agent-downloads-staging",
        "assets": [
            {
                "name": agent["_install_filename"],
                "download_count": metrics[agent["name"]]["downloads"],
            }
            for agent in registry["agents"]
        ],
    }
    repo = snapshot["repo"]
    repo_api = {
        "stargazers_count": repo["stars"],
        "forks_count": repo["forks"],
        "watchers_count": repo["watchers"],
        "open_issues_count": repo["open_issues"],
        "size": repo["size_kb"],
    }
    traffic = snapshot["traffic"]
    traffic_api = {
        "clones": {"count": traffic["clones_14d"]},
        "views": {"count": traffic["views_14d"]},
        "paths": traffic["paths"],
        "referrers": traffic["referrers"],
    }
    return snapshot, registry, release, repo_api, impact, traffic_api


def run_gate(*, require_sentinels=False):
    snapshot, registry, release, repo_api, impact, traffic_api = fixture()
    return verify_metrics(
        snapshot,
        registry,
        release,
        repo_api,
        impact,
        traffic_api=traffic_api,
        expected_owner="kody-w",
        expected_repo="aibast-agents-library",
        release_tag="agent-downloads-staging",
        max_age_hours=24 * 365,
        require_sentinels=require_sentinels,
    )


def test_repository_snapshot_passes_structural_sanity_gate():
    report = run_gate()

    assert report["status"] == "pass", report["failures"]
    assert report["summary"]["agents"] == 72
    assert report["summary"]["tracked_files"] > 5000
    assert report["summary"]["workshops"] == 51


def test_gate_fails_when_one_agent_download_drifts():
    snapshot, registry, release, repo_api, impact, traffic_api = fixture()
    release["assets"][0]["download_count"] += 1

    report = verify_metrics(
        snapshot,
        registry,
        release,
        repo_api,
        impact,
        traffic_api=traffic_api,
        expected_owner="kody-w",
        expected_repo="aibast-agents-library",
        release_tag="agent-downloads-staging",
        max_age_hours=24 * 365,
    )

    failures = {row["name"] for row in report["failures"]}
    assert "per-agent downloads reconcile" in failures
    assert "release total reconciles" in failures


def test_gate_fails_when_workshop_scope_is_incomplete():
    snapshot, registry, release, repo_api, impact, traffic_api = fixture()
    snapshot = copy.deepcopy(snapshot)
    snapshot["workshops"]["rows"].pop()

    report = verify_metrics(
        snapshot,
        registry,
        release,
        repo_api,
        impact,
        traffic_api=traffic_api,
        expected_owner="kody-w",
        expected_repo="aibast-agents-library",
        release_tag="agent-downloads-staging",
        max_age_hours=24 * 365,
    )

    assert "workshop scope reconciles" in {
        row["name"] for row in report["failures"]
    }


def test_sentinel_mode_fails_closed_without_behavioral_proof():
    snapshot, registry, release, repo_api, impact, traffic_api = fixture()
    snapshot = copy.deepcopy(snapshot)
    sentinel = next(
        row for row in snapshot["agent_metrics"]
        if row["name"] == "@aibast-agents-library/account-intelligence"
    )
    sentinel["upvotes"] = 0
    snapshot["workshops"]["totals"]["feedback_reports"] = 0
    snapshot["achievements"]["totals"].update({
        "participants": 0,
        "starts": 0,
        "points": 0,
    })
    snapshot["workshop_certification"]["totals"].update({
        "verified_cohorts": 0,
        "qualified_modules": 0,
    })

    report = verify_metrics(
        snapshot,
        registry,
        release,
        repo_api,
        impact,
        traffic_api=traffic_api,
        expected_owner="kody-w",
        expected_repo="aibast-agents-library",
        release_tag="agent-downloads-staging",
        max_age_hours=24 * 365,
        require_sentinels=True,
    )

    failures = {row["name"] for row in report["failures"]}
    assert "signed-in upvote sentinel present" in failures
    assert "feedback sentinel present" in failures
    assert "achievement sentinel present" in failures
    assert "certification sentinels present" in failures


def test_gate_fails_when_snapshot_traffic_disagrees_with_api():
    snapshot, registry, release, repo_api, impact, traffic_api = fixture()
    snapshot = copy.deepcopy(snapshot)
    snapshot["traffic"]["clones_14d"] += 1

    report = verify_metrics(
        snapshot,
        registry,
        release,
        repo_api,
        impact,
        traffic_api=traffic_api,
        expected_owner="kody-w",
        expected_repo="aibast-agents-library",
        release_tag="agent-downloads-staging",
        max_age_hours=24 * 365,
    )

    assert "Traffic API reconciles" in {
        row["name"] for row in report["failures"]
    }


def test_fetch_json_sends_supplied_token(monkeypatch):
    observed = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return b"{}"

    def fake_urlopen(request, timeout):
        observed["authorization"] = request.get_header("Authorization")
        observed["timeout"] = timeout
        return Response()

    monkeypatch.setattr(
        verify_metrics_sanity.urllib.request,
        "urlopen",
        fake_urlopen,
    )

    assert verify_metrics_sanity.fetch_json(
        "https://example.test",
        "test-token",
    ) == {}
    assert observed == {
        "authorization": "Bearer test-token",
        "timeout": 60,
    }
