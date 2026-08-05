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


def actions_from(description: str, business_value=None) -> list[str]:
    if business_value:
        return [v if v[0].isupper() else v.capitalize() for v in business_value[:3]]
    verbs = []
    for m in VERB_RE.finditer(description or ""):
        tail = (description[m.end():m.end() + 44] or "").strip()
        tail = re.split(r"[,.;]", tail)[0].strip()
        phrase = f"{m.group(0).capitalize()} {tail}".strip()
        if len(phrase) > 12 and phrase not in verbs:
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
        return [f"Reads configuration from {e}" for e in env[:3]]
    return ["Runs on what the operator already has open — no additional configuration"]


def prompt_from(entry: dict) -> str:
    """Recast the description as the operator's opening message."""
    first = (sentences(entry.get("lede") or entry.get("description") or "") or [""])[0]
    first = re.sub(r"^(This (agent|skill)|The agent|It)\s+", "", first).strip().rstrip(".")
    first = re.sub(r"^(Provides?|Generates?|Creates?|Automates?|Helps? you)\s+", "", first, flags=re.I)
    if not first:
        return f"Help me with {entry.get('display_name', 'this task')}."
    return first[0].upper() + first[1:] + " for " + PLACEHOLDER + "."


def findings_block(entry: dict) -> list[str]:
    """What act 4 shows the agent returning. Structure is real; figures are not."""
    out = []
    params = entry.get("parameters") or []
    for p in list(params)[:3]:
        out.append(f"{p}: {PLACEHOLDER}")
    for v in (entry.get("business_value") or [])[:3]:
        out.append(f"{v} — {PLACEHOLDER}")
    if not out:
        out = [f"Result: {PLACEHOLDER}", f"Confidence and sources: {PLACEHOLDER}"]
    return out


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
         "on_screen": [], "narration": problem},
        {"act": "overview", "start": 22.0, "end": 42.0,
         "shot": "Agent overview card — three gradient panels on dark field",
         "panels": {
             "Sources": sources_from(entry),
             "Flow of work": [entry.get("surface") or SURFACE_BY_TIER["brainstem"]],
             "Actions": actions_from(entry.get("description", ""), entry.get("business_value")),
         },
         "narration": f"{name} reads what it needs, works where you already are, "
                      f"and hands back something you can act on."},
        {"act": "walkthrough", "start": 42.0, "end": 120.0,
         "shot": "Laptop-framed chat surface",
         "turns": [
             {"role": "operator", "text": prompt_from(entry)},
             {"role": "agent", "heading": name,
              "body": findings_block(entry),
              "agent_call": entry.get("tool_name") or entry.get("slug")},
             {"role": "operator", "text": "Show me the plan."},
             {"role": "agent", "heading": "Recommended plan",
              "body": [f"Step {i}: {PLACEHOLDER}" for i in (1, 2, 3)],
              "agent_call": entry.get("tool_name") or entry.get("slug")},
         ],
         "narration": "The operator asks in their own words. The agent answers with "
                      "structure, and names the tool it called."},
        {"act": "close", "start": 120.0, "end": 137.0,
         "shot": "Dark card, gradient CTA panel",
         "on_screen": CLOSE_CTA + ([f"{entry.get('ref')} · {entry.get('license')}"]
                                   if kind == "skill" and entry.get("license") else []),
         "narration": ""},
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
