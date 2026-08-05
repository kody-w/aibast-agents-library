#!/usr/bin/env python3
"""Generate RAPPVision walkthrough storyboards from library entries.

The AIBAST industry recordings are all the same film: five acts, ~135 seconds,
fixed order. `media/RAPPVISION.md` writes that format down. This turns it into
a pipeline — every entry in the library, including aggregated skills we did not
author, gets the same walkthrough an authored agent gets.

That is the argument for aggregating rather than linking. A skill arrives as a
paragraph and a URL; it leaves with a one-pager, a machine review, and a
storyboard in the house format.

Deterministic on purpose. No model, no network, no invented facts: every line
is derived from the manifest, and any slot that would need a number a human
must supply is emitted as `[operator supplies]` rather than filled with a
plausible-sounding figure. A demo that fabricates a metric teaches the viewer
something false.

Output: media/walkthroughs/<slug>.json  (rappvision-walkthrough/1.0)

Usage:
    python3 scripts/build_walkthrough.py
    python3 scripts/build_walkthrough.py --only chart_builder
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "media" / "walkthroughs"

SCHEMA = "rappvision-walkthrough/1.0"
FORMAT_VERSION = "1.0.0"

# Act boundaries, in seconds, measured from the shipped recordings.
ACTS = [
    ("title", 0.0, 5.0),
    ("problem", 5.0, 22.0),
    ("overview", 22.0, 42.0),
    ("walkthrough", 42.0, 120.0),
    ("close", 120.0, 137.0),
]

CLOSE_CTA = ["Get started on your agentic journey today.",
             "Talk to your Microsoft representative to learn more."]

PLACEHOLDER = "[operator supplies]"

# Surfaces a RAPP entry can run on, in the order the recordings present them.
SURFACE_BY_TIER = {
    "brainstem": "Engages you in the local brainstem chat",
    "cloud": "Engages you in Microsoft Teams",
    "copilot": "Engages you in Microsoft Copilot Studio",
}

BROLL_BY_CATEGORY = {
    "manufacturing": "plant floor: two operators reviewing a line together",
    "financial_services": "advisory meeting: adviser and client at a desk",
    "healthcare": "clinical setting: staff at a workstation between rounds",
    "retail": "store floor: associate with a handheld, stock behind them",
    "professional_services": "consulting team around a laptop in a shared room",
    "human_resources": "one-to-one conversation in a quiet meeting room",
    "it_management": "operations desk: several dashboards, one person triaging",
    "b2b_sales": "seller preparing before a customer call",
    "energy": "field site: technician with a tablet, equipment behind",
    "general": "modern workplace: focused individual work at a laptop",
    "aggregated": "modern workplace: focused individual work at a laptop",
}

VERB_RE = re.compile(
    r"\b(analy[sz]e[sd]?|generate[sd]?|create[sd]?|summari[sz]e[sd]?|draft[s]?|"
    r"review[s]?|monitor[s]?|detect[s]?|classif(?:y|ies)|extract[s]?|plan[s]?|"
    r"recommend[s]?|route[s]?|reconcile[s]?|forecast[s]?|validate[s]?|fix(?:es)?|"
    r"check[s]?|convert[s]?|build[s]?)\b", re.I)


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", (text or "").strip()) if s.strip()]


ACRONYMS = ("HEDIS", "ROI", "KPI", "SLA", "ERP", "CRM", "API", "SKU", "OEE",
            "EBITDA", "CSAT", "NPS", "AR", "AP", "PO", "RFP", "SOW", "IT",
            "HR", "AI", "ML", "PII", "DLP", "CMK", "SMT", "MES", "B2B", "B2C")


def keep_acronyms(text: str) -> str:
    """Restore acronym casing after any lower-casing rewrite.

    "improve HEDIS performance, campaign ROI" was rendering on the marquee
    frame as "Improve hedis performance" / "Campaign roi", which reads as a
    typo to exactly the audience that knows the term.
    """
    for a in ACRONYMS:
        text = re.sub(rf"\b{a.lower()}\b", a, text)
        text = re.sub(rf"\b{a.capitalize()}\b", a, text)
    return text


def tidy_clause(text: str) -> str:
    """Leave a clause that reads as a finished phrase.

    Truncating to a word count reopens parentheses, strands closing ones, and
    ends on prepositions. This frame is the one a viewer reads longest, so it
    is worth cleaning until stable rather than once.
    """
    STOP = ("and", "or", "with", "from", "for", "to", "the", "a", "an",
            "of", "in", "on", "by", "that", "into")
    tail = text.strip()
    if tail.count("(") > tail.count(")"):
        tail = tail.split("(")[0]
    if tail.count(")") > tail.count("("):
        tail = tail.replace(")", "")
    previous = None
    while tail != previous:
        previous = tail
        tail = tail.strip().rstrip(",;:.-")
        words = tail.split()
        if words and words[-1].lower() in STOP:
            tail = " ".join(words[:-1])
    return keep_acronyms(tail.strip())


def actions_from(description: str, business_value=None) -> list[str]:
    if business_value:
        return [keep_acronyms(v if v[0].isupper() else v.capitalize())
                for v in business_value[:3]]
    verbs = []
    for m in VERB_RE.finditer(description or ""):
        tail = (description[m.end():m.end() + 70] or "").strip()
        # Cut at a real boundary, not the first comma: "Generate clean,
        # consistently-styled charts" would otherwise render on the overview
        # card as "Generate clean", which reads as a different capability.
        tail = re.split(r"[.;]| and then | so that | which ", tail)[0].strip()
        if "," in tail and len(tail.split(",")[0]) < 22:
            tail = tail.rsplit(",", 1)[0] if tail.count(",") > 1 else tail
        tail = re.sub(r"\s*\([^)]*\)", "", tail)
        words = tail.split()
        if len(words) > 8:
            tail = " ".join(words[:8])
        # Clean up AFTER truncating, not before: cutting to a word count can
        # reopen a parenthesis or end on a conjunction, and this frame is the
        # one a viewer reads longest.
        tail = tidy_clause(tail)
        phrase = f"{m.group(0).capitalize()} {tail}".strip()
        if len(phrase) > 16 and phrase not in verbs:
            verbs.append(phrase)
        if len(verbs) == 3:
            break
    return verbs or ["Does the work described above"]


def sources_from(entry: dict) -> list[str]:
    tools = entry.get("featured_tools") or entry.get("requires") or []
    if tools:
        return list(tools)[:3]
    env = entry.get("requires_env") or []
    if env:
        # "Reads configuration from AZURE_OPENAI_IMAGE_DEPLOYMENT" is a variable
        # name, not something a viewer can read off a slide. Name the platform
        # it points at; the exact variable belongs in the one-pager, not the film.
        platforms = []
        for e in env[:4]:
            low = e.lower()
            label = ("Azure OpenAI" if "azure_openai" in low or "openai" in low else
                     "Azure" if low.startswith("azure") else
                     "Microsoft Graph" if "graph" in low else
                     "Dynamics 365" if "dynamics" in low or low.startswith("d365") else
                     "SharePoint" if "sharepoint" in low else
                     e.replace("_", " ").title())
            if label not in platforms:
                platforms.append(label)
        return [f"Connects to {p}" for p in platforms[:3]]
    return ["Runs on what the operator already has open — no additional configuration"]


# Third person to imperative: an operator types "Generate a chart", not
# "Generates charts". Stripping the verb entirely left "Original images with an
# Azure GPT Image deployment and saves them locally", which no one would type.
THIRD_TO_IMPERATIVE = [
    (r"^Generates?\b", "Generate"), (r"^Creates?\b", "Create"),
    (r"^Analy[sz]es\b", "Analyse"), (r"^Provides?\b", "Give me"),
    (r"^Summari[sz]es\b", "Summarise"), (r"^Reviews?\b", "Review"),
    (r"^Checks?\b", "Check"), (r"^Builds?\b", "Build"),
    (r"^Monitors?\b", "Monitor"), (r"^Automates?\b", "Automate"),
    (r"^Extracts?\b", "Extract"), (r"^Detects?\b", "Detect"),
    (r"^Drafts?\b", "Draft"), (r"^Plans?\b", "Plan"),
    (r"^Recommends?\b", "Recommend"), (r"^Converts?\b", "Convert"),
    (r"^Helps? you\b", "Help me"), (r"^Enables?\b", "Help me"),
]


def imperative(text: str) -> str:
    """Rewrite a manifest description as something a person would type."""
    t = text.strip().rstrip(".")
    for pattern, repl in THIRD_TO_IMPERATIVE:
        if re.match(pattern, t, flags=re.I):
            t = re.sub(pattern, repl, t, count=1, flags=re.I)
            break
    # Drop a trailing "and saves them locally"-style clause: it describes the
    # agent's behaviour, not the operator's request.
    t = re.split(r",? and (?:saves?|stores?|writes?|returns?|can) ", t)[0]
    return t.strip()


def prompt_from(entry: dict) -> str:
    """Recast the description as the operator's opening message."""
    first = (sentences(entry.get("lede") or entry.get("description") or "") or [""])[0]
    first = re.sub(r"^(This (agent|skill)|The agent|It)\s+", "", first).strip()
    first = imperative(first)
    if not first:
        return f"Help me with {entry.get('display_name', 'this task')}."
    words = first.split()
    if len(words) > 16:
        first = " ".join(words[:16])
    return keep_acronyms(first[0].upper() + first[1:]) + " for " + PLACEHOLDER + "."


