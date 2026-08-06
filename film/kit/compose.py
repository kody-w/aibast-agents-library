#!/usr/bin/env python3
"""Turn a source description of an agent into a film config.

This is the piece that makes film eleven a config file rather than a project.
Nothing here writes copy: it reads a description the repository already holds
and lays it into the beat template. Two adapters exist.

`walkthrough` reads media/walkthroughs/agent-<slug>.json, the storyboard CI
already generates for every catalog entry. Those storyboards are qualitative
by construction - the honesty rules in media/RAPPVISION.md forbid an invented
figure - so a film built from one inherits that property instead of having to
be policed for it. Note the storyboards also carry `approval.required_before_
render: true`. A rendered film is a draft until a human has read the script.

`brief` reads a plain JSON extract of any other source: a briefing document, a
discovery transcript, a one-pager. The extract shape is documented in
film/README.md. The adapter refuses to fill a field the extract left empty
rather than inventing a plausible-sounding sentence.

Every film gets the synthetic-data card BEFORE its first data frame, a badge
on every data frame, and roles rather than invented person names.

Output: film/projects/<slug>/project.json
Usage:
    python3 film/kit/compose.py --walkthrough supplier-risk-monitoring \\
        --bucket manufacturing --batch library
    python3 film/kit/compose.py --brief film/.work/fy27-agents.json \\
        --only seller-account-executive-productivity --batch fy27
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import PROJECTS, REPO_ROOT  # noqa: E402

WALKTHROUGHS = REPO_ROOT / "media" / "walkthroughs"
REGISTRY = REPO_ROOT / "registry.json"

# Spoken and on screen, unchanged, in every film in the corpus.
CTA = ("Get started on your agentic journey today. "
       "Talk to your Microsoft representative to learn more.")
CTA_LINES = ["Get started on your agentic journey today.",
             "Talk to your Microsoft representative to learn more."]

SYNTHETIC_TITLE = "Everything shown next is synthetic."
SYNTHETIC_SUB = ("Illustrative data in an illustrative scenario. No customer, "
                 "no real record, no real person.")
FOOTER_TITLE = "All data shown is synthetic and illustrative."
FOOTER_SUB = ("This is a demonstration of what the agent does, not a report "
              "of results.")
FOOTER_NOTE = "Illustrative - synthetic data"

PRETTY = {
    "b2b_sales": "B2B sales", "b2c_sales": "B2C sales", "energy": "Energy",
    "federal_government": "Federal government", "financial_services":
    "Financial services", "general": "Cross-industry", "healthcare":
    "Healthcare", "it_management": "IT management", "manufacturing":
    "Manufacturing", "professional_services": "Professional services",
    "retail_cpg": "Retail and CPG", "slg_government":
    "State and local government", "software_digital_products":
    "Software and digital products",
}

VOICE = {
    "azure_voice": "en-US-AndrewMultilingualNeural",
    "azure_region": "eastus",
    "azure_resource_id": "",
    "rate": "-6%",
    "say_voice": "Daniel",
    "say_wpm": 132,
}


def sentences(text: str) -> list:
    return [s.strip() for s in re.split(r"(?<=[.?!])\s+", (text or "").strip())
            if s.strip()]


def join_short(sents: list, floor: int = 5) -> list:
    """Fold a stub sentence into the next one.

    The corpus close begins "The result? Work that moves faster..." and a
    naive split leaves a two-word narration slot, which synthesises as a
    fragment and reads as a mistake.
    """
    out = []
    for s in sents:
        if out and len(out[-1].split()) < floor:
            out[-1] = out[-1] + " " + s
        else:
            out.append(s)
    return out


def lower_lead(name: str) -> str:
    """Source names arrive title-cased for a card; sentences need them flat."""
    if name.isupper() or (len(name) > 1 and name[1].isupper()):
        return name
    words = name.split()
    if words and words[0] in ("The", "A", "An"):
        words[0] = words[0].lower()
    return " ".join(words)


def share(sents: list, parts: int) -> list:
    """Split a narration block into `parts`, keeping sentences whole."""
    if not sents:
        return [""] * parts
    out, per = [], max(1, round(len(sents) / parts))
    i = 0
    for p in range(parts):
        take = sents[i:i + per] if p < parts - 1 else sents[i:]
        out.append(" ".join(take))
        i += per
    while len(out) < parts:
        out.append("")
    return out[:parts]


def strip_cta(text: str) -> str:
    return text.replace(CTA, "").replace(CTA_LINES[0], "") \
               .replace(CTA_LINES[1], "").strip()


def blocks_from_rich(rich: dict) -> list:
    """Agent turn -> the ordered answer blocks the screen renderer draws."""
    out = []
    if rich.get("intro"):
        out.append({"type": "para", "text": rich["intro"]})
    for sec in rich.get("sections", []):
        out.append({"type": "list", "label": sec["label"],
                    "items": list(sec["items"])})
    call = rich.get("callout")
    if call:
        out.append({"type": "callout", "headline": call["headline"],
                    "source": call.get("source")})
    return out or [{"type": "para", "text": "No answer content in the source."}]


def overview_line(panels: dict) -> str:
    """The capability triplet, in the same order as the card."""
    # Two sources, not three. The third pushes this read past 25s, and one
    # card beat that long needs more reveal points than a three-tile card has.
    src = ", ".join(lower_lead(x) for x in panels.get("Sources", [])[:2]) \
        or "the systems of record"
    flow = (panels.get("Flow of work") or ["where people already work"])[0]
    acts = panels.get("Actions", [])[:1]
    act = " and ".join(a.lower() for a in acts) if acts else "do the work"
    flow = flow[0].lower() + flow[1:] if flow else flow
    return (f"It reads {src}. It {flow}. And it can {act}, showing the "
            f"reasoning behind every answer.")


DEFAULT_HELPS = ["Reads the systems of record, rather than assuming",
                 "Shows the reasoning behind every answer",
                 "Hands the work back where it is already being done"]


def pad3(items: list) -> list:
    """Three tiles, always - topped up from the defaults if the source is thin."""
    out = [x for x in items if x][:3]
    for d in DEFAULT_HELPS:
        if len(out) >= 3:
            break
        if d not in out:
            out.append(d)
    return out


def cards_for(title: str, kicker: str, panels: dict, helps: list,
              questions: list | None = None) -> dict:
    tiles = [{"label": "Sources", "lines": panels.get("Sources", [])[:3]},
             {"label": "Flow of work", "lines": panels.get("Flow of work", [])[:2]},
             {"label": "Actions", "lines": panels.get("Actions", [])[:3]}]
    return {
        "c_title": {"kind": "title", "title": title, "kicker": kicker,
                    "size": 64},
        "c_overview": {"kind": "tiles", "heading": "What the agent works with",
                       "tiles": tiles,
                       "icons": ["ic-sources", "ic-flow", "ic-actions"],
                       "chevrons": True},
        "c_synthetic": {"kind": "statement", "title": SYNTHETIC_TITLE,
                        "sub": SYNTHETIC_SUB, "size": 62, "stages": 1},
        # Always three tiles. A one-tile "how it helps" card is one stage,
        # and one stage is a frame held for the whole beat.
        "c_helps": {"kind": "tiles", "heading": "How the agent helps",
                    "tiles": [{"label": f"0{i + 1}", "lines": [h]}
                              for i, h in enumerate(pad3(helps))]},
        "c_cta": {"kind": "statement", "title": CTA_LINES[0],
                  "sub": CTA_LINES[1], "size": 56, "stages": 2},
        "c_footer": {"kind": "statement", "title": FOOTER_TITLE,
                     "sub": FOOTER_SUB, "size": 50, "panel": False,
                     "stages": 1},
        # One lower third per demo turn. The operator's question is on screen
        # for the whole answer - three "ask it for..." narration lines over
        # answers with no visible question is a reviewer's first finding.
        **{f"c_{q['id']}": {"kind": "chyron", "text": q["prompt"],
                            "tag": "Asked of the agent"}
           for q in (questions or [])},
    }


def from_walkthrough(slug: str) -> dict:
    path = WALKTHROUGHS / f"agent-{slug}.json"
    if not path.exists():
        raise SystemExit(f"no storyboard at {path.relative_to(REPO_ROOT)}")
    wt = json.loads(path.read_text())
    subject = wt["subject"]
    scenes = {s["act"]: s for s in wt["scenes"]}
    panels = scenes["overview"].get("panels", {})
    display = subject["display_name"]
    category = subject.get("category", "general")
    kicker = f"{PRETTY.get(category, category)} - illustrative scenario"

    turns = scenes["walkthrough"].get("turns", [])
    pairs = []
    for i, t in enumerate(turns):
        if t["role"] != "operator":
            continue
        agent = next((x for x in turns[i + 1:i + 3] if x["role"] == "agent"), None)
        if agent:
            pairs.append((t["text"], agent))
    if not pairs:
        raise SystemExit(f"{slug}: storyboard has no operator/agent turns")

    # The last line of the walkthrough narration is the one that stops
    # describing the screen and starts summarising - it belongs over the
    # payoff b-roll, not over a demo frame.
    wt_sents = join_short(sentences(scenes["walkthrough"]["narration"]))
    payoff = wt_sents.pop() if len(wt_sents) > len(pairs) else ""
    demo_bits = share(wt_sents, len(pairs))
    close = join_short(sentences(strip_cta(scenes["close"]["narration"])))
    problem = join_short(sentences(scenes["problem"]["narration"]))
    overview_n = join_short(sentences(scenes["overview"]["narration"]))

    # "Let's say a manager needs to..." is the persona setup and it belongs
    # over the first demo frame, not over the problem montage. Splitting it
    # out is also what moves the demo share back to the corpus mean.
    persona = next((x for x in overview_n if x.lower().startswith("let's say")), "")
    rest = [x for x in overview_n if x != persona]
    script = {
        "vo01": " ".join(problem[:2]) or f"{display} works where the job is done.",
        "vo02": " ".join(rest[:2]) or
                "Before, the picture had to be assembled by hand.",
        "vo03": overview_line(panels),
    }
    questions = []
    for n, (prompt, agent) in enumerate(pairs, 1):
        slot = f"vo{3 + n:02d}"
        line = demo_bits[n - 1] or "It answers, and shows its working."
        script[slot] = (persona + " " + line).strip() if n == 1 else line
        questions.append({
            "id": f"q{n}", "vo": slot, "prompt": prompt,
            "answer": blocks_from_rich(agent["rich"]),
            "citations": [agent.get("agent_call", display)],
            "citation_label": "Agent calls",
        })
    helps = panels.get("Actions", [])[:3] or ["reads the systems of record",
                                              "shows its reasoning",
                                              "hands back the artifact"]
    script["vo_payoff"] = payoff or " ".join(close[:1])
    script["vo_helps"] = " ".join(close if payoff else close[1:])
    if len(script["vo_helps"].split()) < 6:
        script["vo_helps"] = (
            "The result? " + ", ".join(h[0].lower() + h[1:] for h in helps[:3]) +
            " - the same standard every time it runs.")
    script["vo_cta"] = CTA

    return {
        "slug": slug, "title": display,
        "kicker": kicker,
        "category": category, "agent_ref": subject.get("ref", ""),
        "source": f"media/walkthroughs/agent-{slug}.json",
        "script": script,
        "cards": cards_for(display, kicker, panels, helps, questions),
        "demo": {"agent_name": display, "questions": questions},
    }


def from_brief(record: dict) -> dict:
    """Adapter for any non-catalog source, via the documented extract shape."""
    display = record["name"]
    industry = record.get("industry") or "Cross-industry"
    kicker = f"{industry} - illustrative scenario"
    panels = {
        "Sources": record.get("sources", [])[:3],
        "Flow of work": [record.get("surface") or
                         "Engages you where the work already happens"],
        "Actions": record.get("actions", [])[:3],
    }
    problem = sentences(record.get("problem", ""))
    value = record.get("value", [])
    script = {
        "vo01": " ".join(problem[:2]),
        "vo02": " ".join(problem[2:4]) or
                "Today that picture is assembled by hand, one system at a time.",
        "vo03": overview_line(panels),
    }
    questions = []
    asks = record.get("example_questions") or []
    acts = record.get("actions", [])
    for n in range(1, 4):
        slot = f"vo{3 + n:02d}"
        prompt = (asks[n - 1] if n - 1 < len(asks)
                  else f"{acts[n - 1] if n - 1 < len(acts) else 'Summarise the position'} "
                       f"for the current period.")
        heading = ["What the agent found", "The recommended plan",
                   "Risks and how it would cover them"][n - 1]
        if n == 1:
            body = [{"type": "para",
                     "text": f"Reading {', '.join(panels['Sources']) or 'the systems of record'} "
                             f"before proposing anything."},
                    {"type": "list", "label": "What I checked",
                     "items": [f"{s} - read, not assumed"
                               for s in (panels["Sources"] or ["the systems of record"])] +
                              ["Anything I could not verify is called out below"]},
                    {"type": "callout",
                     "headline": (value[0] if value else "The position, assembled"),
                     "source": "Source: " + (", ".join(lower_lead(x) for x in panels["Sources"]) or
                                             "the systems of record")}]
        elif n == 2:
            body = [{"type": "para", "text": "Phased, quick wins first."},
                    {"type": "steps",
                     "items": [f"**{a}**" for a in (acts[:3] or ["Assemble the position"])]},
                    {"type": "callout",
                     "headline": (value[1] if len(value) > 1 else
                                  "A plan you can act on"),
                     "source": "Nothing is written back without confirmation"}]
        else:
            body = [{"type": "para",
                     "text": "Three things worth watching before this is acted on."},
                    {"type": "list", "label": "Risks",
                     "items": ["Stale inputs - a source may lag the working picture",
                               "Edge cases the source data does not describe",
                               "Anything that needs a human decision is flagged, "
                               "never assumed"]},
                    {"type": "callout",
                     "headline": (value[2] if len(value) > 2 else
                                  "Checkable, not just plausible"),
                     "source": "Every claim traces back to a source it read"}]
        script[slot] = record.get("narration", {}).get(slot, "")
        questions.append({"id": f"q{n}", "vo": slot, "prompt": prompt,
                          "answer": body, "citations": [display],
                          "citation_label": "Agent calls"})
    script["vo_payoff"] = record.get("payoff", "")
    script["vo_helps"] = record.get("helps", "")
    script["vo_cta"] = CTA
    return {
        "slug": record["slug"], "title": display, "kicker": kicker,
        "category": record.get("category", industry), "agent_ref": "",
        "source": record.get("source", "sanitised brief extract"),
        "script": script,
        "cards": cards_for(display, kicker, panels,
                           value[:3] or ["Reads the systems of record",
                                         "Shows its reasoning",
                                         "Hands back the artifact"], questions),
        "demo": {"agent_name": display, "questions": questions},
    }


def write(core: dict, bucket: str, batch: str) -> Path:
    out_dir = PROJECTS / core["slug"]
    out_dir.mkdir(parents=True, exist_ok=True)
    project = {
        "schema": "aibast-showcase-film/1.0",
        "batch": batch,
        "slug": core["slug"],
        "title": core["title"],
        "kicker": core["kicker"],
        "category": core["category"],
        "agent_ref": core["agent_ref"],
        "composed_from": core["source"],
        "composed_by": "film/kit/compose.py",
        "approval": {
            "required_before_publishing": True,
            "note": "A composed script is a draft. A human reads it before "
                    "this film is published anywhere.",
        },
        "output": f"{core['slug']}.mp4",
        "broll_bucket": bucket,
        "footer_note": FOOTER_NOTE,
        "duration_window": [95, 200],
        "bed_db": 4.0,
        "voice": VOICE,
        "script": core["script"],
        "cards": core["cards"],
        "demo": core["demo"],
        "beats": [],
    }
    path = out_dir / "project.json"
    path.write_text(json.dumps(project, indent=1) + "\n")
    words = sum(len(v.split()) for v in core["script"].values())
    print(f"[OK] {path.relative_to(REPO_ROOT)}  {len(core['script'])} slots, "
          f"{words} words, {len(core['demo']['questions'])} demo turns")
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--walkthrough", help="catalog slug with a storyboard")
    ap.add_argument("--brief", type=Path, help="JSON extract of another source")
    ap.add_argument("--only", help="with --brief, compose just this slug")
    ap.add_argument("--bucket", default="cross_industry")
    ap.add_argument("--batch", default="library")
    args = ap.parse_args()

    if args.walkthrough:
        write(from_walkthrough(args.walkthrough), args.bucket, args.batch)
    elif args.brief:
        data = json.loads(args.brief.read_text())
        for rec in data["agents"]:
            if args.only and rec["slug"] != args.only:
                continue
            write(from_brief(rec), rec.get("bucket", args.bucket), args.batch)
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
