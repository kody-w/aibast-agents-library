#!/usr/bin/env python3
"""Render the demo segment as a sequence of agent-surface stills.

Two ways exist to fill the demo slot. Capturing a live agent is the honest one
and film/CAPTURE.md is the law for it. This module is the other one: a
deterministic renderer that draws the same surface from data in project.json,
for when there is no agent to point at, no network, or the scenario is
explicitly illustrative.

It is not a screenshot and must never be passed off as one. Every frame it
draws carries a badge in the panel header, the copy says "built to answer in
Microsoft 365 Copilot" rather than "answers in", and the film's disclaimer
card lands before the first frame of it — not after.

Each question renders as several stages: the prompt alone, then the answer
arriving a block at a time, then the citations. That is what stops the demo
from being a slide, and it is what keeps every held frame under the five-second
gate. Citations appear only on the final stage, because in the real product
they resolve only when a message completes.

The transcript is anchored to the bottom of the pane and slides up as the
answer grows, the way the product scrolls to its newest content. That is a
correctness requirement as much as a styling one - see render_question().

Output: film/projects/<slug>/work/screens/<qid>_<n>.png
Usage:
    python3 film/kit/screens.py --project supplier-risk-watch
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (BRAND, H, W, font, load_project, mono,  # noqa: E402
                    require_tools, rgb, wrap)

G = BRAND["geometry"]
SX, SY, SW, SH = G["screen_rect"]
PAD = 44
BADGE = "ILLUSTRATIVE - SYNTHETIC DATA"


def _rich(d, x, y, text, size, colour, maxw, bold_colour=None):
    """Draw one line of text where **spans** are emphasised. Returns new y."""
    reg, bold = font(size, "regular"), font(size, "demi")
    words, cur, lines = text.split(" "), [], []
    # Wrap on the regular metric plus a small allowance for the bold runs.
    plain = text.replace("**", "")
    for ln in wrap(d, plain, reg, maxw):
        lines.append(ln)
    # Re-walk the original string, emitting per-line with emphasis preserved.
    remaining = text
    for ln in lines:
        cx = x
        target = ln
        consumed = 0
        emph = remaining.count("**", 0, 0)
        i = 0
        buf, is_bold = "", False
        src = remaining
        while consumed < len(target) and i < len(src):
            if src.startswith("**", i):
                if buf:
                    f = bold if is_bold else reg
                    d.text((cx, y), buf, font=f,
                           fill=(bold_colour or colour) if is_bold else colour)
                    cx += d.textlength(buf, font=f)
                    buf = ""
                is_bold = not is_bold
                i += 2
                continue
            buf += src[i]
            consumed += 1
            i += 1
        if buf:
            f = bold if is_bold else reg
            d.text((cx, y), buf, font=f,
                   fill=(bold_colour or colour) if is_bold else colour)
        remaining = src[i:].lstrip(" ")
        y += int(size * 1.42)
    return y


def _stage_bg():
    """The violet stage the reference stands its device on.

    Not decoration: film/GRAMMAR.md classifies a frame as demo by the
    violet-dominant border, so a demo shot on a flat navy stage is a demo the
    harvester and the grammar checks cannot see. Sampled from
    film/corpus/videos/ask-hr-agent.mp4 at t=130s - #8300F4 top-left falling
    to #150951 bottom-right.
    """
    from PIL import Image
    import cards
    g = cards.grad_panel(W, H, 0, [list(rgb("stage_violet")),
                                   list(rgb("stage_indigo"))])
    return Image.new("RGB", (W, H), rgb("stage_indigo")), g


def _panel(agent_name: str):
    """The surface chrome: violet stage, device frame, panel, composer, badge."""
    from PIL import ImageDraw
    img, g = _stage_bg()
    img.paste(g, (0, 0), g)
    d = ImageDraw.Draw(img)
    bp, br = G["bezel_pad"], G["bezel_radius"]
    d.rounded_rectangle([SX - bp, SY - bp, SX + SW + bp, SY + SH + bp], br,
                        fill=rgb("bezel"))
    d.rounded_rectangle([SX, SY, SX + SW, SY + SH], 14, fill=rgb("paper"))
    # header
    d.rectangle([SX, SY, SX + SW, SY + 62], fill=rgb("surface"))
    d.rounded_rectangle([SX, SY, SX + SW, SY + 30], 14, fill=rgb("surface"))
    d.line([(SX, SY + 62), (SX + SW, SY + 62)], fill=rgb("line"), width=2)
    d.text((SX + PAD, SY + 18), agent_name, font=font(26, "demi"), fill=rgb("ink"))
    bf = font(BRAND["type"]["sizes"]["badge"], "demi")
    bw = d.textlength(BADGE, font=bf)
    bx = SX + SW - PAD - bw - 24
    d.rounded_rectangle([bx, SY + 15, bx + bw + 24, SY + 47], 16, fill=rgb("amber"))
    d.text((bx + 12, SY + 21), BADGE, font=bf, fill=rgb("white"))
    # composer
    cy = SY + SH - 78
    d.rounded_rectangle([SX + PAD, cy, SX + SW - PAD, cy + 52], 10,
                        fill=rgb("paper"), outline=rgb("line"), width=2)
    d.text((SX + PAD + 18, cy + 13), "Ask a question or describe what you need",
           font=font(23, "regular"), fill=rgb("muted"))
    return img, d


def _prompt(d, y: int, text: str) -> int:
    """The operator's question, right-aligned. It is always in frame."""
    f = font(28, "medium")
    maxw = int(SW * 0.62)
    lines = wrap(d, text, f, maxw - 56)
    bw = max(d.textlength(ln, font=f) for ln in lines) + 56
    bh = len(lines) * 36 + 30
    x1 = SX + SW - PAD
    x0 = x1 - bw
    d.rounded_rectangle([x0, y, x1, y + bh], 14, fill=rgb("blue"))
    for i, ln in enumerate(lines):
        d.text((x0 + 28, y + 15 + i * 36), ln, font=f, fill=rgb("white"))
    return y + bh + 30


