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
# Measured from the recordings these films are composited onto — a 132.4s cut,
# not the 137s the first draft assumed. The storyboard is the artifact a human
# approves, so it has to describe the film that actually gets made.
ACTS = [
    ("title", 0.0, 7.3),
    ("problem", 7.3, 22.0),
    ("overview", 22.0, 42.75),
    ("walkthrough", 42.75, 113.5),
    ("close", 113.5, 132.4),
]

CLOSE_CTA = ["Get started on your agentic journey today.",
             "Talk to your Microsoft representative to learn more."]

PLACEHOLDER = "[operator supplies]"

# Surfaces a RAPP entry can run on, in the order the recordings present them.
SURFACE_BY_TIER = {
    "brainstem": "Engages you in Microsoft Teams and Outlook",
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
    r"check[s]?|convert[s]?|build[s]?|optimi[sz]e[sd]?)\b", re.I)


# Explicit, because suffix-stripping turned "Generates" into "Generat".
INFINITIVE = {
    "analyzes": "analyze", "analyses": "analyse", "analyzed": "analyze",
    "generates": "generate", "generating": "generate", "generated": "generate",
    "creates": "create", "creating": "create", "created": "create",
    "summarizes": "summarize", "summarises": "summarise",
    "drafts": "draft", "reviews": "review", "monitors": "monitor",
    "detects": "detect", "classifies": "classify", "extracts": "extract",
    "plans": "plan", "recommends": "recommend", "routes": "route",
    "reconciles": "reconcile", "forecasts": "forecast", "validates": "validate",
    "fixes": "fix", "checks": "check", "converts": "convert", "builds": "build",
    "optimizes": "optimize", "optimises": "optimise",
}


# A demo needs a scenario. The professional recordings are full of concrete
# figures — "2,400 units/day", "OEE 71%", "a 40% holiday surge" — because they
# are SYNTHETIC DEMO DATA, labelled as such on every one-pager. Leaving
# mail-merge fields on screen instead is not honesty, it is an unfinished cut.
#
# So: generate a scenario. Deterministic (seeded by the entry's own slug, so a
# rerun produces the same film), plainly synthetic, and never presented as a
# customer outcome.
SCENARIOS = {
    "manufacturing": {
        "subject": "the production line", "volume": "current throughput",
        "target": "the seasonal target", "metric": "equipment effectiveness below target",
        "window": "the ramp ahead", "driver": "a seasonal demand increase",
        "systems": "the ERP, line telemetry and effectiveness tracking",
        "verb": "improves throughput",
    },
    "healthcare": {
        "subject": "the member panel", "volume": "the open care gaps",
        "target": "the quality target", "metric": "gap closure behind plan",
        "window": "the measurement year", "driver": "a widening quality gap",
        "systems": "the record system, claims history and the care-gap registry",
        "verb": "accelerates gap closure",
    },
    "financial_services": {
        "subject": "the claims queue", "volume": "the open caseload",
        "target": "the service target", "metric": "cycle time above target",
        "window": "the reporting period", "driver": "a rise in incoming volume",
        "systems": "the policy system, claims history and risk signals",
        "verb": "shortens cycle time",
    },
    "retail": {
        "subject": "the region", "volume": "the store estate",
        "target": "the availability target", "metric": "availability below target",
        "window": "the promotional period", "driver": "a promotional lift",
        "systems": "the ERP, point of sale and the demand forecast",
        "verb": "improves availability",
    },
    "professional_services": {
        "subject": "the delivery portfolio", "volume": "active engagements",
        "target": "the utilisation target", "metric": "utilisation below target",
        "window": "the coming quarter", "driver": "concurrent ramp-ups",
        "systems": "the delivery system, timesheets and the resource plan",
        "verb": "raises utilisation",
    },
    "b2b_sales": {
        "subject": "the enterprise pipeline", "volume": "open opportunities",
        "target": "the conversion target", "metric": "conversion below target",
        "window": "the current quarter", "driver": "a compressed buying cycle",
        "systems": "CRM, engagement history and product signals",
        "verb": "improves conversion",
    },
    "teams": {
        "subject": "the current workload", "volume": "the working backlog",
        "target": "same-day turnaround", "metric": "turnaround slower than wanted",
        "window": "the coming month", "driver": "rising request volume",
        "systems": "the systems of record already in use",
        "verb": "accelerates turnaround",
    },
}
# Deliberately qualitative. A demo may show a scenario; it may not show figures
# nobody can stand behind. "Improves", "accelerates", "below target" are claims
# the product supports; "OEE 71%" and "2,400 units/day" are not ours to assert.


