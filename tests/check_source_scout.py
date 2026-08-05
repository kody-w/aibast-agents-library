#!/usr/bin/env python3
"""The source scout must pick a repository's SKILLS, not its documentation.

This is the check that matters most about the scout: size alone would choose a
docs folder in most repositories, and a wrong choice corrupts every skill
aggregated from that source afterwards. Exercised against a synthetic tree
shaped like the repositories we actually meet — no network, so it runs the same
way in CI and on a rate-limited laptop.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import profile_source as ps

# A repository shaped like the ones in the wild: skills live under a content
# path with frontmatter; the biggest .md cluster is documentation without any.
TREE = {"tree": [{"type": "blob", "path": p} for p in [
    "README.md", "CONTRIBUTING.md", "SECURITY.md", ".github/copilot-instructions.md",
    *[f"docs/guide-{i}.md" for i in range(12)],
    *[f"src/content/guides/skill-{i}.md" for i in range(7)],
    "src/content/guides/notes.txt",
]]}
WITH_FM = "---\nname: skill\ndescription: does a thing\nversion: 1.0.0\nweird_field: x\n---\n\n# Skill\n"
NO_FM = "# A documentation page\n\nProse, no manifest.\n"


def fake_gh(url):
    if url.endswith("/license"):
        return {"license": {"spdx_id": "MIT"}, "html_url": "https://example.com/LICENSE"}
    if "/git/trees/" in url:
        return TREE
    return {"default_branch": "main"}


def fake_raw(repo, branch, path):
    return WITH_FM if path.startswith("src/content/guides/") else NO_FM


def main() -> int:
    ps.gh, ps.raw = fake_gh, fake_raw
    doc = ps.profile("owner/repo", "test-source", sample=8)
    shape, problems = doc["shape"], []

    if shape["skill_directory"] != "src/content/guides":
        problems.append(f"picked {shape['skill_directory']!r}; docs/ is larger but "
                        "carries no frontmatter, so it is not the skill home")
    if shape["expected_count"] != 7:
        problems.append(f"counted {shape['expected_count']} skills, expected 7")
    if shape["frontmatter_ratio"] < 1.0:
        problems.append("frontmatter ratio should be 1.0 for this cluster")
    if shape["field_mapping"].get("description") != "description":
        problems.append("obvious frontmatter fields must be mapped")
    if "weird_field" not in shape["unmapped_fields"]:
        problems.append("an unrecognised field must be reported, never guessed at")
    if doc["status"] != "provisional":
        problems.append("a shape no model has confirmed must not claim to be locked")
    if not doc["confirmation_packet"]["prompt"]:
        problems.append("the scout must emit the packet that confirms its guess")
    if doc["license"]["spdx"] != "MIT":
        problems.append("the licence must be resolved from the repository")

    for p in problems:
        print(f"  FAIL {p}", file=sys.stderr)
    if not problems:
        print(f"[scout-test] chose {shape['skill_directory']} over a larger docs/ "
              f"cluster; {len(shape['unmapped_fields'])} field(s) left for the model")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