def _agent_label(d, y: int, name: str) -> int:
    d.ellipse([SX + PAD, y, SX + PAD + 26, y + 26], fill=rgb("blue"))
    d.text((SX + PAD + 38, y + 1), name, font=font(24, "demi"), fill=rgb("muted"))
    return y + 42


def _thinking(d, y: int) -> int:
    f = font(27, "regular")
    d.text((SX + PAD, y), "Working on it...", font=f, fill=rgb("muted"))
    return y + 40


def _para(d, y: int, text: str) -> int:
    return _rich(d, SX + PAD, y, text, 29, rgb("ink"), SW - 2 * PAD,
                 bold_colour=rgb("ink")) + 12


def _table(d, y: int, cols: list, rows: list) -> int:
    hf, bf = font(22, "demi"), font(23, "regular")
    x0 = SX + PAD
    total = SW - 2 * PAD - 40
    widths = [int(total * c["w"]) for c in cols]
    d.rectangle([x0, y, x0 + sum(widths), y + 40], fill=rgb("surface"))
    cx = x0
    for c, w in zip(cols, widths):
        d.text((cx + 14, y + 10), c["label"], font=hf, fill=rgb("muted"))
        cx += w
    y += 40
    for r in rows:
        d.line([(x0, y), (x0 + sum(widths), y)], fill=rgb("line"), width=1)
        cx = x0
        for cell, w in zip(r, widths):
            colour = rgb("ink")
            txt = cell
            if txt.startswith("!"):
                colour, txt = rgb("red"), txt[1:]
            elif txt.startswith("~"):
                colour, txt = rgb("amber"), txt[1:]
            elif txt.startswith("+"):
                colour, txt = rgb("green"), txt[1:]
            f = bf if not txt.startswith("*") else font(23, "demi")
            txt = txt.lstrip("*")
            for j, ln in enumerate(wrap(d, txt, f, w - 28)[:2]):
                d.text((cx + 14, y + 10 + j * 28), ln, font=f, fill=colour)
            cx += w
        y += 10 + 28 * min(2, max(1, len(wrap(d, r[0], bf, widths[0] - 28)))) + 10
    d.line([(x0, y), (x0 + sum(widths), y)], fill=rgb("line"), width=1)
    return y + 22


def _list(d, y: int, label: str, items: list) -> int:
    """A labelled finding block - the shape the agent surface actually uses."""
    d.text((SX + PAD, y), label.upper(), font=font(22, "demi"), fill=rgb("blue"))
    y += 32
    bf = font(27, "regular")
    for it in items:
        d.ellipse([SX + PAD + 4, y + 10, SX + PAD + 12, y + 18], fill=rgb("blue"))
        y = _rich(d, SX + PAD + 28, y, it, 27, rgb("ink"), SW - 2 * PAD - 40,
                  bold_colour=rgb("ink")) + 4
    return y + 14


