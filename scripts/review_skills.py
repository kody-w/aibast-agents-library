#!/usr/bin/env python3
"""Automated skill review — the same rubric discipline, applied to prose.

Aggregating an outside skill and linking back to it is a search index. The
value we add is the review: a converted skill gets held to a stated standard,
the findings are published next to it, and every failed check explains what
good looks like. That is also the point of the library — people learn RAPP by
reading why something did or did not meet the bar.

A skill is instructions, not code, so the rubric asks different questions than
the agent rubric. A skill fails not by crashing but by being vague: steps that
cannot be followed the same way twice, outputs nobody named, a verification
step nobody wrote. Those are the defects this looks for.

Exposes the resident interface Sentinel expects: ``review_one(path) -> dict``
and ``RUBRIC_VERSION``.

Usage:
    python3 scripts/review_skills.py
    python3 scripts/review_skills.py --only accessibility_pass
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO_ROOT / "skills"
OUT_FILE = REPO_ROOT / "state" / "skill_reviews.json"

SCHEMA = "aibast-machine-review/1.0"
RUBRIC_VERSION = "1.0.0"

PRINCIPLES = {
    "provenance": "Can a reader tell where this came from and what licence it carries?",
    "usability": "Can a model tell when to reach for this, without guessing?",
    "determinism": "Would two runs of these steps produce the same thing?",
    "safety": "Can following these instructions damage something?",
    "completeness": "Is everything needed here, in this one file?",
}

REQUIRED_FRONTMATTER = ("schema", "name", "version", "description",
                        "source_url", "source_license", "converted_from")

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
SECRET_LITERAL = re.compile(
    r"(api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}", re.I)
DESTRUCTIVE = re.compile(
    r"(rm\s+-rf\s+/|DROP\s+TABLE|TRUNCATE\s+TABLE|git\s+push\s+--force|"
    r"Remove-Item\s+-Recurse\s+-Force\s+[A-Za-z]:\\)", re.I)
ABS_PATH = re.compile(r"(/Users/[a-z]|/home/[a-z]|[A-Za-z]:\\Users\\)")
STEP_LINE = re.compile(r"^\s*(\d+[.)]\s+|[-*]\s+)", re.M)
DEMO_DOMAINS = {"contoso.com", "fabrikam.com", "example.com", "example.org",
                "microsoft.com", "github.com", "localhost"}
EMAIL_RE = re.compile(r"\b[\w.+-]+@([\w-]+\.[\w.]+)\b")


class Check:
    def __init__(self, cid, principle, level, title):
        self.id, self.principle, self.level, self.title = cid, principle, level, title
        self.passed, self.detail, self.teachable = True, "", ""

    def fail(self, detail, teachable):
        self.passed, self.detail, self.teachable = False, detail, teachable
        return self

    def as_dict(self):
        d = {"id": self.id, "principle": self.principle, "level": self.level,
             "title": self.title, "passed": self.passed}
        if not self.passed:
            d["detail"], d["teachable"] = self.detail, self.teachable
        return d


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    meta = {}
    for line in text[3:end].splitlines():
        line = line.strip()
        if not line or ":" not in line or line.startswith("#"):
            continue
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip().strip("'\"")
    return meta, text[end + 4:].lstrip("\n")


def review_one(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    meta, body = split_frontmatter(text)
    checks: list[Check] = []

    def add(cid, principle, level, title):
        c = Check(cid, principle, level, title)
        checks.append(c)
        return c

    # ------------------------------------------------------------- provenance
    c = add("K1", "provenance", "error", "Carries a complete RAPP skill manifest")
    missing = [k for k in REQUIRED_FRONTMATTER if not meta.get(k)]
    if missing:
        c.fail(f"frontmatter missing: {', '.join(missing)}",
               "The manifest is what makes a skill discoverable and traceable. "
               "Without `source_url` and `source_license` a redistributed skill "
               "is indistinguishable from one we wrote, which is both a licence "
               "problem and a credit problem.")

    c = add("K2", "provenance", "error", "Credits the original author in the body")
    if "Converted skill" not in body and "converted from" not in body.lower():
        c.fail("no attribution block in the body",
               "Frontmatter is metadata; a reader opening the file sees the body. "
               "Redistribution with credit means the credit is visible to the "
               "person reading, not only to the parser.")

    c = add("K3", "provenance", "warn", "Version is a semantic version")
    if not SEMVER.match(str(meta.get("version", ""))):
        c.fail(f"version is {meta.get('version')!r}",
               "Consumers pin skills. A version that does not sort predictably "
               "cannot be pinned, so every consumer silently tracks whatever is "
               "newest — including a breaking change.")

    # -------------------------------------------------------------- usability
    desc = str(meta.get("description", ""))
    c = add("K4", "usability", "warn", "Description is specific enough to route on")
    if len(desc) < 80:
        c.fail(f"description is {len(desc)} characters",
               "A skill competes for attention against every other skill loaded. "
               "A short description loses that competition and the skill is never "
               "reached for. State the trigger and the artifact produced.")

    c = add("K5", "usability", "warn", "Says when to use it, not only what it is")
    if not re.search(r"##\s*When to use", body, re.I):
        c.fail("no 'When to use this' section",
               "What a skill *is* does not tell a model *when* to invoke it. The "
               "trigger condition is the single most load-bearing sentence in a "
               "skill file, and it belongs under its own heading.")

    c = add("K6", "usability", "warn", "Carries tags for discovery")
    tags = meta.get("tags", "")
    if not tags or tags in ("[]", "''"):
        c.fail("no tags",
               "Tags are how a skill is found by someone who does not already "
               "know its name — which is everyone, the first time.")

    # ------------------------------------------------------------ determinism
    c = add("K7", "determinism", "error", "States a deterministic contract")
    if "deterministic layer" not in body.lower():
        c.fail("no deterministic-layer section",
               "A skill that does not state its inputs, outputs, and verification "
               "step produces a different result every run, because the model "
               "fills the gaps differently each time. Stating the contract is "
               "what separates a skill from a suggestion.")

    c = add("K8", "determinism", "warn", "Gives followable steps")
    steps = len(STEP_LINE.findall(body))
    if steps < 3:
        c.fail(f"only {steps} enumerated step(s) found",
               "Prose describing an approach is not a procedure. Numbered steps "
               "are what make two runs comparable — and what make a failure "
               "locatable to a specific step rather than to the whole skill.")

    c = add("K9", "determinism", "warn", "Names a verification step")
    if not re.search(r"verif|confirm|check that|validate", body, re.I):
        c.fail("no verification language in the body",
               "Without a verification step the skill reports success whenever it "
               "finishes, which is not the same thing. Say what to check before "
               "claiming the work is done.")

    # ----------------------------------------------------------------- safety
    c = add("K10", "safety", "error", "No credential literals")
    m = SECRET_LITERAL.search(text)
    if m:
        c.fail(f"credential-shaped literal near offset {m.start()}",
               "A key in a public file is compromised on push and stays in git "
               "history after deletion. Reference the environment variable by "
               "name and let the operator supply the value.")

    c = add("K11", "safety", "error", "No unguarded destructive command")
    m = DESTRUCTIVE.search(text)
    if m:
        c.fail(f"destructive command: {m.group(0)[:50]}",
               "A skill is executed by a model on someone else's machine. A "
               "destructive command with no confirmation step will eventually run "
               "against something that mattered. Require explicit confirmation, "
               "and scope the target.")

    c = add("K12", "safety", "warn", "Sample data uses fictional domains")
    real = sorted({d for d in EMAIL_RE.findall(text) if d.lower() not in DEMO_DOMAINS})
    if real:
        c.fail(f"addresses at: {', '.join(real[:3])}",
               "Example data in a published skill must be fictional. Anything else "
               "is personal data that every fork copies forever.")

    # ----------------------------------------------------------- completeness
    c = add("K13", "completeness", "error", "No absolute path from the author's machine")
    if ABS_PATH.search(text):
        c.fail("contains an absolute home-directory path",
               "The path exists on exactly one machine. Name the file relative to "
               "the working directory, or take the location as an input.")

    c = add("K14", "completeness", "warn", "Substantial enough to act on")
    if len(body.strip()) < 400:
        c.fail(f"body is {len(body.strip())} characters",
               "A skill this short is a title with an intention attached. If the "
               "procedure genuinely fits in a paragraph, it is a note, not a "
               "skill — and publishing it as one costs the reader a click.")

    c = add("K15", "completeness", "warn", "Self-contained: no unresolvable references")
    dangling = re.findall(r"see\s+(?:the\s+)?[`\"']([^`\"']+\.(?:md|py|json))[`\"']", body, re.I)
    unresolved = [d for d in dangling if not (path.parent / d).exists()]
    if unresolved:
        c.fail(f"references files not shipped with it: {', '.join(unresolved[:3])}",
               "The single-file principle is what makes a skill portable: one "
               "download and it works. A reference to a file that did not come "
               "along turns the skill into a broken link.")

    scores, weights = {}, {"error": 2.0, "warn": 1.0}
    for principle in PRINCIPLES:
        rel = [x for x in checks if x.principle == principle]
        total = sum(weights[x.level] for x in rel)
        got = sum(weights[x.level] for x in rel if x.passed)
        scores[principle] = round(100 * got / total) if total else 100

    errors = [x for x in checks if not x.passed and x.level == "error"]
    warns = [x for x in checks if not x.passed and x.level == "warn"]
    overall = round(sum(scores.values()) / len(scores))
    verdict = ("blocked" if errors else "review-ready" if overall >= 85
               else "needs-work" if overall >= 60 else "not-ready")

    return {
        "file": path.relative_to(REPO_ROOT).as_posix(),
        "slug": path.stem,
        "ref": meta.get("name", path.stem),
        "source": meta.get("converted_from", ""),
        "source_url": meta.get("source_url", ""),
        "license": meta.get("source_license", ""),
        "review_type": "machine",
        "subject_kind": "skill",
        "rubric_version": RUBRIC_VERSION,
        "verdict": verdict,
        "overall": overall,
        "scores": scores,
        "error_count": len(errors),
        "warn_count": len(warns),
        "checks": [x.as_dict() for x in checks],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only")
    args = ap.parse_args()

    files = sorted(SKILLS_ROOT.rglob("*.md")) if SKILLS_ROOT.is_dir() else []
    if args.only:
        files = [p for p in files if args.only in p.stem]
    reviews = [review_one(p) for p in files]

    verdicts: dict[str, int] = {}
    for r in reviews:
        verdicts[r["verdict"]] = verdicts.get(r["verdict"], 0) + 1

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps({
        "schema": SCHEMA,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rubric_version": RUBRIC_VERSION,
        "review_type": "machine",
        "subject_kind": "skill",
        "separation_notice": (
            "Machine review of aggregated skills. Static analysis against "
            "published principles; never combined with human ratings, and never "
            "a statement about the upstream author's work beyond what it checks."
        ),
        "principles": PRINCIPLES,
        "count": len(reviews),
        "verdicts": verdicts,
        "reviews": reviews,
    }, indent=2) + "\n", encoding="utf-8")

    print(f"[review-skills] {len(reviews)} skills reviewed: "
          + ", ".join(f"{k} {v}" for k, v in sorted(verdicts.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