def findings_block(entry: dict) -> dict:
    """The agent's answer, structured the way the reference structures it.

    Measured from the reference at 0:55: an opening sentence, two labelled
    sections of short bullets, a highlighted callout carrying the headline
    finding and its source, and a closing question. A single flat list in a
    mostly-empty window is what made the generated cut read as unfinished.

    Every line is derived from what the entry declares. Only figures a human
    must supply stay marked.
    """
    name = entry.get("display_name") or entry["slug"]
    srcs = [s.replace("Connects to ", "").replace(
        "Runs on what the operator already has open — no additional configuration",
        "the operator's working context") for s in sources_from(entry)]
    acts = actions_from(entry.get("description", ""), entry.get("business_value"))
    env = entry.get("requires_env") or []

    intro = (f"I'll {imperative(acts[0])[0].lower() + imperative(acts[0])[1:]} "
             f"for {PLACEHOLDER}. Reading {', '.join(srcs[:2])} and checking "
             f"the constraints before I propose anything.")

    reading = [f"{s}: connected" for s in srcs[:2]]
    if env:
        reading.append("Configuration: " + ", ".join(env[:2]))
    reading.append(f"Records in scope: {PLACEHOLDER}")

    checks = [keep_acronyms(a) for a in acts[:3]]
    if len(checks) < 2:
        checks.append("Verified against the source before reporting")

    return {
        "intro": intro,
        "sections": [
            {"label": "What I read", "items": reading[:4]},
            {"label": "What I checked", "items": checks[:4]},
        ],
        "callout": {
            "headline": f"Headline finding: {PLACEHOLDER}",
            "source": "Source: " + ", ".join(srcs[:2]),
            "question": "Shall I show the plan?",
        },
    }


