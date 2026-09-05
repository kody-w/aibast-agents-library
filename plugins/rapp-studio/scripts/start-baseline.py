"""Run the unchanged installed Brainstem with isolated, pinned OOTB test agents/data."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys


PLUGIN = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(source_root: Path, run_dir: Path, scenario: dict) -> dict:
    source_root = source_root.resolve()
    run_dir = run_dir.resolve()
    if run_dir.exists():
        raise FileExistsError(f"refusing to overwrite baseline directory: {run_dir}")
    selected = scenario["source"]["agents"]
    expected = {"ManageMemory", "ContextMemory", "HackerNews", "LearnNew"}
    if {row["tool"] for row in selected} != expected or len(selected) != len(expected):
        raise ValueError("the default baseline requires exactly the four OOTB agents")
    files = {}
    for row in selected + scenario["source"]["supporting_files"]:
        relative = Path(row["path"])
        source = (source_root / relative).resolve()
        if relative.is_absolute() or not source.is_relative_to(source_root):
            raise ValueError(f"source path escapes the selected root: {relative}")
        if not source.is_file() or digest(source) != row["sha256"]:
            raise ValueError(f"source hash does not match the pinned scenario: {relative}")
        files[str(relative)] = source
    soul = source_root / "soul.md"
    if not soul.is_file():
        raise ValueError("the source Brainstem soul.md is missing")
    (run_dir / "agents").mkdir(parents=True)
    (run_dir / "agents" / "__init__.py").write_text("", encoding="utf-8")
    for relative, source in files.items():
        target = run_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    (run_dir / "soul.md").write_bytes(soul.read_bytes())
    (run_dir / "data").mkdir()
    return {
        "agents": [row["tool"] for row in selected],
        "source_sha256": {relative: digest(path) for relative, path in files.items()},
        "soul_sha256": digest(soul),
        "data_dir": str(run_dir / "data"),
    }


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--model", default="auto")
    args = parser.parse_args()
    runtime = args.runtime_root.expanduser().resolve()
    run_dir = args.run_dir.expanduser().resolve()
    kernel = runtime / "brainstem.py"
    if not kernel.is_file():
        raise FileNotFoundError(f"installed Brainstem kernel is missing: {kernel}")
    scenario = json.loads((PLUGIN / "examples/ootb/scenario.json").read_text())
    record = prepare(args.source_root.expanduser(), run_dir, scenario)
    record["kernel_sha256"] = digest(kernel)
    record["runtime_root"] = str(runtime)
    os.environ.update({
        "AGENTS_PATH": str(run_dir / "agents"),
        "SOUL_PATH": str(run_dir / "soul.md"),
        "BRAINSTEM_LAN_MODE": "false",
        "GITHUB_MODEL": args.model,
        "VOICE_MODE": "false",
    })
    sys.path.insert(0, str(runtime))
    sys.path.insert(0, str(run_dir))
    importlib.import_module("agents.basic_agent")
    storage = load("local_storage", run_dir / "local_storage.py")
    storage._DATA_DIR = str(run_dir / "data")
    brainstem = load("brainstem", kernel)
    brainstem._register_shims()
    if Path(brainstem.AGENTS_PATH).resolve() != run_dir / "agents":
        raise RuntimeError("installed Brainstem did not honor isolated AGENTS_PATH")
    if args.model == "auto":
        brainstem._auto_select_default_model()
    loaded = brainstem.load_agents()
    if set(loaded) != set(record["agents"]):
        raise RuntimeError("the isolated baseline did not load exactly the OOTB agent set")
    from werkzeug.serving import make_server

    server = make_server("127.0.0.1", 0, brainstem.app, threaded=True)
    record.update({
        "url": f"http://127.0.0.1:{server.server_port}",
        "pid": os.getpid(),
        "runtime_version": brainstem.VERSION,
        "model": brainstem.MODEL,
        "isolation": "agent files and memory data; not an OS security sandbox",
    })
    (run_dir / "baseline.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8",
    )
    print(json.dumps(record), flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
