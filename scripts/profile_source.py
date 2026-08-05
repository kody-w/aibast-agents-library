#!/usr/bin/env python3
"""Source scout — learn a repository's shape before aggregating from it.

Every skill repository is laid out differently. One keeps skills in `skills/`,
another in `src/content/guides/`, another one file per directory with the body
in `SKILL.md` and the metadata in a sibling JSON. Aggregating before you know
which is guessing, and a crawler that guesses fails in the worst way: it
silently returns fewer skills than the repository holds and nobody notices,
because "0 found" and "3 found" look equally plausible from outside.

So aggregation is gated on a **locked shape**. This scout walks a repository,
works out where its skills live and what their frontmatter looks like, records
the answer with its evidence, and writes it to `sentinel/sources/<id>.json`.
`crawl_skills.py` refuses to aggregate a source with no locked shape.

Same two-layer design as the rest of Sentinel:

  * The deterministic pass reads the repository tree, clusters candidate files
    by directory, and measures — how many files, which frontmatter keys, how
    consistently. Reproducible, no model, no guessing.
  * The interpretive pass is a packet: a model looks at the evidence and the
    ambiguous cases and states the mapping to RAPP fields. Its answer is
    absorbed with attribution, exactly like any other resident.

A shape with only the deterministic half is `provisional` — usable, but it
says so. A shape a model has confirmed is `locked`.

Usage:
    python3 scripts/profile_source.py microsoft/cat-agent-skills
    python3 scripts/profile_source.py owner/repo --id my-source
    python3 scripts/profile_source.py --check          # every source is locked
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SHAPES_DIR = REPO_ROOT / "sentinel" / "sources"
SOURCES = REPO_ROOT / "sources.json"

SCHEMA = "rapp-source-shape/1.0"
SCOUT_VERSION = "1.0.0"
USER_AGENT = "aibast-source-scout"

# Files every repository has that are never skills.
FURNITURE = re.compile(
    r"(^|/)(readme|contributing|security|support|changelog|license|notice|"
    r"code_of_conduct|authors|governance|maintainers|roadmap)\.md$", re.I)
DOC_DIRS = re.compile(r"^(\.github|docs?|website|site|blog|examples?|tests?)/", re.I)

# A directory is a skill home if enough of its .md files look like skills.
MIN_FILES = 3
MIN_FRONTMATTER_RATIO = 0.5


def gh(url: str) -> dict | list | None:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urllib.request.urlopen(
                urllib.request.Request(url, headers=headers), timeout=45) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
        print(f"[scout] {url} failed: {exc}", file=sys.stderr)
        return None


def raw(repo: str, branch: str, path: str) -> str:
    url = f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"
    try:
        with urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": USER_AGENT}),
                timeout=45) as r:
            return r.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError):
        return ""


def frontmatter_keys(text: str) -> list[str]:
    if not text.startswith("---"):
        return []
    end = text.find("\n---", 3)
    if end == -1:
        return []
    keys = []
    for line in text[3:end].splitlines():
        line = line.strip()
        if line and ":" in line and not line.startswith("#") and not line.startswith("-"):
            keys.append(line.split(":", 1)[0].strip())
    return keys


def profile(repo: str, source_id: str, sample: int) -> dict:
    meta = gh(f"https://api.github.com/repos/{repo}")
    if not meta:
        raise SystemExit(f"cannot read {repo} — is it public?")
    branch = meta.get("default_branch", "main")

    tree = gh(f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1")
    if not tree:
        raise SystemExit(f"cannot read the tree of {repo}")
    if tree.get("truncated"):
        print("[scout] the tree was truncated; the shape is measured from a "
              "partial listing and should be re-scouted with a token",
              file=sys.stderr)

    md = [n["path"] for n in tree.get("tree", [])
          if n.get("type") == "blob" and n["path"].lower().endswith(".md")
          and not FURNITURE.search(n["path"])]

    # Cluster by parent directory: a skill collection lives together.
    by_dir: dict[str, list[str]] = defaultdict(list)
    for p in md:
        by_dir[str(Path(p).parent)].append(p)

    candidates = []
    for directory, files in sorted(by_dir.items(), key=lambda kv: -len(kv[1])):
        if len(files) < MIN_FILES:
            continue
        probe = files[:sample]
        keys_seen, with_fm = Counter(), 0
        for path in probe:
            keys = frontmatter_keys(raw(repo, branch, path))
            if keys:
                with_fm += 1
                keys_seen.update(keys)
        ratio = with_fm / len(probe) if probe else 0
        candidates.append({
            "directory": directory,
            "glob": (f"{directory}/*.md" if directory != "." else "*.md"),
            "file_count": len(files),
            "sampled": len(probe),
            "frontmatter_ratio": round(ratio, 2),
            "frontmatter_keys": [k for k, _ in keys_seen.most_common(12)],
            "looks_like_docs": bool(DOC_DIRS.match(directory + "/")),
            "examples": probe[:3],
        })

    # The skill home is the largest cluster whose files actually carry
    # frontmatter. Size alone would pick a docs folder every time.
    ranked = sorted(
        [c for c in candidates if c["frontmatter_ratio"] >= MIN_FRONTMATTER_RATIO],
        key=lambda c: (-c["file_count"], c["looks_like_docs"]))
    primary = ranked[0] if ranked else (candidates[0] if candidates else None)

    lic = gh(f"https://api.github.com/repos/{repo}/license") or {}
    spdx = ((lic.get("license") or {}).get("spdx_id") or "").strip()

    # Map observed frontmatter onto the RAPP manifest, where the name is
    # unambiguous. Anything else is left for the interpretive pass rather than
    # guessed — a wrong mapping corrupts every skill aggregated afterwards.
    OBVIOUS = {"name": "name", "title": "display_name", "display_name": "display_name",
               "description": "description", "summary": "description",
               "version": "version", "author": "author", "tags": "tags",
               "keywords": "tags", "category": "category", "license": "source_license"}
    observed = primary["frontmatter_keys"] if primary else []
    mapping = {k: OBVIOUS[k] for k in observed if k in OBVIOUS}
    unmapped = [k for k in observed if k not in OBVIOUS]

    return {
        "schema": SCHEMA,
        "scout_version": SCOUT_VERSION,
        "source_id": source_id,
        "repo": repo,
        "default_branch": branch,
        "profiled": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "provisional",
        "status_note": (
            "Measured, not confirmed. The deterministic pass found this shape; a "
            "model has not yet checked it. Aggregation may proceed, and the "
            "provisional status travels with every skill taken from here."
        ),
        "license": {"spdx": spdx, "url": lic.get("html_url")},
        "shape": {
            "skill_glob": primary["glob"] if primary else None,
            "skill_directory": primary["directory"] if primary else None,
            "expected_count": primary["file_count"] if primary else 0,
            "frontmatter_ratio": primary["frontmatter_ratio"] if primary else 0,
            "content_url_template":
                (f"https://raw.githubusercontent.com/{repo}/{branch}/"
                 f"{primary['directory']}/{{slug}}.md" if primary else None),
            "field_mapping": mapping,
            "unmapped_fields": unmapped,
        },
        "evidence": {
            "markdown_files_total": len(md),
            "clusters_considered": candidates[:8],
            "why_this_cluster": (
                "largest directory whose files carry frontmatter at least "
                f"{int(MIN_FRONTMATTER_RATIO * 100)}% of the time"
                if ranked else "no cluster carried frontmatter; this is a guess "
                               "and the shape should not be trusted until confirmed"),
        },
        "confirmation_packet": {
            "schema": "rapp-sentinel-packet/1.0",
            "resident": "source-shape",
            "kind": "interpretive",
            "authority": "blocking",
            "lens": "Is this actually where this repository keeps its skills?",
            "prompt": (
                "You are confirming the shape of a skill repository before anything "
                "is aggregated from it. You are given the candidate clusters found in "
                "its tree, with file counts, frontmatter ratios and example paths. "
                "Decide which cluster holds the repository's SKILLS, as opposed to its "
                "documentation, its website content, or its tests. Then map its "
                "frontmatter fields onto the RAPP manifest fields (name, display_name, "
                "description, version, author, tags, category, source_license), leaving "
                "out any you cannot map confidently — a wrong mapping corrupts every "
                "skill taken from this source. Return JSON: {skill_directory: string, "
                "skill_glob: string, confident: boolean, field_mapping: object, "
                "unmapped_fields: [string], reasoning: string, teachable: string}."
            ),
            "evidence_ref": "evidence.clusters_considered",
        },
    }


def cmd_check() -> int:
    """Every configured source must have a shape on file before it is crawled."""
    if not SOURCES.is_file():
        print("[scout] no sources.json")
        return 0
    cfg = json.loads(SOURCES.read_text(encoding="utf-8"))
    missing, provisional = [], []
    for src in cfg.get("sources", []):
        sid = src["id"]
        shape = SHAPES_DIR / f"{sid}.json"
        if not shape.is_file():
            missing.append(sid)
            continue
        doc = json.loads(shape.read_text(encoding="utf-8"))
        if doc.get("status") != "locked":
            provisional.append(sid)

    for sid in missing:
        print(f"  FAIL {sid}: no locked shape — run "
              f"`python3 scripts/profile_source.py <owner/repo> --id {sid}` "
              "before aggregating from it", file=sys.stderr)
    if provisional:
        print(f"[scout] provisional (measured, not model-confirmed): "
              f"{', '.join(provisional)}")
    print(f"[scout] {len(cfg.get('sources', []))} source(s), "
          f"{len(missing)} without a shape")
    return 1 if missing else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("repo", nargs="?", help="owner/repo to scout")
    ap.add_argument("--id", help="source id (default: the repo name)")
    ap.add_argument("--sample", type=int, default=8,
                    help="files to open per cluster when measuring frontmatter")
    ap.add_argument("--check", action="store_true",
                    help="fail if any configured source has no shape on file")
    args = ap.parse_args()

    if args.check:
        return cmd_check()
    if not args.repo:
        ap.error("give a repo to scout, or --check")

    source_id = args.id or args.repo.split("/")[-1]
    doc = profile(args.repo, source_id, args.sample)

    SHAPES_DIR.mkdir(parents=True, exist_ok=True)
    out = SHAPES_DIR / f"{source_id}.json"
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    shape = doc["shape"]
    print(f"[scout] {args.repo}: skills look like {shape['skill_glob']} "
          f"({shape['expected_count']} files, frontmatter on "
          f"{int(shape['frontmatter_ratio'] * 100)}%)")
    if shape["unmapped_fields"]:
        print(f"[scout] unmapped frontmatter (needs the model): "
              f"{', '.join(shape['unmapped_fields'][:6])}")
    print(f"[scout] wrote {out.relative_to(REPO_ROOT)} — status PROVISIONAL until "
          "a model confirms it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