def _callout(d, y: int, headline: str, source: str | None) -> int:
    """The agent's own conclusion, set apart. Never a number it invented."""
    h = 84 if not source else 124
    d.rounded_rectangle([SX + PAD, y, SX + SW - PAD, y + h], 10,
                        fill=rgb("pale_blue"))
    d.rectangle([SX + PAD, y, SX + PAD + 6, y + h], fill=rgb("blue"))
    yy = _rich(d, SX + PAD + 26, y + 16, "**" + headline + "**", 28,
               rgb("navy"), SW - 2 * PAD - 60, bold_colour=rgb("navy"))
    if source:
        d.text((SX + PAD + 26, yy + 4), source, font=font(20, "regular"),
               fill=rgb("muted"))
    return y + h + 18


def _steps(d, y: int, items: list) -> int:
    nf, bf = font(23, "demi"), font(27, "regular")
    for i, it in enumerate(items, 1):
        d.rounded_rectangle([SX + PAD, y, SX + PAD + 32, y + 32], 8, fill=rgb("blue"))
        d.text((SX + PAD + 16 - d.textlength(str(i), font=nf) / 2, y + 6), str(i),
               font=nf, fill=rgb("white"))
        yy = _rich(d, SX + PAD + 50, y + 2, it, 27, rgb("ink"), SW - 2 * PAD - 60,
                   bold_colour=rgb("ink"))
        y = max(yy, y + 40) + 8
    return y + 10


def _citations(d, y: int, cites: list, label: str = "Agent calls") -> int:
    """The one frame that claims something checkable.

    It names the tool the catalog entry actually registers, and nothing else.
    An invented citation is worse than none - it teaches the viewer that the
    answer was sourced when it was not.
    """
    d.text((SX + PAD, y), label, font=font(21, "demi"), fill=rgb("muted"))
    y += 32
    f = font(20, "medium")
    cx = SX + PAD
    for i, c in enumerate(cites, 1):
        label = f"{i}  {c}"
        w = d.textlength(label, font=f) + 26
        if cx + w > SX + SW - PAD:
            cx = SX + PAD
            y += 38
        d.rounded_rectangle([cx, y, cx + w, y + 30], 8, fill=rgb("pale_blue"))
        d.text((cx + 13, y + 5), label, font=f, fill=rgb("blue_dark"))
        cx += w + 12
    return y + 44


def _sentences(text: str) -> list:
    import re
    return [x.strip() for x in re.split(r"(?<=[.?!])\s+", text.strip()) if x.strip()]


def _steps_of(b: dict) -> list:
    """The partial forms one block can be revealed in, shortest first."""
    if b["type"] in ("list", "steps") and len(b.get("items", [])) > 1:
        return [dict(b, items=b["items"][:k]) for k in range(1, len(b["items"]) + 1)]
    if b["type"] == "para":
        sents = _sentences(b["text"])
        if len(sents) > 1:
            return [dict(b, text=" ".join(sents[:k]))
                    for k in range(1, len(sents) + 1)]
    return [b]


def max_states(blocks: list) -> int:
    """How many distinct frames this answer can be revealed in, plus thinking.

    plan.py sizes a demo beat against this. Sizing it against duration alone
    asked for seven stages from an answer that could only make six, and the
    extra second went onto every hold.
    """
    return 1 + sum(len(_steps_of(b)) for b in blocks)


def reveal_states(blocks: list, want: int) -> list:
    """Every partial answer this question can show, downsampled to `want`.

    The maximal sequence reveals one block at a time and, inside a list block,
    one item at a time. A long read then gets more stages instead of a longer
    hold, which is the only way to satisfy the five-second gate without
    speeding the read up. The full answer is always the last state.
    """
    maximal = []
    shown = []
    for b in blocks:
        forms = _steps_of(b)
        for f in forms:
            maximal.append(shown + [f])
        shown = shown + [forms[-1]]
    if not maximal:
        maximal = [[]]
    want = max(2, min(want, len(maximal)))
    # Evenly spaced, always ending on the complete answer.
    idx = sorted({round(i * (len(maximal) - 1) / (want - 1))
                  for i in range(want)}) if want > 1 else [len(maximal) - 1]
    return [maximal[i] for i in idx]


