#!/usr/bin/env python3
"""Toasted skills: one file that is both the instructions and the code.

A skill and its script drift. The reference implementation this pattern came
from says so in its own docstring — "keep the skill instructions and this
script in sync" — which is a maintenance instruction, and maintenance
instructions are what get skipped. The moment the prose and the Python disagree,
a model reading the prose and a brainstem running the Python do different
things, and nothing tells you.

A toasted skill removes the seam. The Python lives INSIDE the skill.md, in a
fenced block the converter treats as opaque payload:

    skill.md --extract--> agent.py     exactly the bytes in the block
    agent.py --toast----> skill.md     exactly the file back again

Both directions are byte-exact, so there is nothing to keep in sync — there is
only one artifact. A model reads the markdown and follows the steps; a brainstem
extracts the Python and registers a tool; the determinism a model cannot give
you comes from the same file the model just read.

WHY BYTES AND NOT A RENDERING. The older mirror DERIVED agent.py from prose. A
derivation is a lossy guess: the comments, the constants and the docstring the
author wrote are gone, so the round trip cannot return the original. This keeps
the author's Python verbatim and gates the round trip, so "lossless" is measured
rather than asserted.

Usage:
    python3 scripts/toast_skill.py toast agents/.../foo_agent.py   # py  -> skill.md
    python3 scripts/toast_skill.py extract skills/foo.skill.md     # md  -> agent.py
    python3 scripts/toast_skill.py verify skills/foo.skill.md      # round trip
    python3 scripts/toast_skill.py verify-all
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills" / "toasted"
FENCE = "```python"
# The block is addressed by a marker, not by position: a skill may show other
# Python in its prose, and only the payload may be extracted.
BEGIN = "<!-- rapp:agent.py -->"
END = "<!-- /rapp:agent.py -->"
SCHEMA = "rapp-toasted-skill/1.0"


def manifest_of(source: str) -> dict:
    """Read __manifest__ out of the agent without importing it."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "__manifest__":
                    try:
                        return ast.literal_eval(node.value)
                    except Exception:                          # noqa: BLE001
                        return {}
    return {}


def docstring_of(source: str) -> str:
    try:
        return (ast.get_docstring(ast.parse(source)) or "").strip()
    except SyntaxError:
        return ""


def operations_of(source: str) -> list[str]:
    m = re.search(r'"operations"\s*:\s*\[(.*?)\]', source, re.S)
    return re.findall(r'"([^"]+)"', m.group(1)) if m else []


def toast(py_path: Path) -> str:
    """agent.py -> a single skill.md carrying it verbatim."""
    source = py_path.read_text(encoding="utf-8")
    man = manifest_of(source)
    doc = docstring_of(source)
    name = man.get("name") or f"@local/{py_path.stem}"
    display = man.get("display_name") or py_path.stem.replace("_", " ").title()
    desc = man.get("description") or (doc.splitlines()[0] if doc else "")
    ops = operations_of(source)
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()

    front = {
        "schema": SCHEMA,
        "name": name,
        "version": man.get("version", "1.0.0"),
        "display_name": display,
        "description": desc,
        "author": man.get("author", "AIBAST"),
        "tags": man.get("tags", []),
        "category": man.get("category", "general"),
        "requires_env": man.get("requires_env", []),
        "python_sha256": digest,
        "python_filename": py_path.name,
    }
    fm = ["---"]
    for k, v in front.items():
        fm.append(f"{k}: {json.dumps(v) if isinstance(v, (list, dict)) else v}")
    fm.append("---")

    body = [
        "",
        f"# {display}",
        "",
        "> **Toasted skill.** The instructions below and the Python at the end of",
        "> this file are one artifact. A model can read this and follow the steps;",
        "> a brainstem can extract the Python and register it as a tool. There is",
        "> no second file to keep in sync, because there is no second file.",
        "",
        "## What it does",
        "",
        desc or "See the implementation notes below.",
        "",
    ]
    if doc and doc != desc:
        body += ["## How it works", "", doc, ""]
    if ops:
        body += ["## Operations", "",
                 "Call the tool with `operation` set to one of:", ""]
        body += [f"- `{o}`" for o in ops]
        body += [""]
    if front["requires_env"]:
        body += ["## Configuration", "",
                 "Set these in the environment before running:", ""]
        body += [f"- `{e}`" for e in front["requires_env"]]
        body += [""]
    body += [
        "## Run it without a brainstem",
        "",
        "Extract the Python from this file and run it directly:",
        "",
        "```bash",
        f"python3 scripts/toast_skill.py extract {name.split('/')[-1]}.skill.md",
        f"python3 {py_path.name}",
        "```",
        "",
        "## The implementation",
        "",
        "This block is the agent, verbatim. It is extracted byte for byte — the",
        "digest in the frontmatter is checked on the way out, so a file that has",
        "been edited in transit fails rather than runs.",
        "",
        BEGIN,
        FENCE,
        source.rstrip("\n"),
        "```",
        END,
        "",
    ]
    return "\n".join(fm + body)


