#!/usr/bin/env python3
"""Stage an offline gallery workshop; preview by default, persist only with --write."""

import argparse
import ast
import difflib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent_to_package

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = Path("agents/@aibast-agents-library")
KNOWN_VERTICALS = {
    "contract-compliance-reviewer": "professional_services",
    "invoice-processing": "general",
    "team-ideas-board": "general",
}
FALLBACK = '''try:
    from basic_agent import BasicAgent
except ImportError:
    try:  # inside a Brainstem the kernel also provides agents.basic_agent
        from agents.basic_agent import BasicAgent
    except ImportError:  # in the library tree, beside the other templates
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
        from basic_agent import BasicAgent'''
TWO_LEVEL = '''try:
    from basic_agent import BasicAgent
except ImportError:
    from agents.basic_agent import BasicAgent'''
TODO = "TODO (authored)"


def normalized_source(source, vertical):
    if FALLBACK not in source:
        if source.count(TWO_LEVEL) != 1:
            raise ValueError("unrecognized BasicAgent import; cannot apply the templates fallback")
        source = source.replace(TWO_LEVEL, "import os\nimport sys\n\n" + FALLBACK, 1)
    tree = ast.parse(source)
    manifest = next(
        (node.value for node in tree.body if isinstance(node, ast.Assign)
         and any(isinstance(target, ast.Name) and target.id == "__manifest__"
                 for target in node.targets)),
        None,
    )
    if not isinstance(manifest, ast.Dict):
        raise ValueError("agent has no literal __manifest__ dictionary")
    category = next((value for key, value in zip(manifest.keys, manifest.values)
                     if isinstance(key, ast.Constant) and key.value == "category"), None)
    if category is None:
        raise ValueError("agent manifest has no category")
    lines = source.splitlines(keepends=True)
    start = sum(len(line.encode("utf-8")) for line in lines[:category.lineno - 1]) + category.col_offset
    end = sum(len(line.encode("utf-8")) for line in lines[:category.end_lineno - 1]) + category.end_col_offset
    encoded = source.encode("utf-8")
    return (encoded[:start] + json.dumps(vertical).encode() + encoded[end:]).decode("utf-8")


def resolved_source(source, existing, notices):
    if not re.search(r"^(?:<<<<<<<|=======|>>>>>>>)", source, re.M):
        return source
    conflict = re.compile(r"^<<<<<<<[^\n]*\n(.*?)^=======\n(.*?)^>>>>>>>[^\n]*\n", re.M | re.S)
    parts, last = [], 0
    for match in conflict.finditer(source):
        parts += [re.escape(source[last:match.start()]),
                  "(?:" + re.escape(match[1]) + "|" + re.escape(match[2]) + ")"]
        last = match.end()
    parts.append(re.escape(source[last:]))
    if existing is None or not last or not re.fullmatch("".join(parts), existing):
        raise ValueError("gallery source has unresolved conflicts without an exact existing library resolution")
    if re.search(r"^(?:<<<<<<<|=======|>>>>>>>)", existing, re.M):
        raise ValueError("existing library agent also has unresolved conflicts")
    notices.append("WARNING: gallery source has conflict markers; using the exact existing library resolution.")
    return existing


