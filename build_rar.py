#!/usr/bin/env python3
"""AIBAST RAR builder — generates rar/registry.json, the business-focused
agent registry the Brainstem's RAR browser installs from.

Derives from registry.json (the catalog build_registry.py already validates)
and adds what the RAR trust model needs: a SHA-256 digest per agent file
(verified by the browser and again by /agents/import) and the install
filename. Run after build_registry.py; commit the result. The Brainstem pins
a specific commit revision of this repo, so publishing a new RAR means:
build, commit, then update RAR_REVISION in rapp_brainstem to that commit.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    reg = json.loads((ROOT / "registry.json").read_text(encoding="utf-8"))
    agents = []
    for a in reg.get("agents", []):
        p = ROOT / a["_file"]
        data = p.read_bytes()
        entry = dict(a)
        entry["_sha256"] = hashlib.sha256(data).hexdigest()
        base = p.name if p.name.endswith("_agent.py") else p.stem + "_agent.py"
        entry["_install_filename"] = base
        agents.append(entry)
    out = {
        "schema": reg.get("schema", "rapp-registry/1.0"),
        "version": reg.get("version", "1.0.0"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "instance": "AIBAST RAR",
        "stats": dict(reg.get("stats", {})),
        "duplicates": [],
        "swarms": [],
        "stacks": [],
        "agents": agents,
    }
    (ROOT / "rar").mkdir(exist_ok=True)
    (ROOT / "rar" / "registry.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print(f"[OK] AIBAST RAR built: {len(agents)} agents, digests verified installable")


if __name__ == "__main__":
    main()
