#!/usr/bin/env python3
"""Build the Brainstem in one file: brainstem.pyz.

Everything the Brainstem needs rides inside it: the unchanged kernel, the hatch, the pure-Python packages the
kernel imports, and the whole agent library with its catalog. Running it needs a Python and nothing else:
no network, no install, no sign-in. The AI that runs it is the model.

    python3 tools/build_carry.py [out.pyz]        (build time only: this step downloads the pinned packages)
"""
import hashlib, json, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PINS = ["flask==3.1.2", "flask-cors==6.0.1", "requests==2.32.5", "python-dotenv==1.1.1"]
MAIN = '''"""The Brainstem in one file. Run:  python brainstem.pyz tools | ask "<words>" | answer '<answer>' | bring <agent> | chat | thaw <snapshot> | freeze"""
import os, sys, zipfile, contextlib, io
from pathlib import Path
here = Path(os.environ.get("BRAINSTEM_CARRY", "brainstem_carry")).resolve()
stamp = here / ".stamp"
with zipfile.ZipFile(Path(__file__).resolve().parent if not zipfile.is_zipfile(sys.argv[0]) else sys.argv[0]) as z:
    want = z.read("carry/STAMP").decode()
    if not stamp.exists() or stamp.read_text() != want:
        for n in z.namelist():
            if n.startswith("carry/") and not n.endswith("/"):
                t = here / n[len("carry/"):]
                t.parent.mkdir(parents=True, exist_ok=True)
                t.write_bytes(z.read(n))
        stamp.write_text(want)
os.environ.setdefault("HATCH_SOURCE", str(here))
sys.path[:0] = [str(here / "site"), str(here / "docs" / "any-ai")]
sys.dont_write_bytecode = True
import hatch
if not Path("rapp_brainstem", "brainstem.py").exists() and sys.argv[1:2] != ["thaw"]:
    code, out = hatch.get()
    if code:
        import json; print(json.dumps(out)); sys.exit(code)
sys.exit(hatch.main(["brainstem.pyz", *sys.argv[1:]]))
'''


def build(out, brainfreeze=None):
    manifest = json.loads((ROOT / "docs/any-ai/hatch-manifest.json").read_text())
    registry = json.loads((ROOT / "registry.json").read_text())
    files = {"registry.json": ROOT / "registry.json", "docs/any-ai/hatch-manifest.json": ROOT / "docs/any-ai/hatch-manifest.json"}
    for f in ("hatch.py", "plug.py"):
        files[f"docs/any-ai/{f}"] = ROOT / "docs/any-ai" / f
    for rel in manifest["files"]:
        files[f"rapp_brainstem/{rel}"] = ROOT / "rapp_brainstem" / rel
    for a in registry["agents"]:
        src = ROOT / a["_file"]
        if hashlib.sha256(src.read_bytes()).hexdigest() != a["_sha256"]:
            sys.exit(f"{a['_file']} does not match the catalog; rebuild the registry first")
        files[a["_file"]] = src
    with tempfile.TemporaryDirectory() as tmp:
        site = Path(tmp) / "site"
        subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--no-compile", "--target", str(site), *PINS], check=True)
        for junk in [*site.rglob("*.so"), *site.rglob("*.pyd"), *site.rglob("__pycache__"), site / "bin"]:
            shutil.rmtree(junk) if junk.is_dir() else junk.unlink(missing_ok=True)
        for f in sorted(site.rglob("*")):
            if f.is_file():
                files["site/" + f.relative_to(site).as_posix()] = f
        if brainfreeze:        # the freezer rides along, unchanged, so a Brainstem can be thawed and frozen with no network
            for f in sorted(Path(brainfreeze).rglob("*.py")) + sorted(Path(brainfreeze).rglob("*.json")):
                files["site/brainfreeze/" + f.relative_to(brainfreeze).as_posix()] = f
        digest = hashlib.sha256()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for name in sorted(files):
                body = files[name].read_bytes()
                digest.update(name.encode() + b"\0" + hashlib.sha256(body).digest())
                z.writestr(zipfile.ZipInfo("carry/" + name, (2020, 1, 1, 0, 0, 0)), body, zipfile.ZIP_DEFLATED)
            z.writestr(zipfile.ZipInfo("carry/STAMP", (2020, 1, 1, 0, 0, 0)), digest.hexdigest())
            z.writestr(zipfile.ZipInfo("__main__.py", (2020, 1, 1, 0, 0, 0)), MAIN)
    return {"file": str(out), "bytes": Path(out).stat().st_size, "kernel_version": manifest["kernel_version"],
            "agents": len(registry["agents"]), "files": len(files), "sha256": hashlib.sha256(Path(out).read_bytes()).hexdigest()}


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--brainfreeze=")]
    freezer = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--brainfreeze=")), None)
    print(json.dumps(build(Path(args[0] if args else "brainstem.pyz"), freezer), indent=1))
