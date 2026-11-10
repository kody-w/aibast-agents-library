"""Guards for two defects a bad merge shipped to staging on 2026-11-10: committed conflict markers, and
reference answers whose recorded agent fingerprint no longer matched the agent beside them."""
import hashlib
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
MARKER = re.compile(r"^(<{7} |>{7} |={7}$)", re.M)
TEXT = (".py", ".json", ".md", ".html", ".js", ".css", ".yml", ".yaml", ".sh", ".ps1", ".txt")


def tracked():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [ROOT / p for p in out.splitlines() if p.endswith(TEXT)]


def test_no_conflict_markers_in_tracked_text_files():
    bad = []
    for p in tracked():
        try:
            if MARKER.search(p.read_text(encoding="utf-8")):
                bad.append(str(p.relative_to(ROOT)))
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    assert not bad, f"unresolved merge conflict markers in: {bad}"


def test_reference_answers_match_the_agent_beside_them():
    stale = []
    for ref in sorted((ROOT / "federation").rglob("reference-answers.json")):
        doc = json.loads(ref.read_text())
        agent = ref.parent / doc["agent"]
        if hashlib.sha256(agent.read_bytes()).hexdigest() != doc["agent_sha256"]:
            stale.append(str(ref.relative_to(ROOT)))
    assert not stale, f"re-record with tools/record_reference_answers.py: {stale}"
