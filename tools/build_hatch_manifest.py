"""Build docs/any-ai/hatch-manifest.json: the Brainstem files a hatch fetches, each with its fingerprint.

    python tools/build_hatch_manifest.py          write the manifest
    python tools/build_hatch_manifest.py --check  fail if the manifest is stale
"""
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KERNEL = ROOT / "rapp_brainstem"
OUT = ROOT / "docs" / "any-ai" / "hatch-manifest.json"
FILES = ["brainstem.py", "local_storage.py", "soul.md", "VERSION", "requirements.txt", "agents/basic_agent.py",
         "agents/context_memory_agent.py", "agents/manage_memory_agent.py", "agents/hacker_news_agent.py",
         "agents/rar_rapp_learn_new_agent.py"]


def build():
    files = {f: hashlib.sha256((KERNEL / f).read_bytes()).hexdigest() for f in FILES}
    return json.dumps({"schema": "aibast-hatch-manifest/1.0", "kernel_version": (KERNEL / "VERSION").read_text().strip(),
                       "files": files}, indent=1, sort_keys=True) + "\n"


if __name__ == "__main__":
    want = build()
    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_text() != want:
            sys.exit("docs/any-ai/hatch-manifest.json is stale. Run: python tools/build_hatch_manifest.py")
        print("hatch manifest is current")
    else:
        OUT.write_text(want)
        print(f"wrote {OUT.relative_to(ROOT)}")