def load_agent(path, root):
    basic = root / LIBRARY / "templates"
    previous_path = sys.path[:]
    previous_basic = sys.modules.pop("basic_agent", None)
    sys.path.insert(0, str(basic))
    try:
        spec = importlib.util.spec_from_file_location("gallery_workshop_agent", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        classes = [value for value in vars(module).values()
                   if isinstance(value, type) and value.__module__ == module.__name__
                   and callable(getattr(value, "perform", None))]
        if len(classes) != 1:
            raise ValueError(f"expected one agent class, found {len(classes)}")
        agent = classes[0]()
    finally:
        sys.path[:] = previous_path
        sys.modules.pop("basic_agent", None)
        if previous_basic is not None:
            sys.modules["basic_agent"] = previous_basic
    for name in ("INSTRUCTIONS", "OPERATION_GUIDE"):
        if not getattr(module, name, None):
            raise ValueError(f"transfer layer is missing {name}; author it in the agent")
    return module, agent


def case_evidence(text):
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = None
    if isinstance(value, (dict, list)):
        candidates = agent_to_package.json_evidence(value, n=100)
    else:
        rows = [line.strip().strip("|").split("|") for line in text.splitlines()
                if line.lstrip().startswith("|") and not re.fullmatch(r"[\s|:\-]+", line)]
        candidates = [row[0].strip() for row in rows[1:]]
        candidates += re.findall(r"^\s*[-*]\s+\*\*(.+?)\*\*", text, re.M)
        candidates += re.findall(
            r"\b\d{4}-\d{2}-\d{2}(?:T[\d:+.\-Z]+)?\b"
            r"|\b(?=[A-Za-z0-9_-]*\d)[A-Za-z][A-Za-z0-9]*(?:[-_][A-Za-z0-9]+)+\b"
            r"|\b[A-Z]{1,12}\d[\w-]*\b", text
        )
    safe = [item for item in candidates if item and not re.search(
        r"[$\u00a3\u20ac]|\b\d[\d,.]*\s+(?:of|rows?|items?|findings?|shown|records?|invoices?)\b"
        r"|^[+-]?\d[\d,.]*(?:\s*[A-Z]{3})?$", item
    )]
    return list(dict.fromkeys(safe))[:3]


def draft_cases(slug, filename, module, agent, report_only=False):
    cases = []
    prefix = "".join(word[0] for word in slug.split("-")).upper()
    for index, (operation, guide) in enumerate(module.OPERATION_GUIDE.items(), 1):
        if index > 2:
            break
        arguments = {"operation": operation, **(guide.get("args") or {})}
        output = agent.perform(**arguments)
        evidence = case_evidence(output)
        if not evidence and not report_only:
            raise ValueError(f"{operation}: no safe demo evidence in actual perform() output")
        cases.append({
            "id": f"{prefix}-{index:02d}", "persona": "TODO persona",
            "operation": operation, "onepager_bullet": None, "prompt": guide["ask"],
            "arguments": arguments, "must_include": evidence,
            "must_not_include": ["I do not have access", "I cannot help"],
            "expects_agent": agent.name,
        })
    return {
        "solution": module.__manifest__["display_name"],
        "agent": f"@aibast-agents-library/{slug}", "onepager": None,
        "agent_files": [Path(filename).stem],
        "note": f"DRAFT synthetic cases from actual agent output; persona needs authoring. Built on the Copilot Studio Gallery solution {slug}.",
        "cases": cases,
    }


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def keep_authored_procedures(root, generated, notices):
    kept = 0
    pattern = re.compile(r"^## Procedure\n.*?(?=^## |\Z)", re.M | re.S)
    for path, data in generated.items():
        if path.name != "SKILL.md" or not (root / path).exists():
            continue
        authored = pattern.search((root / path).read_text(encoding="utf-8"))
        if authored:
            text = data.decode("utf-8")
            revised = pattern.sub(lambda _: authored[0], text, count=1)
            if revised != text:
                generated[path] = revised.encode("utf-8")
                kept += 1
    if kept:
        notices.append(f"Kept authored Procedure sections in {kept} existing skill(s); evidence regenerated.")


def draft_readme(root, slug, display, agent_path, operations, case_count):
    template = (root / "solutions/invoice-processing/README.md").read_text(encoding="utf-8")
    template = template.split("<!-- scaffold-solution-journey:start -->")[0].rstrip() + "\n"
    template = template.replace("Invoice Processing", display).replace("invoice-processing", slug)
    template = template.replace(
        "agents/@aibast-agents-library/general_stacks/invoice_processing_stack/invoice_ledger_agent.py",
        agent_path.as_posix(),
    )
    scope = (f"## Scope\n\n{TODO}\n\nImplemented operations: "
             + ", ".join(f"`{op}`" for op in operations)
             + f". The draft contains {case_count} persona-language case(s) and {len(operations)} uploadable skill(s).\n\n")
    template = re.sub(r"## Scope\n.*?(?=## Approval boundary)", lambda _: scope, template, flags=re.S)
    template = re.sub(r"## Approval boundary\n.*?(?=## Manual Copilot Studio preparation)",
                      lambda _: f"## Approval boundary\n\n{TODO}\n\n", template, flags=re.S)
    template = template.replace("the `SKILL.md` file", "each `SKILL.md` file")
    return ("DRAFT - authored Scope and Approval boundary required; no live validation claimed.\n\n" + template).encode("utf-8")


def draft_deployment(root, slug, display, agent_path, operations, agent, cases):
    value = json.loads((root / "solutions/invoice-processing/deployment.json").read_text(encoding="utf-8"))

    def clean(item):
        if isinstance(item, dict):
            return {key: clean(child) for key, child in item.items() if not key.startswith("validated_")}
        if isinstance(item, list):
            return [clean(child) for child in item]
        if isinstance(item, str):
            return item.replace("invoice-processing", slug)
        return item

    value = clean(value)
    value.update({
        "name": f"@aibast-agents-library/{slug}", "display_name": display,
        "source_path": agent_path.as_posix(),
        "source_url": "https://raw.githubusercontent.com/microsoft/aibast-agents-library/main/" + agent_path.as_posix(),
        "target_filename": agent_path.name, "expected_tool": agent.name,
        "smoke_test": {key: cases["cases"][0][key] for key in ("prompt", "arguments", "must_include")},
    })
    value["smoke_test"]["must_call"] = agent.name
    value["copilot_studio"].update({
        "operations": list(operations), "manual_skill_count": len(operations),
        "required_connections": [TODO],
    })
    return json_bytes(value)


def plan(root, slug, vertical=None, records=None):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValueError("slug must be a gallery folder name, not a path")
    sources = sorted((root / "federation/copilot-studio-gallery" / slug).glob("*_agent.py"))
    if len(sources) != 1:
        raise ValueError(f"{slug}: expected one gallery agent, found {len(sources)}")
    source = sources[0]
    matches = sorted((root / LIBRARY).glob(f"*_stacks/*/{source.name}"))
    if len(matches) > 1:
        raise ValueError(f"{slug}: ambiguous existing library agent")
    existing = matches[0] if matches else None
    existing_vertical = existing.parent.parent.name.removesuffix("_stacks") if existing else None
    vertical = vertical or existing_vertical or KNOWN_VERTICALS.get(slug)
    if not vertical or not re.fullmatch(r"[a-z][a-z0-9_]*", vertical):
        raise ValueError(f"{slug}: supply --vertical naming an existing <vertical>_stacks folder")
    if not (root / LIBRARY / f"{vertical}_stacks").is_dir():
        raise ValueError(f"{vertical}_stacks does not exist; refusing to invent a vertical")
    if existing and vertical != existing_vertical:
        raise ValueError(f"{slug}: existing library agent is in {existing_vertical}, not {vertical}")
    agent_path = (existing.relative_to(root) if existing else LIBRARY / f"{vertical}_stacks"
                  / (source.stem.removesuffix("_agent") + "_stack") / source.name)
    notices = []
    source_text = resolved_source(source.read_text(encoding="utf-8"),
                                  existing.read_text(encoding="utf-8") if existing else None, notices)
    content = normalized_source(source_text, vertical)
    planned = {agent_path: content.encode("utf-8")}
    solution = Path("solutions") / slug
    case_path = Path("tests/demo_cases") / f"{slug}.json"
    with tempfile.TemporaryDirectory(prefix="gallery-workshop-") as directory:
        temp = Path(directory)
        staged_agent = temp / source.name
        staged_agent.write_text(content, encoding="utf-8")
        module, agent = load_agent(staged_agent, root)
        notices.append(f'metadata.description contains "on file": {"yes" if "on file" in agent.metadata["description"].lower() else "no"} (unchanged)')
        authored_cases = (root / case_path).exists()
        draft = draft_cases(slug, source.name, module, agent, report_only=authored_cases)
        if authored_cases:
            cases = json.loads((root / case_path).read_text(encoding="utf-8"))
            differences = [key for key in ("persona", "prompt", "must_include", "arguments")
                           if [case.get(key) for case in cases["cases"]]
                           != [case.get(key) for case in draft["cases"]]]
            notices.append("Demo cases: kept authored file; draft differences: " + (", ".join(differences) or "none"))
            for case in draft["cases"]:
                if not case["must_include"]:
                    notices.append(f'Demo comparison: {case["operation"]} has no safe automatic evidence; authored must_include retained.')
        else:
            cases = draft
            planned[case_path] = json_bytes(cases)
        command = [
            "python3", "tools/capture_demo_transcripts.py", case_path.as_posix(),
            (solution / "evals/transcripts.json").as_posix(),
            "--agents-dir", str(Path.home() / ".brainstem/src/rapp_brainstem/agents"),
            "--base-url", "http://localhost:7199",
        ]
        notices.append("Transcripts NOT recorded. Live command: " + shlex.join(command))
        if records is None:
            planned[solution / "RECORDS-DRAFT.md"] = (
                f"# {slug} records - DRAFT\n\n"
                "DRAFT: authored, not derived. A person must write the real synthetic records.\n\n"
                "TODO: fictional-data banner, fixed-snapshot records table, and numbered rules.\n"
                "Do not treat this placeholder as knowledge or evidence.\n"
            ).encode("utf-8")
            notices.append("STOP before stage 5: provide --records with human-authored synthetic records.")
            return planned, notices
        snapshot = temp / "records.md"
        snapshot.write_bytes(Path(records).read_bytes())
        package = temp / "package"
        scratch = temp / "scratch"
        scratch.mkdir()
        result = subprocess.run(
            [sys.executable, "-B", str(root / "tools/agent_to_package.py"),
             str(staged_agent), slug, str(package), "--knowledge", str(snapshot)],
            text=True, capture_output=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "TMPDIR": str(scratch)},
        )
        if result.returncode:
            raise ValueError("agent_to_package failed:\n" + result.stdout + result.stderr)
        skills = sorted((package / "manual/skills").glob("*/SKILL.md"))
        if len(skills) != len(module.OPERATION_GUIDE):
            raise ValueError("agent_to_package produced an unexpected skill count")
        for skill in skills:
            text = skill.read_text(encoding="utf-8")
            section = text.split("## Deterministic pilot evidence\n", 1)[-1].split("\n## ", 1)[0]
            if "## Deterministic pilot evidence\n" not in text or not re.search(r"^- `.+`$", section, re.M):
                raise ValueError(f"{skill.name} ({skill.parent.name}): empty evidence section")
        manual = solution / "manual"
        generated = {manual / path.relative_to(package / "manual"): path.read_bytes()
                     for path in sorted((package / "manual").rglob("*")) if path.is_file()}
        keep_authored_procedures(root, generated, notices)
        planned.update(generated)
        if (root / manual).exists():
            for path in (root / manual).rglob("*"):
                if path.is_file() and path.relative_to(root) not in generated:
                    planned[path.relative_to(root)] = None
        for name, builder in (
            ("README.md", lambda: draft_readme(root, slug, module.__manifest__["display_name"],
                                              agent_path, module.OPERATION_GUIDE, len(cases["cases"]))),
            ("deployment.json", lambda: draft_deployment(root, slug, module.__manifest__["display_name"],
                                                        agent_path, module.OPERATION_GUIDE, agent, cases)),
        ):
            if not (root / solution / name).exists():
                planned[solution / name] = builder()
        notices.append(f"Package: {len(skills)} skills; every evidence section is non-empty.")
    return planned, notices