def plan_block(entry: dict) -> list[str]:
    """The follow-up turn: a plan made of the entry's own steps."""
    acts = actions_from(entry.get("description", ""), entry.get("business_value"))
    steps = []
    for i, a in enumerate(acts[:3], 1):
        steps.append(f"{i}. {imperative(a)}")
    steps.append(f"{len(steps) + 1}. Confirm the result against the source system")
    steps.append(f"{len(steps) + 1}. Hand back the artifact, and the reasoning "
                 f"behind it")
    return steps


def narration_for(act: str, entry: dict, name: str, seconds: float) -> str:
    """A line long enough to carry its act.

    The professional recordings narrate almost continuously; three short lines
    across 137 seconds reads as an unfinished cut. Roughly 2.6 words a second
    at the synthesiser's default rate, and a line is built up to about 85% of
    the act so it lands before the cut.
    """
    # 3.49 words/sec measured from the neural voice at 0.95 speed, filled to
    # 92% of the act. The old 2.6 estimate left a third of the film silent,
    # which is the loudest difference between this and the reference.
    budget = int(seconds * 3.49 * 0.92)
    parts: list[str] = []

    def take(*chunks):
        for c in chunks:
            c = (c or "").strip().rstrip(".")
            if not c:
                continue
            # Skip a chunk that will not fit rather than stopping: a later,
            # shorter line can still land, and an act that runs mostly silent
            # is what makes a cut look unfinished.
            if len(" ".join(parts + [c]).split()) > budget:
                continue
            parts.append(c + ".")

    if act == "problem":
        take(entry.get("lede") or entry.get("description"),
             "Today that is done by hand",
             "It is the kind of work that rewards being done the same way every time",
             "An agent holds that standard on every case, not only the ones "
             "someone has time for",
             "It reads the same sources a person would, applies the same checks "
             "in the same order, and shows its working",
             "The result is not just faster. It is repeatable, which is what "
             "makes it something you can build a process on")
    elif act == "overview":
        srcs = sources_from(entry)
        acts_ = actions_from(entry.get("description", ""), entry.get("business_value"))
        take(f"{name} reads what it needs and works where you already are",
             "It draws on " + ", ".join(s.replace("Connects to ", "") for s in srcs[:2]),
             "and it can " + ", ".join(a[0].lower() + a[1:] for a in acts_[:2]),
             "Everything it does is grounded in your own systems, under your own "
             "permissions",
             "Nothing is copied out, and nothing is cached somewhere you cannot "
             "see it",
             "It works inside the tools your team already has open all day")
    elif act == "close":
        take(f"{name} is one of more than a hundred agents in the AIBAST library",
             "Every one ships as a single file you can read before you run it",
             "with its architecture, its review and this walkthrough alongside it",
             "Start from the library, or bring your own use case",
             "Everything you have seen was generated from the agent's own "
             "manifest, and you can regenerate it yourself")
    elif act == "walkthrough":
        take("Here it is in use",
             "The operator asks in their own words — no form to fill in and no "
             "syntax to learn",
             f"{name} works out what is being asked, chooses the tools it needs, "
             f"and calls them",
             "The answer comes back with structure: what it found, what it "
             "recommends, and the tool it called to get there",
             "That last part matters, because it is what makes the answer "
             "checkable rather than merely convincing",
             "Ask a follow-up and it carries the context forward, so the "
             "conversation builds instead of restarting",
             "Notice what is not happening here",
             "Nobody is copying data between systems, and nobody is retyping an "
             "answer into a document",
             "The agent is reading the systems of record in place, under the "
             "permissions the operator already has",
             "so the answer reflects what is true right now rather than whatever "
             "was exported last week",
             "Where a figure has to come from the operator, it is marked rather "
             "than invented",
             "That is deliberate — a demonstration that fabricates a number "
             "teaches the room something false",
             "Everything else on screen is generated from this agent's own "
             "manifest",
             "which is why it can be produced for every agent in the library, "
             "not only the ones that got a film crew",
             "The same manifest drives the one-pager, the architecture diagram "
             "and the review you can read alongside this",
             "One source of truth, four surfaces, and none of them can drift "
             "from the others",
             "When the agent changes, all of them change with it")
    return " ".join(parts)


