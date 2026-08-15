"""Semantic regression gates for constitutional and public-governance drift."""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _normalized(relative_path):
    return " ".join(_read(relative_path).split())


def test_constitution_covers_existing_repository_topology():
    constitution = _read("CONSTITUTION.md")
    required_paths = {
        "rapp_brainstem/": ROOT / "rapp_brainstem",
        "agents/@aibast-agents-library/": (
            ROOT / "agents" / "@aibast-agents-library"
        ),
        "community_rapp/": ROOT / "community_rapp",
        "rapp_ai/": ROOT / "rapp_ai",
        "rar/registry.json": ROOT / "rar" / "registry.json",
        "twin/stack_names.json": ROOT / "twin" / "stack_names.json",
        "docs/badge-program.md": ROOT / "docs" / "badge-program.md",
        "frontier-channel.json": (
            ROOT / "rapp_brainstem" / "frontier-channel.json"
        ),
    }

    for reference, path in required_paths.items():
        assert reference in constitution, f"Constitution omits {reference}"
        assert path.exists(), f"Constitution references missing path {path}"
    assert "docs/install.*" in constitution
    assert list(ROOT.glob("MSFTAIBASMultiAgentCopilot_*.zip"))


def test_constitution_scopes_single_file_rule_and_separates_aibast_rar():
    constitution = _read("CONSTITUTION.md")

    assert "hot-loadable Python agent" in constitution
    assert "stack-level `manifest.json` is allowed" in constitution
    assert "separate from the public/global RAR" in constitution
    assert "There is nothing else" not in constitution
    assert "The single file is the law" not in constitution


def test_badge_fork_is_named_first_gate_not_publication_consent():
    constitution = _normalized("CONSTITUTION.md")
    rules = _normalized("docs/badge-program.md")
    canonical_repo = "microsoft/aibast-agents-library"

    for document in (constitution, rules):
        assert canonical_repo in document
        assert "first" in document.lower()
        assert "fork" in document.lower()
    assert "consents to badge-program submission and eligibility review" in constitution
    assert "not to publication of course results" in constitution
    assert "Public badge or progress display still requires" in constitution
    assert "fork relationship and fork owner" in rules
    assert "a public fork alone must never be treated as consent" not in constitution


def test_badge_program_defines_private_quiz_and_public_completion_gate():
    constitution = _normalized("CONSTITUTION.md")
    rules = _normalized("docs/badge-program.md")

    required = (
        "three-question",
        "open-book",
        "exact public",
        "explicitly confirm",
        "never the raw answers",
        "background GitHub issue API",
        "issue event triggers the governed badge workflow",
        "event-driven profile job",
        "nightly scheduled reconciliation",
        "manual workflow dispatch",
        "idempotent",
        "badge progress remains whole and current",
    )
    for phrase in required:
        assert phrase in constitution
    assert "Status: planned, not operational" in rules
    assert ".github/workflows/badge-profile.yml" in rules
    assert "docs/badges/" in rules
    assert "The course UI evaluates the check without publishing raw answers" in rules
    assert "The participant explicitly confirms that public payload" in rules


def test_powercat_reference_is_evidence_not_approval_or_schema_equivalence():
    constitution = _normalized("CONSTITUTION.md")
    contributing = _normalized("CONTRIBUTING.md")

    assert "microsoft/power-cat-skills" in constitution
    assert "33bc38456abb83f27daad968b748c8085f2a78ef" in constitution
    assert "observable public repository interaction patterns" in constitution
    assert "organization-owned marketplace and plugin metadata" in constitution
    assert "Individual `author` metadata exists in some reference skills" in constitution
    assert "stricter local requirement" in constitution
    assert "not a runtime dependency, schema dependency, legal opinion" in constitution
    assert "approved public-contribution shape observed" not in constitution
    assert "inspired by observable repository patterns" in contributing
    assert "not a shared schema, legal opinion" in contributing


def test_constitution_adopts_complete_public_interaction_policy():
    constitution = _normalized("CONSTITUTION.md")
    required = (
        "PowerCAT-Aligned Public Interaction Policy",
        "Public contribution lifecycle",
        "Public issue and API lifecycle",
        "Permissions and approval prompts",
        "Shared workflows and generated wrappers",
        "Public safety, support, and liability boundaries",
        "AIBAST enforcement exceeds the reference where needed",
        "allowed-tools",
        "CODEOWNERS or equivalent",
        "Microsoft Open Source Code of Conduct",
        "Trademark & Brand Guidelines",
        "MIT license",
        "Contributor License Agreement",
    )
    for phrase in required:
        assert phrase in constitution