def changes(root, planned):
    return {path: data for path, data in planned.items()
            if ((root / path).read_bytes() if (root / path).exists() else None) != data}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--records", type=Path)
    parser.add_argument("--vertical")
    args = parser.parse_args(argv)
    try:
        planned, notices = plan(ROOT, args.slug, args.vertical, args.records)
        changed = changes(ROOT, planned)
        for notice in notices:
            print(notice)
        for path, data in sorted(changed.items()):
            old = (ROOT / path).read_text(encoding="utf-8") if (ROOT / path).exists() else ""
            new = data.decode("utf-8") if data is not None else ""
            print("".join(difflib.unified_diff(
                old.splitlines(keepends=True), new.splitlines(keepends=True),
                fromfile=f"a/{path}" if (ROOT / path).exists() else "/dev/null",
                tofile=f"b/{path}" if data is not None else "/dev/null",
            )), end="")
        print(f"Diff: {len(changed)} file(s)" if changed else "Diff: EMPTY")
        if args.write:
            for path, data in changed.items():
                target = ROOT / path
                if data is None:
                    target.unlink()
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
            print(f"Wrote {len(changed)} file(s).")
    except (OSError, ValueError, SyntaxError, KeyError) as error:
        parser.exit(1, f"ERROR: {error}\n")


if __name__ == "__main__":
    main()