def scenario_for(entry: dict) -> dict:
    inds = entry.get("industries") or ([str(entry["category"]).replace("_", " ")]
                                       if entry.get("category") else [])
    key = "teams"
    hay = " ".join(inds).lower()
    for bucket in SCENARIOS:
        if bucket != "teams" and bucket.replace("_", " ") in hay:
            key = bucket
            break
    else:
        for bucket, words in (("healthcare", ("health", "clinical", "patient", "care")),
                              ("financial_services", ("financ", "bank", "insur", "claim")),
                              ("manufacturing", ("manufactur", "industrial", "supply", "inventory")),
                              ("retail", ("retail", "store", "commerce", "cpg")),
                              ("professional_services", ("professional", "consult", "legal")),
                              ("b2b_sales", ("sales", "b2b", "account", "pipeline"))):
            if any(w in hay for w in words):
                key = bucket
                break
    return SCENARIOS[key]


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


def to_infinitive(phrase: str) -> str:
    """Force a phrase to its bare-infinitive form.

    `actions_from` feeds three slots that are all grammatically infinitive —
    "a manager needs to ...", "I'll ... for the pipeline", "It can ... in the
    same conversation". A manifest's business_value reads "Improves conversion",
    third person, and dropping that into any of them yields "It can improves
    conversion". The conversion belongs here, once, rather than at each slot.
    """
    t = phrase.strip()
    if not t:
        return t
    head, _, rest = t.partition(" ")
    low = head.lower().rstrip(",")
    if low in INFINITIVE:
        head = INFINITIVE[low]
    elif low.endswith("ies") and len(low) > 4:
        head = low[:-3] + "y"
    elif low.endswith(("sses", "xes", "ches", "shes", "zzes")):
        # Only a stem that genuinely ends in a sibilant takes "-es". Testing for
        # a bare "-ses" instead ate a letter off ordinary verbs: "raises" became
        # "rais", and "the agent can rais margin" shipped.
        head = low[:-2]
    elif low.endswith("s") and not low.endswith("ss"):
        head = low[:-1]
    else:
        head = low
    return (head + (" " + rest if rest else "")).strip()


def as_display(phrase: str) -> str:
    """Sentence case for a phrase that is stored infinitive but read as a line."""
    p = phrase.strip()
    return (p[0].upper() + p[1:]) if p else p


def actions_from(description: str, business_value=None, entry=None) -> list[str]:
    if business_value:
        # Stored infinitive; every consumer inflects for its own slot.
        return [to_infinitive(keep_acronyms(v)) for v in business_value[:3]]
    verbs = []
    # Only match a verb that STARTS a clause. Matching anywhere produced
    # "forecasts and generating cost-effective transfer plans" out of
    # "...against demand forecasts and generating..." — a noun phrase dropped
    # into a verb slot, which then propagated to five on-screen locations and
    # both narration lines.
    for m in VERB_RE.finditer(description or ""):
        before = (description or "")[:m.start()].rstrip()
        # Word boundary, not endswith: "against demand".endswith("and") is True,
        # which let a noun through as a verb.
        last = before.split()[-1].strip(".,;:").lower() if before.split() else ""
        if before and not (before[-1] in ".,;:" or last in ("and", "or", "then", "to")):
            continue
        # Slice generously, then cut at a WORD boundary. A fixed 70-character
        # window sliced "against" into "agai" and shipped it to screen.
        tail = (description[m.end():m.end() + 120] or "").strip()
        if len(description) > m.end() + 120:
            tail = tail.rsplit(" ", 1)[0]
        # Cut at a real boundary, not the first comma: "Generate clean,
        # consistently-styled charts" would otherwise render on the overview
        # card as "Generate clean", which reads as a different capability.
        tail = re.split(r"[.;]| and then | so that | which ", tail)[0].strip()
        if "," in tail and len(tail.split(",")[0]) < 22:
            tail = tail.rsplit(",", 1)[0] if tail.count(",") > 1 else tail
        tail = re.sub(r"\s*\([^)]*\)", "", tail)
        words = tail.split()
        if len(words) > 8:
            # Cut at a clause boundary inside the window rather than at word 8,
            # which produced "...stock levels agai".
            cut = " ".join(words[:8])
            for sep in (" by ", " against ", " using ", " with ", " from ", " and "):
                if sep in cut:
                    cut = cut.split(sep)[0]
                    break
            tail = cut
        # Clean up AFTER truncating, not before: cutting to a word count can
        # reopen a parenthesis or end on a conjunction, and this frame is the
        # one a viewer reads longest.
        tail = tidy_clause(tail)
        verb = m.group(0)
        # Normalise to a bare infinitive so it reads correctly after "needs to"
        # and as a plan step: "Analyzes" -> "Analyze", "Generating" -> "Generate".
        verb = INFINITIVE.get(verb.lower(), verb)
        phrase = f"{verb.lower()} {tail}".strip()
        if len(phrase) > 16 and phrase not in verbs:
            verbs.append(phrase)
        if len(verbs) == 3:
            break
    if verbs:
        return verbs
    # Derive from the display name rather than admitting defeat on screen.
    entry = entry or {}
    name = (entry.get("display_name") or entry.get("slug") or "").replace("-", " ")
    name = re.sub(r"\bagent\b", "", name, flags=re.I).strip()
    if name:
        sc = scenario_for(entry or {})
        # Infinitive like everything else this returns; the scenario verb is
        # authored third person ("Improves conversion") and reached "It can
        # improves conversion" without this.
        return [f"handle {name.lower()}", to_infinitive(sc["verb"]),
                "report back with my reasoning"]
    return ["complete the task end to end", "report back with my reasoning"]