TOP_Y = SY + 62 + 34
BOTTOM_Y = SY + SH - 78 - 26      # the composer's top edge, less a gap


def _transcript(d, y: int, q: dict, agent_name: str, state: list,
                thinking: bool, cites: bool) -> int:
    """Draw the conversation from `y` down. Returns the y it ended at."""
    y = _prompt(d, y, q["prompt"])
    y = _agent_label(d, y, agent_name)
    if thinking:
        return _thinking(d, y)
    for b in state:
        if b["type"] == "para":
            y = _para(d, y, b["text"])
        elif b["type"] == "table":
            y = _table(d, y, b["cols"], b["rows"])
        elif b["type"] == "steps":
            y = _steps(d, y, b["items"])
        elif b["type"] == "list":
            y = _list(d, y, b["label"], b["items"])
        elif b["type"] == "callout":
            y = _callout(d, y, b["headline"], b.get("source"))
    # Citations resolve only when the message completes. A mid-stream frame
    # that already shows them is a lie about how the product works.
    if cites and q.get("citations"):
        y = _citations(d, y, q["citations"], q.get("citation_label", "Agent calls"))
    return y


def _measure(q, agent_name, state, thinking, cites) -> int:
    from PIL import Image, ImageDraw
    scratch = Image.new("RGB", (W, H))
    return _transcript(ImageDraw.Draw(scratch), 0, q, agent_name, state,
                       thinking, cites)


def render_question(q: dict, agent_name: str, min_stages: int = 4) -> list:
    """Return the ordered stages for one question, thinking frame first.

    The conversation is anchored to the BOTTOM of the pane, against the
    composer, and slides up as the answer grows - which is what the product
    does when it scrolls to the newest content. It is also the only way the
    build is visible to the hold gate. Top-anchored, one extra bullet changes
    about 0.1 % of the frame, which is exactly freezedetect's floor: two demo
    stages that differed by a single list item read as one 8.2-second freeze
    on the first kit build. Sliding the whole transcript moves every line of
    it, so any real reveal is unmistakable.
    """
    stages = []
    plans = [(None, True, False)]
    states = reveal_states(q["answer"], max(2, min_stages - 1))
    for n, state in enumerate(states):
        plans.append((state, False, n == len(states) - 1))

    for state, thinking, cites in plans:
        h = _measure(q, agent_name, state or [], thinking, cites)
        img, d = _panel(agent_name)
        if h <= BOTTOM_Y - TOP_Y:
            _transcript(d, BOTTOM_Y - h, q, agent_name, state or [], thinking, cites)
        else:
            # Taller than the pane. Clamping to TOP_Y kept the OLDEST content
            # pinned and pushed the newest under the composer, where it was
            # clipped mid-sentence. A chat pane does the opposite: the newest
            # line stays against the composer and the oldest scrolls off the
            # top. Draw the whole transcript on its own layer and paste only
            # the window the pane can show.
            from PIL import Image, ImageDraw
            layer = Image.new("RGBA", (W, h + TOP_Y + 40), (0, 0, 0, 0))
            _transcript(ImageDraw.Draw(layer), 0, q, agent_name,
                        state or [], thinking, cites)
            window = layer.crop((0, h - (BOTTOM_Y - TOP_Y), W, h))
            img.paste(window, (0, TOP_Y), window)
        stages.append(img)
    return stages


def render(project: dict) -> dict:
    out_dir = project["_work"] / "screens"
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.png"):
        old.unlink()
    agent_name = project["demo"]["agent_name"]
    written = {}
    want = {b["question"]: b.get("stages", 4)
            for b in project.get("beats", []) if b.get("question")}
    for q in project["demo"]["questions"]:
        stages = render_question(q, agent_name, want.get(q["id"], 4))
        paths = []
        for i, img in enumerate(stages):
            p = out_dir / f"{q['id']}_{i}.png"
            img.save(p)
            paths.append(p.name)
        written[q["id"]] = paths
        print(f"[OK] {q['id']:6s} {len(paths)} stage(s)  {q['prompt'][:58]}")
    (out_dir / "index.json").write_text(json.dumps(written, indent=1))
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", required=True)
    args = ap.parse_args()
    require_tools()
    render(load_project(args.project))
    return 0


if __name__ == "__main__":
    sys.exit(main())
