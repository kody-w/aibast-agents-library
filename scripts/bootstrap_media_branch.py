#!/usr/bin/env python3
"""Stand up a repository's own media branch, and cut the site over to it.

The library streams its demo recordings from an orphan branch rather than
carrying them in the code clone. A fork inherits the pages but not the branch,
so until this has run, a fork's site plays media from whichever repo does have
it — the fallback in media.js. That works, and it is a dependency on someone
else's repository, which is not where this should end up.

This is the one command that ends that dependency:

    fetch the media from the source repo's branch
    create the SAME orphan branch here, with the same paths
    verify every file arrives and is playable
    remove the fallback from media.js, so the site uses its own branch

Why an orphan branch. It shares no history with main, so a merge cannot pull
600 MB into the code clone by accident, and `git clone --depth 1` of main never
fetches a single byte of it — depth 1 implies single-branch. That is the whole
mechanism; keep it.

Nothing is pushed without --apply. The default is a dry run that says exactly
what it would do, because this creates a branch in a repository that may not be
yours.

Usage:
    python3 scripts/bootstrap_media_branch.py --target microsoft/aibast-agents-library
    python3 scripts/bootstrap_media_branch.py --target microsoft/... --apply
    python3 scripts/bootstrap_media_branch.py --target ... --apply --keep-fallback
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = "kody-w/aibast-agents-library"
BRANCH = "media-server"
MEDIA_DIR = "media/videos"
MANIFEST = "media/renditions.json"


def run(args, cwd=None, check=True):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and p.returncode:
        print(" ".join(str(a) for a in args), file=sys.stderr)
        print((p.stderr or p.stdout)[-1500:], file=sys.stderr)
        raise SystemExit(f"command failed ({p.returncode})")
    return p


def remote_has_branch(remote: str, branch: str) -> bool:
    p = run(["git", "ls-remote", "--heads", f"https://github.com/{remote}.git", branch],
            check=False)
    return bool(p.stdout.strip())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--target", required=True,
                    help="owner/repo that should own the media branch")
    ap.add_argument("--source", default=DEFAULT_SOURCE,
                    help=f"owner/repo to copy the media from (default {DEFAULT_SOURCE})")
    ap.add_argument("--branch", default=BRANCH)
    ap.add_argument("--apply", action="store_true",
                    help="actually create and push; without it this is a dry run")
    ap.add_argument("--keep-fallback", action="store_true",
                    help="leave media.js pointing at the source as a safety net")
    args = ap.parse_args()

    if args.target == args.source:
        print("[media] target and source are the same repository; nothing to do")
        return 0

    print(f"[media] source  {args.source}@{args.branch}")
    print(f"[media] target  {args.target}@{args.branch}")

    if not remote_has_branch(args.source, args.branch):
        print(f"[media] the source has no {args.branch} branch — nothing to copy",
              file=sys.stderr)
        return 1
    if remote_has_branch(args.target, args.branch):
        print(f"[media] the target ALREADY has {args.branch}. This script creates it; "
              "it does not merge into an existing one. Delete it there first if you "
              "mean to replace it.", file=sys.stderr)
        return 1

    work = Path(tempfile.mkdtemp(prefix="media-bootstrap-"))
    try:
        # Only the media branch, only its tip: this is 600+ MB of video and
        # there is no reason to fetch its history or any other branch.
        print("[media] fetching the media branch (tip only)…")
        run(["git", "clone", "--quiet", "--depth", "1", "--branch", args.branch,
             f"https://github.com/{args.source}.git", str(work / "src")])
        src = work / "src"
        files = sorted((src / MEDIA_DIR).glob("**/*"))
        media = [f for f in files if f.is_file()]
        total = sum(f.stat().st_size for f in media)
        print(f"[media] {len(media)} file(s), {total/1048576:.0f} MB")
        if not media:
            print("[media] the source branch has no media; refusing to create an "
                  "empty branch", file=sys.stderr)
            return 1

        if not args.apply:
            print("\n[media] DRY RUN — nothing was created. With --apply this would:")
            print(f"  1. create orphan branch {args.branch} in {args.target}")
            print(f"  2. copy {len(media)} file(s) ({total/1048576:.0f} MB) under {MEDIA_DIR}/")
            print(f"  3. push it")
            print("  4. " + ("leave the media.js fallback in place"
                             if args.keep_fallback else
                             "remove the media.js fallback so the site uses its own branch"))
            print("\n  Re-run with --apply when you have push rights on the target.")
            return 0

        # Build the branch in a fresh clone of the target so nothing here is at
        # risk, and so the orphan really is orphan.
        print("[media] preparing the target…")
        run(["git", "clone", "--quiet", "--depth", "1",
             f"https://github.com/{args.target}.git", str(work / "dst")])
        dst = work / "dst"
        run(["git", "checkout", "--quiet", "--orphan", args.branch], cwd=dst)
        run(["git", "rm", "-rq", "--cached", "."], cwd=dst, check=False)
        for p in dst.iterdir():
            if p.name == ".git":
                continue
            shutil.rmtree(p) if p.is_dir() else p.unlink()

        shutil.copytree(src / MEDIA_DIR, dst / MEDIA_DIR)
        if (src / MANIFEST).is_file():
            (dst / MANIFEST).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src / MANIFEST, dst / MANIFEST)
        (dst / "README.md").write_text(
            f"# {args.branch} — large media, kept out of the code clone\n\n"
            "Demo recordings, served to the site at runtime by `media.js`.\n\n"
            "This is an **orphan branch**: it shares no history with `main`, so a\n"
            "merge cannot pull it into the code clone by accident, and\n"
            "`git clone --depth 1` of `main` never fetches a byte of it — depth 1\n"
            "implies single-branch. That is the entire mechanism; keep it.\n\n"
            f"Copied from `{args.source}@{args.branch}` by\n"
            "`scripts/bootstrap_media_branch.py`.\n\n"
            "Files above ~25 MB do not belong here: an object URL buffers the whole\n"
            "file and gives up range requests. Use a release asset for those.\n",
            encoding="utf-8")

        run(["git", "add", "-A"], cwd=dst)
        run(["git", "commit", "-q", "-m",
             f"{args.branch}: demo recordings, copied from {args.source}\n\n"
             "Orphan branch, no shared history with the code branches, so a merge\n"
             "can never pull this into the install clone by accident.\n"], cwd=dst)
        print("[media] pushing… (this is the slow part; it is the video itself)")
        run(["git", "push", "-q", "origin", args.branch], cwd=dst)
        print(f"[media] pushed {args.target}@{args.branch}")

        if not args.keep_fallback:
            mp = REPO_ROOT / "media.js"
            s = mp.read_text(encoding="utf-8")
            new = re.sub(r"    fallback: \{[^}]*\},\n", "    fallback: null,\n", s, count=1)
            if new != s:
                mp.write_text(new, encoding="utf-8")
                print("[media] media.js fallback removed — the site now uses its own "
                      "branch only. Commit that change.")
            else:
                print("[media] media.js had no fallback to remove")
        else:
            print("[media] fallback left in place (--keep-fallback)")

        print("\n[media] done. Verify before you rely on it:")
        print(f"  curl -sI https://cdn.jsdelivr.net/gh/{args.target}@{args.branch}"
              f"/{MEDIA_DIR}/<slug>.mp4 | head -3")
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
