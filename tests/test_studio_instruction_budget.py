import json
from pathlib import Path

import pytest

from tools import build_studio_package as package

ROOT = Path(__file__).resolve().parents[1]
COMPACTED = (
    "portfolio-rebalancing", "procurement-agent", "building-permit-processing",
    "client-health-score", "fs-customer-onboarding", "fs-regulatory-compliance",
)


def long_site_url():
    prefix = "https://contoso.sharepoint.com/sites/"
    return prefix + "a" * (1000 - len(prefix))


def test_every_committed_global_has_runtime_and_site_substitution_headroom():
    for slug in package.data.studio_slugs():
        text = (ROOT / "solutions" / slug / "studio/agent/GLOBAL-INSTRUCTIONS.md").read_text()
        if slug == package.REFERENCE and package.SITE_TOKEN not in text:
            text += (ROOT / "tests/fixtures/studio/emission-tracking-site-section.md").read_text()
        assert text.count("YOUR_SITE_ADDRESS") == 1, slug
        assert len(text) <= 7000, (slug, len(text))
        assert len(text.replace("YOUR_SITE_ADDRESS", long_site_url())) <= 8000, slug


@pytest.mark.parametrize("slug", COMPACTED)
def test_compaction_preserves_full_controls_and_exact_runtime_mappings(slug):
    inputs = package.load_inputs(slug)
    schema = package.make_schema(inputs, ROOT)
    tools = package.tool_names(schema, inputs.overrides)
    original = (ROOT / "solutions" / slug / "manual/GLOBAL-INSTRUCTIONS.md").read_text()
    first, body = original.split("\n", 1)
    expected = package.studio_instructions_heading(first) + "\n" + package.rewrite_source_references(body, inputs)
    expected = expected.replace(package.OLD_ROUTING, package.ROUTING)
    files = package.package_files(slug)
    base = Path("solutions") / slug
    control = base / "studio/agent/knowledge" / f"{slug}-instruction-controls.md"
    assert files[control] == expected
    assert "YOUR_SITE_ADDRESS" not in files[control]
    instructions = files[base / "studio/agent/GLOBAL-INSTRUCTIONS.md"]
    assert package.column_instructions(schema, tools) in instructions
    assert instructions.endswith(package.sharepoint_site_section(inputs, schema) + "\n")
    assert "Before every answer, retrieve" in instructions
    assert "mandatory human-review paragraph" in instructions
    document = json.loads(files[base / "studio/walkthrough.json"])
    assert control.relative_to(base).as_posix() in document["agent"]["knowledge"]
    assert any(control.relative_to(base).as_posix() in step.get("downloads", [])
               for step in document["modes"]["manual"]["steps"])
    package.check_instruction_budget(instructions)


def test_procurement_mandatory_human_review_and_footer_remain_verbatim():
    files = package.package_files("procurement-agent")
    instructions = files[Path("solutions/procurement-agent/studio/agent/GLOBAL-INSTRUCTIONS.md")]
    assert ("Required human reviews remain unresolved: Finance for budget validation and reconciliation; "
            "procurement for request and supplier review; legal, security, competition, supplier diversity, "
            "conflicts of interest, business-owner, delegated-authority and explicit publication review by "
            "the corresponding authorized owners.") in instructions
    assert ("Synthetic procurement evidence; decision support only. No approval, supplier action, purchase "
            "order, or spend commitment occurred.") in instructions


def test_instruction_budget_rejects_overlength_and_ambiguous_templates():
    valid = "x" * (7000 - len("YOUR_SITE_ADDRESS")) + "YOUR_SITE_ADDRESS"
    package.check_instruction_budget(valid)
    with pytest.raises(package.StudioPackageError, match="maximum 7000"):
        package.check_instruction_budget("x" + valid)
    for invalid in ("no site token", valid + "YOUR_SITE_ADDRESS"):
        with pytest.raises(package.StudioPackageError, match="exactly once"):
            package.check_instruction_budget(invalid)
