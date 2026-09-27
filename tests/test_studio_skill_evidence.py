import json
import re
from pathlib import Path

import pytest

from tools import build_studio_package as package

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "tests/fixtures/studio/emission-tracking-evidence-contract.json").read_text())


def test_required_evidence_bullets_and_existing_no_action_sentence_are_unchanged():
    inputs = package.load_inputs("emission-tracking")
    for path in inputs.skills:
        original = path.read_text()
        generated = package.skill_for(path, inputs)
        old = original.split("## Required evidence\n\n", 1)[1]
        bullets, never = old.split("\n\nNever imply ", 1)
        expected = ("## Required evidence\n\n" + CONTRACT["intro"] + "\n\n" + bullets + "\n\n"
                    + CONTRACT["conclusions"] + "\n\nNever imply " + never)
        assert generated.endswith(expected)
        assert generated.count(CONTRACT["intro"]) == 1
        assert generated.count(CONTRACT["conclusions"]) == 1


def test_every_generated_skill_has_exact_evidence_and_no_added_claims():
    checked = 0
    for slug in package.data.studio_slugs():
        if slug == package.REFERENCE:
            continue
        for path in (ROOT / "solutions" / slug / "studio/agent/skills").glob("*/SKILL.md"):
            text = path.read_text()
            assert "## Required evidence\n\n" + CONTRACT["intro"] + "\n\n" in text, path
            assert text.count(CONTRACT["conclusions"]) == 1, path
            assert package.LEGACY_EVIDENCE_CONCLUSIONS not in text, path
            assert re.search(r"(?m)^- .+", text.split("## Required evidence\n\n", 1)[1]), path
            checked += 1
    assert checked > 200


def test_multi_case_skill_keeps_each_phrase_set_scoped_to_its_prompt():
    inputs = package.load_inputs("building-permit-processing")
    path = next(path for path in inputs.skills if "intake-triage" in path.parent.name)
    text = package.skill_for(path, inputs)
    assert "only to the matching request" in text
    by_id = {case["id"]: case for case in inputs.cases}
    for case_id in ("BPP-02", "BPP-03"):
        case = by_id[case_id]
        expected = "For: " + case["prompt"] + "\n\n" + "\n".join("- " + phrase for phrase in case["must_include"])
        assert expected in text


def test_evidence_guard_is_idempotent_for_an_existing_evidence_section():
    inputs = package.load_inputs("emission-tracking")
    path = inputs.skills[0]
    text = package.skill_for(path, inputs)
    assert package.exact_skill_evidence(text, path, inputs) == text


def test_prior_conclusion_guard_is_replaced_not_duplicated():
    inputs = package.load_inputs("emission-tracking")
    path = inputs.skills[0]
    current = package.skill_for(path, inputs)
    previous = current.replace(CONTRACT["conclusions"], package.LEGACY_EVIDENCE_CONCLUSIONS)
    assert package.exact_skill_evidence(previous, path, inputs) == current
    assert "simple arithmetic on those figures that you label as computed" in current
    assert "covers, closes, exceeds, offsets or is sufficient for another" in current
    assert "do not rank or recommend options" in current


@pytest.mark.parametrize("missing", ["intro", "conclusions"])
def test_evidence_contract_oracle_detects_controlled_mutations(missing):
    inputs = package.load_inputs("emission-tracking")
    text = package.skill_for(inputs.skills[0], inputs).replace(CONTRACT[missing], "MUTATED", 1)
    with pytest.raises(AssertionError):
        assert CONTRACT["intro"] in text and CONTRACT["conclusions"] in text