def test_contributor_guide_is_curated_cla_gated_and_non_warranting():
    contributing = _normalized("CONTRIBUTING.md")

    required = (
        "Portable Runtime Agent Principle",
        "A business stack may be multi-file",
        "public/global RAR",
        "CODEOWNERS",
        "Contributor License Agreement",
        "Do not merge an external contribution until every required CLA check passes",
        "AIBAST Skill Requirements Inspired by PowerCAT",
        "`allowed-tools` as a comma-separated least-privilege list",
        "preview the complete public payload",
        "rights needed to submit",
        "does not enforce itself",
    )
    for phrase in required:
        assert phrase in contributing
    assert "No manifest.json. No README.md. No subdirectory." not in contributing
    assert "no security issues" not in contributing
    assert "guaranteed compatibility" not in contributing


def test_public_governance_surfaces_are_structured_and_scrubbed():
    codeowners = _read(".github/CODEOWNERS")
    issue_config = _read(".github/ISSUE_TEMPLATE/config.yml")
    forms = [
        _read(".github/ISSUE_TEMPLATE/bug_report.yml"),
        _read(".github/ISSUE_TEMPLATE/feature_request.yml"),
    ]
    pr_template = _read(".github/pull_request_template.md")
    support = _read("SUPPORT.md")
    conduct = _read("CODE_OF_CONDUCT.md")

    owners = [
        line for line in codeowners.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert any(re.fullmatch(r"\*\s+@\S+", line.strip()) for line in owners)
    assert "Interim review principal" in codeowners
    assert "blank_issues_enabled: false" in issue_config
    assert "https://aka.ms/SECURITY.md" in issue_config
    assert "/discussions" in issue_config

    disclosure_pattern = re.compile(
        r"- label:[^\n]*reviewed the final public payload[^\n]*\n"
        r"\s*required:\s*true\b"
    )
    for form in forms:
        assert "public" in form.lower()
        for prohibited in (
            "credentials",
            "internal URLs",
            "tenant IDs",
            "customer data",
            "proprietary code",
            "unnecessary personal",
        ):
            assert prohibited in form
        assert disclosure_pattern.search(form)

    assert "Public attribution and rights" in pr_template
    assert "Microsoft CLA check" in pr_template
    assert "Source authority and generated artifacts" in pr_template
    assert "Status: planned, not operational" in _read("docs/badge-program.md")
    assert "not operational until" in support
    assert "Security vulnerabilities" in support
    assert "Microsoft Open Source Code of Conduct FAQ" in conduct
    assert "moderation-support" in conduct


def test_readme_uses_authoritative_config_license_and_full_trademark_notice():
    readme = _normalized("README.md")

    assert "rapp_brainstem/.env.example" in readme
    assert "External CommunityRAPP dependency" in readme
    assert "not a Microsoft-maintained property" in readme
    assert "[MIT License](LICENSE)" in readme
    assert "MIT License — Copyright" not in readme
    assert "must not cause confusion or imply Microsoft sponsorship" in readme
    assert "third-party trademarks or logos" in readme


def test_badge_automation_launch_contract_is_atomic_and_explicit():
    workflow = ROOT / ".github" / "workflows" / "badge-profile.yml"
    output = ROOT / "docs" / "badges"

    assert workflow.exists() == output.exists(), (
        "badge-profile.yml and docs/badges/ must launch together"
    )
    if not workflow.exists():
        assert "Status: planned, not operational" in _read("docs/badge-program.md")
        return

    text = workflow.read_text(encoding="utf-8")
    for trigger in ("issues:", "schedule:", "workflow_dispatch:"):
        assert re.search(rf"(?m)^\s{{2}}{re.escape(trigger)}", text), (
            f"badge-profile.yml missing on.{trigger}"
        )
    for key in ("permissions:", "concurrency:"):
        assert re.search(rf"(?m)^{re.escape(key)}", text), (
            f"badge-profile.yml missing top-level {key}"
        )


def test_review_enforcement_gap_is_disclosed_until_admin_rules_exist():
    constitution = _normalized("CONSTITUTION.md")
    contributing = _normalized("CONTRIBUTING.md")

    assert "not technically review-enforced" in constitution
    assert "requires pull requests and code-owner approval" in constitution
    assert "does not enforce itself" in contributing


def test_all_published_installer_mirrors_are_byte_identical():
    for filename in ("install.sh", "install.ps1", "install.cmd", "install.command"):
        assert (ROOT / filename).read_bytes() == (ROOT / "docs" / filename).read_bytes()