def extract(md_path: Path) -> tuple[str, dict]:
    """skill.md -> the exact Python it carries."""
    text = md_path.read_text(encoding="utf-8")
    front = {}
    if text.startswith("---"):
        end = text.index("\n---", 3)
        for line in text[3:end].splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                front[k.strip()] = v.strip()

    i = text.find(BEGIN)
    j = text.find(END)
    if i == -1 or j == -1:
        raise SystemExit(f"{md_path.name}: no toasted payload")
    block = text[i + len(BEGIN):j]
    m = re.search(r"```python\n(.*)\n```", block, re.S)
    if not m:
        raise SystemExit(f"{md_path.name}: payload is not a python fence")
    source = m.group(1) + "\n"

    want = front.get("python_sha256")
    got = hashlib.sha256(source.encode("utf-8")).hexdigest()
    if want and want != got:
        raise SystemExit(f"{md_path.name}: digest mismatch — the Python was edited "
                         f"in transit\n  frontmatter {want}\n  actual      {got}")
    return source, front


def verify(md_path: Path) -> bool:
    """Extract, re-toast, and require the markdown back byte for byte."""
    source, front = extract(md_path)
    tmp = REPO_ROOT / ".toast-verify.py"
    tmp.write_text(source, encoding="utf-8")
    try:
        # Re-toast under the original filename so the round trip is fair.
        original = front.get("python_filename", tmp.name)
        holder = tmp.with_name(original)
        tmp.replace(holder)
        again = toast(holder)
        holder.unlink(missing_ok=True)
    except Exception:                                          # noqa: BLE001
        tmp.unlink(missing_ok=True)
        raise
    return again == md_path.read_text(encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("command", choices=["toast", "extract", "verify", "verify-all"])
    ap.add_argument("path", nargs="?")
    ap.add_argument("--out")
    args = ap.parse_args()

    if args.command == "verify-all":
        mds = sorted(SKILLS_DIR.glob("*.skill.md"))
        if not mds:
            print(f"[toast] no toasted skills in {SKILLS_DIR.relative_to(REPO_ROOT)}")
            return 0
        bad = []
        for m in mds:
            ok = verify(m)
            print(f"  {'PASS' if ok else 'FAIL'}  {m.name}")
            if not ok:
                bad.append(m.name)
        print(f"[toast] {len(mds) - len(bad)}/{len(mds)} round-trip byte-exact")
        return len(bad)

    if not args.path:
        print("[toast] a path is required", file=sys.stderr)
        return 2
    p = Path(args.path)
    if not p.is_absolute():
        p = REPO_ROOT / p

    if args.command == "toast":
        md = toast(p)
        SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        man = manifest_of(p.read_text(encoding="utf-8"))
        slug = (man.get("name") or p.stem).split("/")[-1]
        out = Path(args.out) if args.out else SKILLS_DIR / f"{slug}.skill.md"
        out.write_text(md, encoding="utf-8")
        print(f"[toast] {out.relative_to(REPO_ROOT)}  "
              f"({len(md.encode()) // 1024} KB, python embedded)")
        return 0

    if args.command == "extract":
        source, front = extract(p)
        out = Path(args.out) if args.out else REPO_ROOT / front.get(
            "python_filename", p.stem.replace(".skill", "") + ".py")
        out.write_text(source, encoding="utf-8")
        print(f"[toast] {out.relative_to(REPO_ROOT)}  digest verified")
        return 0

    ok = verify(p)
    print(f"[toast] {'round trip is byte-exact' if ok else 'ROUND TRIP LOST BYTES'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