def named_systems(entry: dict) -> list[str]:
    """Systems that can be NAMED in a sentence — never a prose fallback.

    The reviewer caught "It pulls data from Runs on what the operator already
    has open — no additional configuration" being spoken aloud. That string is
    a legitimate panel caption and an illegitimate noun phrase. A slot that
    feeds a sentence has to be typed: if nothing can be named, the sentence is
    rewritten, not filled with prose.
    """
    out = []
    for x in sources_from(entry):
        x = x.replace("Connects to ", "").strip()
        if x.startswith("Runs on what") or x.startswith("Reads configuration"):
            continue
        if len(x.split()) > 6 or "—" in x:
            continue
        out.append(x)
    return out


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
    # No declared tools and no env: the scenario names real systems for this
    # industry, and the reference always NAMES things here. A panel that says
    # "runs on what the operator already has open" is a placeholder in a
    # sentence's clothing.
    sc = scenario_for(entry)
    named = re.split(r",\s*|\s+and\s+", sc["systems"])
    return [n.strip()[0].upper() + n.strip()[1:] for n in named if n.strip()][:3]


# Third person to imperative: an operator types "Generate a chart", not
# "Generates charts". Stripping the verb entirely left "Original images with an
# Azure GPT Image deployment and saves them locally", which no one would type.
THIRD_TO_IMPERATIVE = [
    (r"^Optimi[sz]es?\b", "Optimise"), (r"^Coordinates?\b", "Coordinate"),
    (r"^Manages?\b", "Manage"), (r"^Identifies\b", "Identify"),
    (r"^Tracks?\b", "Track"), (r"^Delivers?\b", "Deliver"),
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
    # An operator types a request, not a product description. The reference is
    # "Analyze production line 3 performance and optimize for the upcoming
    # holiday demand surge" — one clause, no sub-clauses.
    first = re.split(r"\s+by\s+|\s+using\s+|\s+through\s+|,\s+", first)[0].strip()
    first = tidy_clause(first)
    if not first:
        return f"Help me with {entry.get('display_name', 'this task')}."
    words = first.split()
    if len(words) > 11:
        first = " ".join(words[:11])
    sc = scenario_for(entry)
    return (keep_acronyms(first[0].upper() + first[1:]) + " for " + sc["subject"]
            + " — we're looking at " + sc["driver"] + ".")


def findings_block(entry: dict) -> dict:
    """The agent's answer, with a real scenario in it.

    Structured the way the reference structures it — an opening sentence, two
    labelled sections of short bullets, a highlighted callout with a Source
    line and a closing question — and populated with the synthetic scenario for
    this entry's industry. Concrete figures, plainly synthetic, exactly as the
    professional recordings do it. No slots reach the picture.
    """
    sc = scenario_for(entry)
    srcs = [x.replace("Connects to ", "").replace(
        "Runs on what the operator already has open — no additional configuration",
        "the systems already in use") for x in sources_from(entry)]
    acts = [keep_acronyms(a) for a in
            actions_from(entry.get("description", ""), entry.get("business_value"), entry)]

    first = imperative(acts[0]) if acts else "do the work"
    intro = (f"I'll {first[0].lower() + first[1:]} for {sc['subject']}, working "
             f"against {sc['driver']}. Reading {sc['systems']} before I propose "
             f"anything.")

    current = [
        f"Scope: {sc['volume']}",
        f"Current: {sc['metric']}",
        f"Goal: close the gap to {sc['target']}",
        f"Window: {sc['window']}",
    ]
    # "What I checked" answers where the answer came from. Listing the agent's
    # own capabilities there — "Handle account intelligence" — restates the
    # heading instead of grounding it.
    checks = [f"{keep_acronyms(x)} — read, not assumed" for x in srcs[:3]] or [
        "Verified against the source before reporting"]
    checks.append("Anything I could not verify is called out below")

    return {
        "intro": intro,
        "sections": [
            {"label": "Current position", "items": current},
            {"label": "What I checked", "items": checks[:4]},
        ],
        "callout": {
            # "conversion below target, against the conversion target" said
            # the same thing twice; the constraint alone is the finding.
            "headline": f"Biggest constraint: {sc['metric']}",
            "source": f"Source: {sc['systems']}",
            "question": "Shall I show the plan?",
        },
    }


def risk_block(entry: dict) -> dict:
    """The third exchange: what the agent will not do without being told.

    Qualitative like everything else here — the point is the guardrail, not a
    number we cannot stand behind.
    """
    sc = scenario_for(entry)
    named = named_systems(entry) or ["the source systems"]
    return {
        "intro": f"Three things I would watch on {sc['subject']}.",
        "sections": [
            {"label": "Risks", "items": [
                f"Stale inputs — {named[0]} may lag the working picture",
                "Edge cases the source data does not describe",
                "A recommendation that reads confident but is thinly evidenced",
            ]},
            {"label": "How I cover them", "items": [
                "Cite the record behind every line, so it can be checked",
                "Flag low-evidence items rather than smoothing over them",
                "Stop and ask before anything is written back",
            ]},
        ],
        "callout": {
            "headline": "You approve each step; nothing changes on its own",
            "source": f"Source: {sc['systems']}",
            "question": "Want me to start with the quick wins?",
        },
    }


def plan_block(entry: dict) -> list[str]:
    """The follow-up turn: a plan made of the entry's own steps."""
    acts = actions_from(entry.get("description", ""), entry.get("business_value"), entry)
    steps = []
    for i, a in enumerate(acts[:3], 1):
        steps.append(f"{i}. {as_display(imperative(a))}")
    steps.append(f"{len(steps) + 1}. Confirm the result against the source system")
    steps.append(f"{len(steps) + 1}. Hand back the artifact, and the reasoning "
                 f"behind it")
    return steps


def narration_for(act: str, entry: dict, name: str, seconds: float) -> str:
    """The narration for one act, on the reference's own template.

    Reverse-engineered from the transcript of the professional recording
    (media/reference-transcript.json, analysed in media/REFERENCE-ANALYSIS.md).
    Three things that measurement alone never surfaced:

      * The reference is a CUSTOMER NARRATIVE, not a description. It never
        mentions how it was made. Before/after, escalating asks, business
        results.
      * 2.1 words per second including pauses — a measured read, not a rushed
        one. Budgeting 3.49 produced narration that races the picture.
      * Speech starts at 9.4s. The title card and the opening of the b-roll are
        deliberately silent.
    """
    inds = entry.get("industries") or []
    if not inds and entry.get("category"):
        inds = [str(entry["category"]).replace("_", " ")]
    industry = (inds[0] if inds else "organisations").lower()
    if industry in ("cross-industry", "cross industry", "general", "aggregated", ""):
        industry = "teams"
    # "manufacturing get guided assistance" — a mass noun in a plural-actor
    # slot. The reference says "manufacturers get".
    ACTORS = {"manufacturing": "manufacturers", "healthcare": "care teams",
              "financial services": "financial services teams",
              "retail": "retailers", "professional services": "services firms",
              "energy": "energy operators", "b2b sales": "sales teams",
              "human resources": "HR teams", "it management": "IT teams",
              "teams": "teams", "organisations": "organisations"}
    actors = ACTORS.get(industry, industry if industry.endswith("s")
                        else industry + " teams")
    persona = ((entry.get("personas") or entry.get("audience") or ["manager"])[0])
    surface_name = (entry.get("surface") or "Microsoft Teams")
    srcs = [x.replace("Connects to ", "") for x in sources_from(entry)]
    # "pulls data from Teams … engages you directly in Teams" reads as a
    # mistake. The surface is where the operator meets it, not a source.
    srcs = [x for x in srcs if x.split(" —")[0] not in surface_name] or srcs
    acts_ = [keep_acronyms(a) for a in
             actions_from(entry.get("description", ""), entry.get("business_value"), entry)]
    values = [keep_acronyms(v) for v in (entry.get("business_value") or [])]
    surface = surface_name
    # The action lands after "needs to", so it must be a bare verb phrase.
    primary = imperative(acts_[0]) if acts_ else "do the work"
    primary = primary[0].lower() + primary[1:] if primary else "do the work"

    # 2.1 w/s, filled to 94% of the act — the reference's own coverage.
    budget = int(seconds * 2.1 * 0.94)
    parts: list[str] = []

    def take(*chunks):
        for c in chunks:
            c = (c or "").strip().rstrip(".")
            if not c:
                continue
            if len(" ".join(parts + [c]).split()) > budget:
                continue
            # A chunk that begins lower-case is a CONTINUATION of the previous
            # clause, not a new sentence. Punctuating it as one produced
            # "…gather insights. piecing the picture together by hand."
            if parts and c[0].islower():
                parts[-1] = parts[-1].rstrip(".") + ", " + c + "."
            else:
                parts.append(c if c[-1] in "?!" else c + ".")

    if act == "problem":
        # Silent until 9.4s by design; this act only carries the premise.
        named = named_systems(entry)
        source_clause = (f"It pulls data from {' and '.join(named[:2])}"
                         if named else "It reads the systems you already work in")
        take(f"There's an agent to guide {actors} through these processes",
             source_clause,
             f"engages you directly in {surface}",
             "and delivers targeted recommendations in the flow of the work")
    elif act == "overview":
        take(f"Let's say a {persona.lower()} needs to {primary}",
             "Before, they would have needed to jump across multiple systems to "
             "manually gather insights",
             "piecing the picture together by hand, and hoping nothing moved "
             "while they worked",
             "Now, in an instant, an agent can deliver a clear snapshot of the "
             "metrics that matter",
             "and automatically highlight what needs attention first")
    elif act == "walkthrough":
        second = acts_[1] if len(acts_) > 1 else "go further"
        take(f"But what if the {persona.lower()} wants to go a step further?",
             f"The agent handles the analysis and offers a set of targeted "
             f"recommendations right in their workflow",
             f"Work like this used to require cross-referencing different "
             f"systems by hand",
             ("Now, with unified data context across "
              + " and ".join(named_systems(entry)[:2]) + ", the agent can "
              "rapidly generate a phased plan with quick wins"
              if named_systems(entry) else
              "Now, with one unified data context, the agent can rapidly "
              "generate a phased plan with quick wins"),
             "For risk mitigation, the agent helps as well, outlining a strategy "
             "that keeps the work on track",
             "When the detail is needed, they simply ask, and the agent quickly "
             "compiles a clear summary",
             f"It can {second[0].lower() + second[1:]} in the same conversation, "
             f"without anyone switching tools",
             "Finally, the agent creates a monitoring plan, so teams keep the "
             "effort aligned to the metrics they are measured on",
             f"With {name}, {actors} get guided assistance embedded directly "
             f"into their workflows")
    elif act == "close":
        if len(values) >= 2:
            take("The result?",
                 ", ".join(v[0].lower() + v[1:] for v in values[:2]) +
                 (f", and better {values[2][0].lower() + values[2][1:]}"
                  if len(values) > 2 else ""))
        else:
            take("The result? Work that moves faster, stays consistent, and "
                 "holds the same standard every time it runs")
        # Verbatim from the reference. Every recording ends this way.
        take("Get started on your agentic journey today",
             "Talk to your Microsoft representative to learn more")
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
        {"act": "title", "start": 0.0, "end": 7.3, "shot": "Microsoft logo, white field",
         "on_screen": title_lines, "narration": ""},
        {"act": "problem", "start": 7.3, "end": 22.0, "shot": f"B-roll — {broll}",
         "on_screen": [], "narration": narration_for("problem", entry, name, 13.5)},
        {"act": "overview", "start": 22.0, "end": 42.75,
         "shot": "Agent overview card — three gradient panels on dark field",
         "panels": {
             "Sources": sources_from(entry),
             "Flow of work": [entry.get("surface") or SURFACE_BY_TIER["brainstem"]],
             # Panel lines are read, not spoken into a clause, so they are
             # sentence-cased here rather than left in the infinitive form the
             # narration slots need.
             "Actions": [as_display(a) for a in actions_from(
                 entry.get("description", ""), entry.get("business_value"), entry)],
         },
         "narration": narration_for("overview", entry, name, 20.0)},
        {"act": "walkthrough", "start": 42.75, "end": 113.5,
         "shot": "Laptop-framed chat surface",
         "turns": [
             {"role": "operator", "text": prompt_from(entry)},
             {"role": "agent", "heading": name,
              "rich": findings_block(entry),
              "agent_call": entry.get("tool_name") or entry.get("slug")},
             {"role": "operator", "text": "Show me the plan."},
             {"role": "agent", "heading": "Recommended plan",
              # The heading names the message; the section label names what is
              # inside it. Repeating the heading two lines below itself read as
              # an unfinished template.
              "rich": {"intro": "Phased, quick wins first.",
                       "sections": [{"label": "Steps",
                                     "items": plan_block(entry)}],
                       "callout": {"headline": ("Phased over " +
                                    scenario_for(entry)["window"] +
                                    ", starting with the quick wins"),
                                   "source": "Nothing is written back without confirmation",
                                   "question": "Approve and I'll proceed."}},
              "agent_call": entry.get("tool_name") or entry.get("slug")},
             # A third exchange, because the laptop shot runs about seventy
             # seconds and two exchanges left more than half of it on a frozen
             # frame. The reference plays six; this is the shape of the third.
             {"role": "operator", "text": "What could go wrong?"},
             {"role": "agent", "heading": "Risks and how I would cover them",
              "rich": risk_block(entry),
              "agent_call": entry.get("tool_name") or entry.get("slug")},
         ],
         "narration": narration_for("walkthrough", entry, name, 78.0)},
        {"act": "close", "start": 113.5, "end": 132.4,
         "shot": "Dark card, gradient CTA panel",
         "narration": narration_for("close", entry, name, 17.0),
         "on_screen": CLOSE_CTA + ([f"{entry.get('ref')} · {entry.get('license')}"]
                                   if kind == "skill" and entry.get("license") else [])},
    ]

    # Every placeholder is a remix point. A seller fills these in with their own
    # customer's scenario and the generic demo becomes theirs — which is the
    # difference between a video someone watches and a video someone presents.
    # Remix points. Previously these were the [operator supplies] markers; with
    # those gone the swappable material is the SCENARIO — the subject, the
    # driver, the systems. That is what a seller replaces to make the demo
    # their customer's, and it is why the film never needed mail-merge fields
    # on screen to be customisable.
    sc = scenario_for(entry)
    slots = [
        {"path": "scenario.subject", "label": "What the demo is about",
         "value": sc["subject"]},
        {"path": "scenario.driver", "label": "What is driving the work",
         "value": sc["driver"]},
        {"path": "scenario.systems", "label": "Systems it reads",
         "value": sc["systems"]},
        {"path": "scenario.window", "label": "Timeframe", "value": sc["window"]},
    ]

    return {
        "schema": SCHEMA,
        "format_version": FORMAT_VERSION,
        "remix": {
            "slot_count": len(slots),
            "slots": slots,
            "scenario": sc,
            "how": ("Replace the scenario below with your own customer's and "
                    "this stops being a generic demo and becomes yours. The acts, "
                    "timings, and the Agent Calls line stay fixed — those are the "
                    "format and the checkable claim."),
            "rule": ("The shipped film states no figures, because these are "
                     "demonstrations rather than results. Substitute real numbers "
                     "only if you can stand behind them — a personalised demo "
                     "carries more weight, which is exactly why an invented "
                     "number in one does more damage."),
        },
        "format_doc": "media/RAPPVISION.md",
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "subject": {"slug": entry["slug"], "kind": kind, "ref": entry.get("ref"),
                    "display_name": name, "category": category},
        "runtime_seconds": ACTS[-1][2],
        "status": "storyboard",
        "approval": {
            "required_before_render": True,
            "note": ("A storyboard is a script, not footage. Every claim is "
                     "qualitative rather than invented — a demo that fabricates a "
                     "metric teaches the viewer something false, so this script "
                     "says an agent accelerates a task and never says by how "
                     "much. A human approves the script before anything is "
                     "rendered."),
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
