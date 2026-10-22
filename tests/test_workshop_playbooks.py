"""The workshop skill is the one front door; playbooks hold the guidance it fetches at run time."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAYBOOKS = ROOT / "skills" / "playbooks"
SKILLS = [
    ROOT / "skills" / "aibast-easy-mode-copilot" / "SKILL.md",
    ROOT / "skills" / "aibast-easy-mode-brainstem" / "SKILL.md",
]


def indexed_playbooks():
    index = (PLAYBOOKS / "README.md").read_text(encoding="utf-8")
    return re.findall(r"^\| `([^`]+\.md)` \|", index, flags=re.MULTILINE)


def test_every_indexed_playbook_exists_and_every_playbook_is_indexed():
    listed = indexed_playbooks()
    on_disk = sorted(p.name for p in PLAYBOOKS.glob("*.md") if p.name != "README.md")
    assert listed, "the playbook index lists nothing"
    assert sorted(listed) == on_disk


def test_both_workshop_skills_route_through_the_playbook_index():
    for skill in SKILLS:
        text = skill.read_text(encoding="utf-8")
        assert "## Start from what you need" in text
        assert "skills/playbooks/README.md" in text
        assert "build-it-yourself.md" in text
        assert "adapt-and-connect.md" in text
        assert "never promise that a requested workshop will be built" in text


def test_playbooks_keep_customer_data_and_secrets_out():
    for playbook in PLAYBOOKS.glob("*.md"):
        if playbook.name == "README.md":
            continue
        text = " ".join(playbook.read_text(encoding="utf-8").split())
        assert "Never ask for, accept, or store real customer records" in text, playbook.name
        assert "calculated by the agent's code from the data" in text, playbook.name


def test_live_systems_stay_in_copilot_studio_draft():
    text = " ".join((PLAYBOOKS / "adapt-and-connect.md").read_text(encoding="utf-8").split())
    assert "Never store keys, passwords, or tokens in files or chat." in text
    assert "read-only first" in text
    assert "Stay in Draft." in text
    assert "Azure" not in text


def test_every_workshop_offers_the_industry_box_and_keeps_the_standard_prompt():
    quests = sorted((ROOT / "solutions").glob("*/quest.html"))
    assert len(quests) >= 65
    for quest in quests:
        text = quest.read_text(encoding="utf-8")
        assert text.count("data-make-it-yours=") == 2, quest.parent.name
        assert 'const industryKey = "aibast.workshop.industry";' in text, quest.parent.name
        # The printed default stays the standard phrase the skills handle.
        assert re.search(r'id="copilot-build-prompt">Give me .+ using Easy Mode and test it for me\.</pre>', text), quest.parent.name