def build(entry: dict) -> dict:
    name = entry.get("display_name") or entry["slug"]
    kind = entry.get("kind", "agent")
    category = (entry.get("category") or "general").lower()
    broll = BROLL_BY_CATEGORY.get(category, BROLL_BY_CATEGORY["general"])

    problem = (sentences(entry.get("lede") or entry.get("description") or "")
               or [f"{name} does work that is currently done by hand."])[0]

    title_lines = [name]
    if kind == "skill":
        title_lines.append(f"Aggregated from {entry.get('source') or 'an upstream project'}")

    scenes = [
        {"act": "title", "start": 0.0, "end": 5.0, "shot": "Microsoft logo, white field",
         "on_screen": title_lines, "narration": ""},
        {"act": "problem", "start": 5.0, "end": 22.0, "shot": f"B-roll — {broll}",
         "on_screen": [], "narration": narration_for("problem", entry, name, 17.0)},
        {"act": "overview", "start": 22.0, "end": 42.0,
         "shot": "Agent overview card — three gradient panels on dark field",
         "panels": {
             "Sources": sources_from(entry),
             "Flow of work": [entry.get("surface") or SURFACE_BY_TIER["brainstem"]],
             "Actions": actions_from(entry.get("description", ""), entry.get("business_value")),
         },
         "narration": narration_for("overview", entry, name, 20.0)},
        {"act": "walkthrough", "start": 42.0, "end": 120.0,
         "shot": "Laptop-framed chat surface",
         "turns": [
             {"role": "operator", "text": prompt_from(entry)},
             {"role": "agent", "heading": name,
              "rich": findings_block(entry),
              "agent_call": entry.get("tool_name") or entry.get("slug")},
             {"role": "operator", "text": "Show me the plan."},
             {"role": "agent", "heading": "Recommended plan",
              "rich": {"intro": "Here is the plan.",
                       "sections": [{"label": "Recommended plan",
                                     "items": plan_block(entry)}],
                       "callout": {"headline": f"Expected effect: {PLACEHOLDER}",
                                   "source": "Nothing is written back without confirmation",
                                   "question": "Approve and I'll proceed."}},
              "agent_call": entry.get("tool_name") or entry.get("slug")},
         ],
         "narration": narration_for("walkthrough", entry, name, 78.0)},
        {"act": "close", "start": 120.0, "end": 137.0,
         "shot": "Dark card, gradient CTA panel",
         "narration": narration_for("close", entry, name, 17.0),
         "on_screen": CLOSE_CTA + ([f"{entry.get('ref')} · {entry.get('license')}"]
                                   if kind == "skill" and entry.get("license") else [])},
    ]

    # Every placeholder is a remix point. A seller fills these in with their own
    # customer's scenario and the generic demo becomes theirs — which is the
    # difference between a video someone watches and a video someone presents.
    slots = []
    def collect(node, path):
        if isinstance(node, str):
            if PLACEHOLDER in node:
                slots.append({"path": path, "template": node})
        elif isinstance(node, list):
            for i, v in enumerate(node):
                collect(v, f"{path}[{i}]")
        elif isinstance(node, dict):
            for k, v in node.items():
                collect(v, f"{path}.{k}")
    collect(scenes, "scenes")

    return {
        "schema": SCHEMA,
        "format_version": FORMAT_VERSION,
        "remix": {
            "placeholder": PLACEHOLDER,
            "slot_count": len(slots),
            "slots": slots,
            "how": ("Replace each placeholder with your own customer's scenario and "
                    "this stops being a generic demo and becomes yours. The acts, "
                    "timings, and the Agent Calls line stay fixed — those are the "
                    "format and the checkable claim. Everything a customer would "
                    "recognise as their own situation is a slot."),
            "rule": ("Substitute real figures only if you can stand behind them. A "
                     "personalised demo carries more weight than a generic one, which "
                     "is exactly why an invented number in it does more damage."),
        },
        "format_doc": "media/RAPPVISION.md",
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "subject": {"slug": entry["slug"], "kind": kind, "ref": entry.get("ref"),
                    "display_name": name, "category": category},
        "runtime_seconds": ACTS[-1][2],
        "status": "storyboard",
        "approval": {
            "required_before_render": True,
            "note": ("A storyboard is a script, not footage. Every figure is marked "
                     f"{PLACEHOLDER} rather than invented — a demo that fabricates a "
                     "metric teaches the viewer something false. A human approves the "
                     "script before anything is rendered."),
        },
        "scenes": scenes,
    }


