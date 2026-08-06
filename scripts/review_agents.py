#!/usr/bin/env python3
"""Automated agent review — the machine half of the library's review layer.

This produces a MACHINE review of every ``agent.py`` in the library. It is
deliberately and permanently separate from human ratings:

  * Human ratings come from GitHub Discussions — people reacting and
    commenting. They measure whether an agent is *liked and used*.
  * Machine reviews come from this script. They measure whether an agent is
    *built correctly* against stated principles.

The two are never averaged, never blended into one number, and never rendered
in the same panel. A five-star human rating cannot rescue an agent that leaks a
credential, and a perfect machine score is not an endorsement by anybody. Both
are useful precisely because they answer different questions, and they stop
being useful the moment a reader cannot tell which one they are looking at.

Every failed check carries a ``teachable`` note: what the principle is, why it
matters, and what to do instead. That is the point of publishing the review —
a reader learns the standard by reading why something missed it, and a
maintainer gets a queue of what to fix before approving.

Reviews are computed by parsing the source with ``ast``. Agent code is never
imported and never executed.

Output:
    state/agent_reviews.json   (published as api/v1/reviews.json)

Usage:
    python3 scripts/review_agents.py
    python3 scripts/review_agents.py --only art-generator
    python3 scripts/review_agents.py --check      # fail if any error-level check fails
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_ROOT = REPO_ROOT / "agents"
OUT_FILE = REPO_ROOT / "state" / "agent_reviews.json"

SCHEMA = "aibast-machine-review/1.0"
RUBRIC_VERSION = "1.0.0"

# Principles the machine can actually check. A principle nobody can check is a
# wish, and wishes do not belong in a review that claims to be objective.
PRINCIPLES = {
    "quality": "Is it built the way a maintained agent is built?",
    "usability": "Can a model — and a human — tell what this does and how to call it?",
    "effectiveness": "Does it actually do the work, or only describe it?",
    "safety": "Can installing this hurt the person who installed it?",
    "portability": "Will it run somewhere other than the machine that wrote it?",
}

# Fictional domains Microsoft documentation uses on purpose. Sample data in a
# demo agent is fine; a real address is not.
DEMO_DOMAINS = {
    "contoso.com", "fabrikam.com", "example.com", "example.org", "example.net",
    "northwind.com", "adventure-works.com", "adventureworks.com",
    "woodgrovebank.com", "tailwindtraders.com", "relecloud.com",
    "alpineski.com", "wideworldimporters.com", "litware.com", "proseware.com",
    "wingtiptoys.com", "lamnahealthcare.com", "vanarsdelltd.com",
    "treyresearch.net", "bellowscollege.com", "localhost",
    # Not an address: the OData binding annotation `@odata.bind`.
    "odata.bind",
}

EMAIL_RE = re.compile(r"\b[\w.+-]+@([\w-]+\.[\w.]+)\b")
SECRETISH = re.compile(r"(secret|token|api_?key|password|passwd|client_secret|conn(ection)?_?str)", re.I)
ABS_PATH_RE = re.compile(r"(/Users/|/home/[a-z]|[A-Za-z]:\\\\?Users)")
STDLIB_OK = {
    "os", "sys", "re", "json", "time", "math", "random", "base64", "hashlib",
    "datetime", "pathlib", "typing", "collections", "itertools", "functools",
    "urllib", "http", "logging", "uuid", "textwrap", "csv", "io", "string",
    "dataclasses", "enum", "abc", "traceback", "subprocess", "tempfile",
    "shutil", "glob", "copy", "decimal", "statistics", "warnings", "asyncio",
    "concurrent", "threading", "queue", "html", "xml", "sqlite3", "zipfile",
    "unicodedata", "difflib", "secrets", "calendar", "struct", "binascii",
}


class Check:
    """One rubric check: a verdict plus, when it fails, how to fix it."""

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
            d["detail"] = self.detail
            d["teachable"] = self.teachable
        return d


def looks_like_a_secret(value: str) -> bool:
    """Distinguish an opaque credential from a config string named like one.

    A reviewer that cries wolf gets ignored, and an ignored reviewer catches
    nothing. `AZURE_SCOPE = "https://…/.default"` is named like a secret and is
    published documentation; a real key is opaque and high-entropy.
    """
    if re.match(r"https?://", value) or " " in value or value.startswith("{"):
        return False
    if re.fullmatch(r"[A-Za-z0-9_.\-]+", value) and "." in value and not re.search(r"\d{4}", value):
        return False  # dotted identifier: a scope, a setting name, a module path
    alphabet = len(set(value))
    return alphabet >= 12 and bool(re.search(r"\d", value)) and bool(re.search(r"[A-Za-z]", value))


def walk(node):
    yield node
    for child in ast.iter_child_nodes(node):
        yield from walk(child)


def literal(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


class AgentSource:
    """Everything the rubric needs, extracted from source without running it."""

    def __init__(self, path: Path):
        self.path = path
        self.text = path.read_text(encoding="utf-8", errors="replace")
        self.tree = None
        self.parse_error = None
        try:
            self.tree = ast.parse(self.text)
        except SyntaxError as exc:
            self.parse_error = f"line {exc.lineno}: {exc.msg}"
            return

        self.classes = [n for n in self.tree.body if isinstance(n, ast.ClassDef)]
        # The library ships two base classes: BasicAgent (brainstem agents) and
        # BasicSkill (the skill shape). Both are valid registrations.
        self.agent_classes = [
            c for c in self.classes
            if any(getattr(b, "id", getattr(b, "attr", "")) in ("BasicAgent", "BasicSkill")
                   for b in c.bases)
        ]
        # The base classes themselves are framework, not agents, and are the one
        # legitimate way to have zero subclasses in a file.
        self.is_base_class = any(c.name in ("BasicAgent", "BasicSkill") for c in self.classes)
        self.metadata = self._metadata()
        self.perform = self._perform()

    def _metadata(self) -> dict:
        for node in walk(self.tree):
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    name = getattr(tgt, "attr", getattr(tgt, "id", ""))
                    if name in ("metadata", "__manifest__"):
                        value = literal(node.value)
                        if isinstance(value, dict):
                            return value
                        # Metadata built from self.name and literals: recover the
                        # literal keys we can, so a dynamic name is not a miss.
                        if isinstance(node.value, ast.Dict):
                            out = {}
                            for k, v in zip(node.value.keys, node.value.values):
                                key = literal(k)
                                if isinstance(key, str):
                                    val = literal(v)
                                    if val is not None:
                                        out[key] = val
                            return out
        return {}

    def _perform(self):
        for node in walk(self.tree):
            if isinstance(node, ast.FunctionDef) and node.name == "perform":
                return node
        return None


def review_one(path: Path) -> dict:
    src = AgentSource(path)
    checks: list[Check] = []

    def add(cid, principle, level, title):
        c = Check(cid, principle, level, title)
        checks.append(c)
        return c

    # ---------------------------------------------------------------- quality
    c = add("Q1", "quality", "error", "Source parses as Python")
    if src.parse_error:
        c.fail(src.parse_error,
               "An agent that does not parse cannot be discovered. The brainstem "
               "reads every agent file on each request; one syntax error removes "
               "the agent from the tool list silently. Run "
               "`python3 -m py_compile` on the file before publishing.")
        return finish(path, checks)

    if src.is_base_class:
        # A base class is the framework the agents extend. Reviewing it against
        # the agent rubric would report the framework as a broken agent.
        return {
            "file": path.relative_to(REPO_ROOT).as_posix(), "slug": path.stem,
            "review_type": "machine", "rubric_version": RUBRIC_VERSION,
            "verdict": "framework", "overall": None, "scores": {},
            "error_count": 0, "warn_count": 0, "checks": [],
            "note": "Base class, not an agent — the agent rubric does not apply.",
        }

    c = add("Q2", "quality", "error", "Declares exactly one agent class")
    if len(src.agent_classes) != 1:
        c.fail(f"found {len(src.agent_classes)} classes extending BasicAgent",
               "One file, one agent — that is the Single File Agent principle. "
               "Discovery registers by file, so a second agent class in the same "
               "file is invisible, and zero classes means nothing registers. Split "
               "additional agents into their own files.")

    c = add("Q3", "quality", "error", "Publishes a metadata contract")
    if not src.metadata.get("description"):
        c.fail("no metadata description found",
               "`metadata` is the function schema the model sees. Without a "
               "description the model has only the agent's name to decide with, "
               "so it either never calls the agent or calls it wrongly. Describe "
               "what it does and what it returns.")

    c = add("Q4", "quality", "warn", "No silent exception swallowing")
    swallowed = []
    for node in walk(src.tree):
        if isinstance(node, ast.ExceptHandler):
            bare = node.type is None
            passes = all(isinstance(b, ast.Pass) for b in node.body)
            if bare or passes:
                swallowed.append(node.lineno)
    if swallowed:
        c.fail(f"bare or empty except at line(s) {', '.join(map(str, swallowed[:5]))}",
               "A swallowed exception turns a failure into a wrong answer. The "
               "agent returns something that looks like success, and the model "
               "reports it to the user as fact. Catch the specific exception and "
               "return a message that says what failed.")

    c = add("Q5", "quality", "error", "No credential literals in source")
    hits = []
    for node in walk(src.tree):
        if isinstance(node, ast.Assign):
            names = [getattr(t, "attr", getattr(t, "id", "")) for t in node.targets]
            val = literal(node.value)
            if isinstance(val, str) and len(val) >= 16 and any(SECRETISH.search(n or "") for n in names):
                if looks_like_a_secret(val):
                    hits.append(names[0])
    if hits:
        c.fail(f"credential-shaped literal assigned to {', '.join(hits[:3])}",
               "A secret committed to a public repository is compromised the "
               "moment it is pushed, and deleting the line does not undo it — the "
               "value stays in git history. Read secrets from the environment and "
               "list the variable names in `requires_env`.")

    # -------------------------------------------------------------- usability
    desc = str(src.metadata.get("description") or "")
    c = add("U1", "usability", "warn", "Description is specific enough to route on")
    if len(desc) < 80:
        c.fail(f"description is {len(desc)} characters",
               "Model routing is a text-similarity problem. A short description "
               "competes badly against every other tool in the list, so the agent "
               "gets skipped on the requests it was built for. State the task, the "
               "trigger, and the shape of what comes back.")

    params = src.metadata.get("parameters") or {}
    props = (params.get("properties") or {}) if isinstance(params, dict) else {}
    c = add("U2", "usability", "warn", "Every parameter is documented")
    undocumented = [k for k, v in props.items() if not (isinstance(v, dict) and v.get("description"))]
    if undocumented:
        c.fail(f"no description on: {', '.join(undocumented[:5])}",
               "An undescribed parameter gets guessed at. The model fills it with "
               "something plausible and the agent runs on invented input. Give "
               "every property a description and an example value.")

    c = add("U3", "usability", "warn", "Declares which parameters are required")
    if props and isinstance(params, dict) and "required" not in params:
        c.fail("parameters has properties but no `required` list",
               "Without `required`, every argument is optional as far as the model "
               "is concerned, so the agent is called with nothing and has to fail "
               "or guess. List the arguments that must be present — an empty list "
               "is a valid, explicit answer.")

    c = add("U4", "usability", "warn", "Configuration comes from the environment")
    literal_urls = [
        n.value for n in walk(src.tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
        and re.match(r"https?://", n.value)
        and not any(d in n.value for d in DEMO_DOMAINS)
        and "docs.microsoft" not in n.value and "learn.microsoft" not in n.value
        and "github.com" not in n.value and "schema" not in n.value
    ]
    if literal_urls:
        c.fail(f"hardcoded endpoint: {literal_urls[0][:60]}",
               "A hardcoded endpoint pins the agent to one tenant or region, so "
               "the next person who installs it is silently calling your service. "
               "Read the endpoint from the environment and declare it in "
               "`requires_env`.")

    # ---------------------------------------------------------- effectiveness
    c = add("E1", "effectiveness", "warn", "Does work rather than returning a fixed answer")
    if src.perform:
        body = [n for n in src.perform.body if not isinstance(n, ast.Expr) or not isinstance(n.value, ast.Constant)]
        only_const_return = (
            len(body) == 1 and isinstance(body[0], ast.Return)
            and isinstance(body[0].value, ast.Constant)
        )
        if only_const_return:
            c.fail("perform() returns a constant",
                   "A constant response is a mock, not an agent. It demonstrates "
                   "a conversation shape, which is useful for a scripted demo and "
                   "misleading anywhere else. Mark it as a demo in the description, "
                   "or connect it to the system it claims to read.")
    else:
        c.fail("no perform() method",
               "`perform(**kwargs)` is the entry point the brainstem calls. "
               "Without it the agent registers and then fails at call time.")

    c = add("E2", "effectiveness", "warn", "Returns a value on every path")
    if src.perform:
        returns = [n for n in walk(src.perform) if isinstance(n, ast.Return)]
        if not returns or any(r.value is None for r in returns):
            c.fail("a code path returns None",
                   "Returning nothing gives the model an empty tool result, which "
                   "it usually reports as success with no detail. Return a string "
                   "on every path, including the failure paths.")

    c = add("E3", "effectiveness", "warn", "States its contract in a docstring")
    doc = ast.get_docstring(src.agent_classes[0]) if src.agent_classes else None
    if not doc and not (src.perform and ast.get_docstring(src.perform)):
        c.fail("no docstring on the agent class or perform()",
               "The docstring is where the deterministic layer lives: inputs, "
               "outputs, and how to verify the result. It is what a reader checks "
               "when the agent behaves unexpectedly, and it costs nothing at "
               "runtime.")

    # ----------------------------------------------------------------- safety
    c = add("S1", "safety", "error", "No eval or exec")
    dangerous = [n.func.id for n in walk(src.tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                 and n.func.id in ("eval", "exec", "compile")]
    if dangerous:
        c.fail(f"calls {', '.join(sorted(set(dangerous)))}",
               "`eval` on anything a model produced is remote code execution with "
               "extra steps — the model's output is attacker-influenced whenever a "
               "user can type. Parse with `json.loads` or `ast.literal_eval`.")

    c = add("S2", "safety", "error", "No shell execution with a composed string")
    shelly = []
    for node in walk(src.tree):
        if isinstance(node, ast.Call):
            fn = ast.unparse(node.func) if hasattr(ast, "unparse") else ""
            if fn.endswith("os.system") or fn.endswith("os.popen"):
                shelly.append(fn)
            if "subprocess" in fn:
                for kw in node.keywords:
                    if kw.arg == "shell" and literal(kw.value) is True:
                        shelly.append("subprocess(shell=True)")
    if shelly:
        c.fail(f"uses {', '.join(sorted(set(shelly)))}",
               "A shell string built from agent input is a command-injection hole; "
               "a semicolon in a filename is enough. Pass an argument list to "
               "`subprocess.run` and leave `shell` off.")

    c = add("S3", "safety", "warn", "Sample data uses documented fictional domains")
    real_domains = sorted({d for d in EMAIL_RE.findall(src.text) if d.lower() not in DEMO_DOMAINS})
    if real_domains:
        c.fail(f"email addresses at: {', '.join(real_domains[:3])}",
               "Demo data in a public library must be fictional. Microsoft "
               "documentation reserves contoso.com and fabrikam.com for exactly "
               "this; a real address is personal data that a fork copies forever.")

    # ------------------------------------------------------------ portability
    c = add("P1", "portability", "error", "No absolute paths from the author's machine")
    m = ABS_PATH_RE.search(src.text)
    if m:
        c.fail(f"absolute path near offset {m.start()}",
               "An absolute home-directory path works on exactly one machine. "
               "Resolve paths relative to the agent file or read a directory from "
               "the environment.")

    c = add("P2", "portability", "warn", "Imports are standard library or declared")
    imported = set()
    for node in walk(src.tree):
        if isinstance(node, ast.Import):
            imported |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imported.add(node.module.split(".")[0])
    external = sorted(imported - STDLIB_OK - {"agents", "utils", "basic_agent"})
    if external:
        c.fail(f"third-party imports: {', '.join(external[:5])}",
               "A single-file agent should install by copying one file. Every "
               "third-party import is a dependency the installer does not know "
               "about, so the agent registers and then fails on first call. Use "
               "the standard library, or say so in the description.")

    return finish(path, checks)


def finish(path: Path, checks: list[Check]) -> dict:
    scores, weights = {}, {"error": 2.0, "warn": 1.0}
    for principle in PRINCIPLES:
        rel = [c for c in checks if c.principle == principle]
        if not rel:
            continue
        total = sum(weights[c.level] for c in rel)
        got = sum(weights[c.level] for c in rel if c.passed)
        scores[principle] = round(100 * got / total) if total else 100

    errors = [c for c in checks if not c.passed and c.level == "error"]
    warns = [c for c in checks if not c.passed and c.level == "warn"]
    overall = round(sum(scores.values()) / len(scores)) if scores else 0

    if errors:
        verdict = "blocked"
    elif overall >= 85:
        verdict = "review-ready"
    elif overall >= 60:
        verdict = "needs-work"
    else:
        verdict = "not-ready"

    return {
        "file": path.relative_to(REPO_ROOT).as_posix(),
        "slug": path.stem,
        "review_type": "machine",
        "rubric_version": RUBRIC_VERSION,
        "verdict": verdict,
        "overall": overall,
        "scores": scores,
        "error_count": len(errors),
        "warn_count": len(warns),
        "checks": [c.as_dict() for c in checks],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", help="review a single agent by file stem")
    ap.add_argument("--check", action="store_true", help="exit non-zero if any agent is blocked")
    args = ap.parse_args()

    files = [p for p in sorted(AGENTS_ROOT.rglob("*.py")) if "__pycache__" not in p.parts]
    if args.only:
        files = [p for p in files if args.only in p.stem]

    reviews = [review_one(p) for p in files]
    by_verdict: dict[str, int] = {}
    for r in reviews:
        by_verdict[r["verdict"]] = by_verdict.get(r["verdict"], 0) + 1

    doc = {
        "schema": SCHEMA,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rubric_version": RUBRIC_VERSION,
        "review_type": "machine",
        "separation_notice": (
            "Machine review only. These scores are produced by static analysis "
            "against published principles and are never combined with human "
            "ratings from Discussions. A machine score is not an endorsement, "
            "and a human rating is not a correctness proof."
        ),
        "principles": PRINCIPLES,
        "count": len(reviews),
        "verdicts": by_verdict,
        "reviews": reviews,
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"[review] {len(reviews)} agents reviewed: " +
          ", ".join(f"{k} {v}" for k, v in sorted(by_verdict.items())))
    print(f"[review] wrote {OUT_FILE.relative_to(REPO_ROOT)}")

    if args.check and by_verdict.get("blocked"):
        print(f"[review] {by_verdict['blocked']} agents blocked on error-level checks", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
