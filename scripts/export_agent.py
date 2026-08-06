#!/usr/bin/env python3
"""Export a converted RAPP skill.md as its mirrored agent.py.

`skill.md` and `agent.py` are not two products. They are **two projections of
one contract** — the same manifest, the same deterministic layer, the same
procedure — rendered for two runtimes:

    skill.md   a model reads it and follows the steps
    agent.py   a brainstem registers it and calls it as a tool

Publishing only one of them hides the property that makes the format worth
adopting. An outside skill arrives as prose with no manifest and no stated
contract; it leaves this pipeline as a matched pair where the manifest is
identical in both and neither can drift from the other, because the `.py` is
generated from the `.md` and the gate re-derives it.

Generation is deterministic and lossless in the direction that matters: every
manifest field is copied, not paraphrased, and the full skill body is embedded
so the exported file is genuinely single-file. Re-running produces a
byte-identical result, so `--check` is a drift test.

Output: skills/<namespace>/<slug>.py, beside its skill.md.

Usage:
    python3 scripts/export_agent.py
    python3 scripts/export_agent.py --only accessibility_pass
    python3 scripts/export_agent.py --check     # fail if any export has drifted
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO_ROOT / "skills"

MANIFEST_SCHEMA = "rapp-agent/1.0"


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    meta: dict = {}
    for line in text[3:end].splitlines():
        line = line.strip()
        if not line or ":" not in line or line.startswith("#"):
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            meta[k] = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
        else:
            meta[k] = v.strip("'\"")
    return meta, text[end + 4:].lstrip("\n")


def class_name(slug: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", slug)
    name = "".join(p[:1].upper() + p[1:] for p in parts if p)
    if not name or name[0].isdigit():
        name = "Skill" + name
    return name + "Agent"


def py_literal(value, indent: int = 4) -> str:
    """JSON is a subset of Python literals for the types a manifest carries."""
    return json.dumps(value, indent=indent, ensure_ascii=False)


def export(skill_path: Path) -> str:
    meta, body = split_frontmatter(skill_path.read_text(encoding="utf-8"))
    ref = meta.get("name") or f"@aggregated/{skill_path.stem}"
    slug = ref.split("/")[-1]
    display = meta.get("display_name") or slug
    description = meta.get("description", "")
    license_id = meta.get("source_license", "")
    source_url = meta.get("source_url", "")
    converted_from = meta.get("converted_from", "an upstream project")
    author = meta.get("author", converted_from)

    tags = meta.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]

    # The description a model routes on must describe what CALLING this returns,
    # not what following the procedure eventually achieves. The agent hands back
    # the procedure; it is not itself the accessibility fixer, the chart
    # renderer, or whatever the skill ultimately produces. Saying otherwise
    # would be exactly the misrepresentation our own review rubric fails.
    agent_description = (
        f"Returns the verified RAPP procedure for: {description} "
        f"Call this to obtain the full step-by-step contract (inputs, outputs, "
        f"verification) and then carry out those steps."
    )

    manifest = {
        "schema": MANIFEST_SCHEMA,
        "name": ref,
        "version": meta.get("version", "1.0.0"),
        "display_name": display,
        "description": agent_description,
        "author": author,
        "tags": list(tags)[:8],
        "category": meta.get("category", "aggregated"),
        "quality_tier": "aggregated",
        "requires_env": meta.get("requires_env") or [],
        "dependencies": ["@rapp/basic-agent"],
        "mirrors": f"{slug}.md",
        "source_url": source_url,
        "source_license": license_id,
        "converted_from": converted_from,
    }

    # Embedded so the export is genuinely one file. Two things in real skill
    # bodies break a naive triple-quoted literal, and both are silent until the
    # file is imported: a backslash (Windows paths, regex, escaped table pipes)
    # is read as a Python escape, and an embedded `"""` closes the literal
    # early. Escape backslashes FIRST — doing it after would double the
    # backslashes this very step introduces.
    safe_body = body.rstrip().replace("\\", "\\\\").replace('"""', '\\"\\"\\"')

    return f'''"""
{display} — RAPP agent, mirrored from {slug}.md

This file is GENERATED from its skill.md by scripts/export_agent.py and is one
half of a matched pair. The manifest below and the procedure embedded further
down are identical to the ones in the .md; the only difference is the runtime:
a model reads the .md, a brainstem registers this .py and calls it as a tool.

Do not edit this file. Edit {slug}.md and re-run the exporter — the gate
re-derives this file and fails if the two have drifted apart.

Redistributed from {converted_from} under {license_id or "its upstream licence"}
with attribution. Original author: {author}.
Origin: {source_url}
"""

# ===============================================================
# RAPP AGENT MANIFEST - Do not remove. Used by registry builder.
# ===============================================================
__manifest__ = {py_literal(manifest)}
# ===============================================================

try:  # cloud layout (agents package)
    from agents.basic_agent import BasicAgent
except ImportError:  # local brainstem / standalone layout
    import os
    import sys

    sys.path.insert(0, os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..",
        "agents", "@aibast-agents-library", "templates"))
    from basic_agent import BasicAgent


# The skill body, embedded verbatim. This is what makes the export single-file:
# the procedure travels with the agent rather than being fetched at call time.
SKILL_PROCEDURE = """{safe_body}
"""

SKILL_REF = {json.dumps(ref)}
SKILL_LICENSE = {json.dumps(license_id)}
SKILL_SOURCE = {json.dumps(source_url)}


class {class_name(slug)}(BasicAgent):
    """Delivers a verified RAPP procedure as a callable tool.

    Inputs — none required. `context` optionally narrows the returned
        procedure to a stated situation; it is echoed back, never invented.
    Output — the full skill procedure as text: inputs, outputs, and the
        verification step the caller must perform before reporting success.
    Verification — the caller confirms the artifact named by the procedure
        exists and matches what was asked. This agent returns instructions; it
        does not perform the work described in them, and it never reports
        success on the caller's behalf.
    Configuration — none. The procedure is embedded in this file.
    """

    def __init__(self):
        self.name = {json.dumps(display)}
        self.metadata = {{
            "name": self.name,
            "description": __manifest__["description"],
            "parameters": {{
                "type": "object",
                "properties": {{
                    "context": {{
                        "type": "string",
                        "description": (
                            "Optional. The specific situation the procedure is "
                            "being applied to, echoed back with the steps — for "
                            "example 'a 40-slide deck for an external customer'."
                        ),
                    }}
                }},
                "required": [],
            }},
        }}
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs):
        context = (kwargs.get("context") or "").strip()
        header = [
            f"# {{self.name}} — RAPP procedure",
            "",
            f"Source: {{SKILL_REF}} · redistributed under {{SKILL_LICENSE}} "
            f"with attribution ({{SKILL_SOURCE}}).",
        ]
        if context:
            header += ["", f"**Applied to:** {{context}}"]
        header += [
            "",
            "Follow the steps below exactly. Where a step names an input you "
            "do not have, say so and stop rather than guessing, and complete "
            "the verification step before reporting success.",
            "",
            "---",
            "",
        ]
        return "\\n".join(header) + SKILL_PROCEDURE
'''


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", help="export one skill by file stem")
    ap.add_argument("--check", action="store_true",
                    help="fail if any export is missing or has drifted")
    args = ap.parse_args()

    skills = sorted(SKILLS_ROOT.rglob("*.md")) if SKILLS_ROOT.is_dir() else []
    if args.only:
        skills = [p for p in skills if args.only in p.stem]
    if not skills:
        print(f"[export-agent] nothing matched {args.only!r}", file=sys.stderr)
        return 1

    written, drifted = 0, []
    for skill in skills:
        out = skill.with_suffix(".py")
        text = export(skill)
        if args.check:
            if not out.is_file():
                drifted.append(f"{out.relative_to(REPO_ROOT)} is missing")
            elif out.read_text(encoding="utf-8") != text:
                drifted.append(f"{out.relative_to(REPO_ROOT)} has drifted from its skill.md")
            continue
        if not out.is_file() or out.read_text(encoding="utf-8") != text:
            out.write_text(text, encoding="utf-8")
            written += 1

    if args.check:
        for d in drifted:
            print(f"  FAIL {d}", file=sys.stderr)
        print(f"[export-agent] checked {len(skills)} pair(s), {len(drifted)} drifted")
        return 1 if drifted else 0

    print(f"[export-agent] {len(skills)} skill.md / agent.py pairs, {written} written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
