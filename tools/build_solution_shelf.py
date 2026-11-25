"""Put every industry solution on the skills shelf as one file: skills/<name>/SKILL.md.

Each file is made from the solution's own agent.py (the one its deployment.json names) and holds
that agent, unchanged, with its SHA-256. The agent file stays the single source: this never edits it.

  python tools/build_solution_shelf.py --converter <rapp_skills.py>   write the shelf (build time only)
  python tools/build_solution_shelf.py --check                        no converter needed: every shelf
                                                                      file still holds its agent, byte for byte
  python tools/build_solution_shelf.py --smoke                        each agent taken OUT of its shelf file
                                                                      answers the solution's test call the same as the original
"""
import argparse, hashlib, importlib.util, json, pathlib, re, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHELF = ROOT / "skills"
MARK = re.compile(r"<!-- agent sha256=([0-9a-f]{64}) -->\n(`{3,})python\n(.*?)\n\2\n<!-- /agent -->", re.S)
FILE = re.compile(r'^  file: "([^"]+)"$', re.M)
NAME = re.compile(r'^name: "?([a-z0-9-]+)"?$', re.M)


def solutions():
    """[(slug, agent path, deployment)] for every solution whose deployment.json names an agent file that exists."""
    found = []
    for path in sorted((ROOT / "solutions").glob("*/deployment.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        source = data.get("source_path") or ""
        if source and (ROOT / source).is_file():
            found.append((path.parent.name, ROOT / source, data))
    return found


def shelf_files():
    """{agent file name: SKILL.md path} for shelf skills that were made from an agent file."""
    out = {}
    for md in sorted(SHELF.glob("*/SKILL.md")):
        text = md.read_text(encoding="utf-8")
        hit = FILE.search(text.split("\n---\n", 1)[0])
        if hit and MARK.search(text):
            out[hit.group(1)] = md
    return out


def agent_inside(md):
    hit = MARK.search(md.read_text(encoding="utf-8"))
    return (hit.group(1), (hit.group(3) + "\n").encode("utf-8")) if hit else (None, None)


def check():
    problems, shelf, seen = [], shelf_files(), set()
    for slug, agent, _ in solutions():
        md = shelf.get(agent.name)
        if md is None:
            problems.append(f"{slug}: no shelf skill for {agent.name}; run with --converter")
            continue
        seen.add(agent.name)
        stated, inside = agent_inside(md)
        real = agent.read_bytes()
        if inside != real or stated != hashlib.sha256(real).hexdigest():
            problems.append(f"{slug}: skills/{md.parent.name}/SKILL.md no longer matches {agent.relative_to(ROOT)}; run with --converter")
        if NAME.search(md.read_text(encoding="utf-8")).group(1) != md.parent.name:
            problems.append(f"{slug}: skill name and folder differ in skills/{md.parent.name}")
    for name in sorted(set(shelf) - seen):
        problems.append(f"skills/{shelf[name].parent.name}: made from {name}, which no solution names any more")
    return problems, len(seen)


def load_agent(path):
    sys.path.insert(0, str(ROOT / "agents" / "@aibast-agents-library" / "templates"))
    spec = importlib.util.spec_from_file_location("shelf_" + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for value in vars(module).values():
        if isinstance(value, type) and value.__module__ == module.__name__ and hasattr(value, "perform"):
            return value()
    raise RuntimeError(f"{path.name}: no agent class")


def smoke():
    """Take each agent OUT of its shelf file and run the solution's own test call against it."""
    problems, passed, shelf = [], 0, shelf_files()
    with tempfile.TemporaryDirectory() as tmp:
        for slug, agent, data in solutions():
            md = shelf.get(agent.name)
            if md is None:
                problems.append(f"{slug}: not on the shelf")
                continue
            copy = pathlib.Path(tmp) / slug.replace("-", "_") / agent.name
            copy.parent.mkdir()
            copy.write_bytes(agent_inside(md)[1])
            call = (data.get("smoke_test") or {}).get("arguments") or {}
            try:
                said, original = str(load_agent(copy).perform(**call)), str(load_agent(agent).perform(**call))
            except Exception as exc:  # noqa: BLE001
                problems.append(f"{slug}: {exc.__class__.__name__}: {exc}")
                continue
            if not said.strip() or said != original:
                problems.append(f"{slug}: the agent from the shelf file answers differently from the library's")
            else:
                passed += 1
    return problems, passed


def build(converter):
    spec = importlib.util.spec_from_file_location("rapp_skills_core", converter)
    core = importlib.util.module_from_spec(spec)
    sys.modules["rapp_skills_core"] = core
    spec.loader.exec_module(core)
    taken = {md.parent.name for md in SHELF.glob("*/SKILL.md")} - {md.parent.name for md in shelf_files().values()}
    wrote = 0
    with tempfile.TemporaryDirectory() as tmp:
        for slug, agent, _ in solutions():
            made = core.toast(agent, pathlib.Path(tmp) / slug)
            ok, why = core.roundtrip(made, pathlib.Path(tmp) / (slug + "-rt"))
            if not ok:
                raise SystemExit(f"{slug}: {why}")
            if made.name in taken:
                raise SystemExit(f"{slug}: skills/{made.name} already belongs to another skill")
            target = SHELF / made.name / "SKILL.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            text = (made / "SKILL.md").read_bytes()
            if not target.exists() or target.read_bytes() != text:
                target.write_bytes(text)
                wrote += 1
    return wrote


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--converter")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    if args.converter:
        print(f"wrote {build(args.converter)} shelf files")
    problems, count = smoke() if args.smoke else check()
    total = len(solutions())
    print(f"{'ran' if args.smoke else 'match'}: {count} of {total}")
    for line in problems:
        print("  " + line)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