def entries_from_registry() -> list[dict]:
    out = []
    doc = json.loads((REPO_ROOT / "api" / "v1" / "agents.json").read_text(encoding="utf-8"))
    onepagers = {}
    op_file = REPO_ROOT / "data" / "onepagers.json"
    if op_file.is_file():
        for s in json.loads(op_file.read_text(encoding="utf-8"))["onepagers"]:
            onepagers[re.sub(r"[^a-z0-9]+", "", s["display_name"].lower())] = s

    for a in doc.get("agents", []):
        slug = a["name"].split("/")[-1]
        key = re.sub(r"[^a-z0-9]+", "", (a.get("display_name") or "").lower())
        sol = onepagers.get(key, {})
        out.append({
            "slug": slug, "kind": "agent", "ref": a["name"],
            "display_name": a.get("display_name"), "description": a.get("description"),
            "category": a.get("category"), "requires_env": a.get("requires_env"),
            "tool_name": a.get("display_name"),
            "lede": sol.get("lede"), "business_value": sol.get("business_value"),
            "featured_tools": sol.get("featured_tools"),
        })
    return out


def entries_from_aggregated() -> list[dict]:
    f = REPO_ROOT / "state" / "aggregated.json"
    if not f.is_file():
        return []
    doc = json.loads(f.read_text(encoding="utf-8"))
    out = []
    for s in doc.get("skills", []):
        if not s.get("rapp_skill"):
            continue  # index-only entries have nothing of ours to build on
        out.append({
            "slug": s["ref"].split("/")[-1], "kind": "skill", "ref": s["ref"],
            "display_name": s.get("display_name"), "description": s.get("description"),
            "category": "aggregated", "tool_name": s["ref"].split("/")[-1],
            "source": s.get("author"), "license": (s.get("license") or {}).get("spdx"),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", help="build one storyboard by slug")
    args = ap.parse_args()

    entries = entries_from_registry() + entries_from_aggregated()
    if args.only:
        entries = [e for e in entries if args.only in e["slug"]]
    if not entries:
        print(f"[rappvision] nothing matched {args.only!r}", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    kept, written = set(), 0
    for entry in entries:
        doc = build(entry)
        out = OUT_DIR / f"{entry['kind']}-{entry['slug']}.json"
        kept.add(out)
        text = json.dumps(doc, indent=2) + "\n"
        if out.exists():
            old = json.loads(out.read_text(encoding="utf-8"))
            if {k: v for k, v in old.items() if k != "generated"} == \
               {k: v for k, v in doc.items() if k != "generated"}:
                continue
        out.write_text(text, encoding="utf-8")
        written += 1

    if not args.only:
        for stale in OUT_DIR.glob("*.json"):
            if stale not in kept:
                stale.unlink()

    agents = sum(1 for e in entries if e["kind"] == "agent")
    print(f"[rappvision] {len(entries)} storyboards "
          f"({agents} agents, {len(entries) - agents} aggregated skills), "
          f"{written} written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
