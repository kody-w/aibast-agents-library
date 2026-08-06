#!/usr/bin/env python3
"""Render every still element of a film: title panel, statement cards, the
Sources / Flow of work / Actions overview, benefit tiles, chyrons and the
synthetic-data footer.

Cards are built as *stages*, not as single images. A card that holds one
unchanged frame for eleven seconds is dead air, and the gate fails at five, so
a statement card renders its title and then its supporting line, and a tile
card lights one tile at a time. That spotlight build is what the shipped
recordings do to keep a static card alive, and it is the reason the cards in
this kit are a list of PNGs rather than one PNG.

**A stage only counts if the hold detector can see it.** ffmpeg's
`freezedetect=n=-60dB` calls two frames identical when their mean absolute
luma difference is under 0.1 % of full scale. One extra line of body text is
about 0.12 % — right on the line, so it is detected on some cards and missed
on others, and a missed one silently doubles the hold. Measured on the first
kit build: two overview stages that differed by a single line of tile copy
read as one 7.7-second freeze. Every reveal step here therefore changes a
whole region - a tile's gradient, or the depth of the lozenge - not one line.
`card_capacity()` reports how many such steps a card can actually make, and
plan.py sizes the beat against it.

Everything is measured in brand.json. No colour or size is written here.

Output: film/projects/<slug>/work/cards/*.png
Usage:
    python3 film/kit/cards.py --project supplier-risk-watch
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (BRAND, FILM, H, REPO_ROOT, W, font, load_project,  # noqa: E402
                    require_tools, rgb, wrap)

JEWELS = REPO_ROOT / "media" / "jewels"
G = BRAND["geometry"]
S = BRAND["type"]["sizes"]


def _draw():
    from PIL import ImageDraw
    return ImageDraw


def stage(footer_note: str | None = None):
    """The card ground: navy, with the Microsoft mark and the footer note.

    Navy, not white. The 19 reference recordings put every full-screen card on
    #070E27 (sampled at ask-hr-agent t=50s, recorded in brand.json). A kit
    build that shipped white paper cards passed every gate and still did not
    look like the catalog, which is the whole reason the palette now lives in
    brand.json as measured data.
    """
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W, H), rgb("card_bg"))
    d = ImageDraw.Draw(img)
    q, ox, oy = 15, G["footer_mark_x"], H - 74
    for i, c in enumerate(BRAND["palette"]["four_square"]):
        d.rectangle([ox + (i % 2) * (q + 4), oy + (i // 2) * (q + 4),
                     ox + (i % 2) * (q + 4) + q, oy + (i // 2) * (q + 4) + q],
                    fill=tuple(c))
    d.text((ox + 2 * (q + 4) + 14, oy + 4), "Microsoft", font=font(24, "demi"),
           fill=rgb("card_muted"))
    if footer_note:
        f = font(22, "medium")
        d.text((W - 90 - d.textlength(footer_note, font=f), oy + 6), footer_note,
               font=f, fill=rgb("card_muted"))
    return img


def _lerp_stops(stops: list, t: float) -> tuple:
    """Colour at 0..1 along a list of RGB stops spaced evenly."""
    if t <= 0:
        return tuple(stops[0])
    if t >= 1:
        return tuple(stops[-1])
    span = 1.0 / (len(stops) - 1)
    i = min(int(t / span), len(stops) - 2)
    f = (t - i * span) / span
    a, b = stops[i], stops[i + 1]
    return tuple(int(x + (y - x) * f) for x, y in zip(a, b))


def grad_panel(w: int, h: int, radius: int, stops: list, diagonal: bool = True,
               dim: float = 0.0):
    """Rounded gradient panel with an alpha mask, in the corpus's colours.

    Drawn small and resized: a 96x96 gradient scaled up is indistinguishable
    from a per-pixel one at this size and renders a whole card in a blink
    rather than a second. `dim` blends the panel back towards the tile
    container so an unlit tile reads as waiting rather than as missing.
    """
    from PIL import Image, ImageDraw
    n = 96
    small = Image.new("RGB", (n, n))
    px = small.load()
    back = tuple(rgb("card_panel"))
    for y in range(n):
        for x in range(n):
            t = ((x + y) / (2 * (n - 1))) if diagonal else (x / (n - 1))
            c = _lerp_stops(stops, t)
            if dim:
                c = tuple(int(v + (b - v) * dim) for v, b in zip(c, back))
            px[x, y] = c
    grad = small.resize((w, h), Image.BILINEAR)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius, fill=255)
    grad.putalpha(mask)
    return grad


TILE_STOPS = ["grad_pink", "grad_magenta", "grad_violet"]


def _stops():
    return [list(rgb(k)) for k in TILE_STOPS]


def block(d, lines, fnt, cx, cy, fill, leading=None):
    lh = int(fnt.size * (leading or BRAND["type"]["leading"]))
    top = cy - (len(lines) * lh) // 2
    for i, ln in enumerate(lines):
        d.text((cx - d.textlength(ln, font=fnt) / 2, top + i * lh), ln,
               font=fnt, fill=fill)
    return top + len(lines) * lh


def statement_max_stages(spec: dict) -> int:
    """Distinct frames a statement card can make. Two, or one without a sub.

    Padding a statement card with repeats of itself does not buy a stage. The
    old renderer did that and grew an 8px accent rule a little further each
    time to keep the frames "different"; the hold detector cannot see 8px and
    the beat read as one long freeze. The lozenge growing to admit the
    supporting line is a change the detector can see, and there is exactly one
    of those.
    """
    return 2 if spec.get("sub") else 1


def statement_stages(title: str, kicker: str | None, sub: str | None,
                     size: int, panel: bool = True, footer_note=None,
                     stages: int = 2) -> list:
    """A statement card: the title in a gradient lozenge, then the sub line.

    The lozenge is anchored at its TOP and grows downward to admit the
    supporting line, so the title never moves - a build that shifts its own
    heading reads as a glitch - while the change is a whole band of gradient
    rather than one line of text, which is what the hold detector needs.
    """
    from PIL import ImageDraw
    out = []
    steps = [(kicker, title, None)]
    if sub:
        steps.append((kicker, title, sub))
    stages = max(1, min(stages, len(steps)))
    # A single-stage card shows the finished thing; there is no build to make.
    steps = steps[len(steps) - stages:] if stages < len(steps) else steps
    probe = stage(footer_note)
    pd = ImageDraw.Draw(probe)
    tf = font(size, "demi")
    kf = font(S["kicker"], "medium")
    sf = font(S["sub"], "regular")
    maxw = G["panel_width"] - 200 if panel else W - 460
    tlines = wrap(pd, title, tf, maxw)
    full_s = wrap(pd, sub, sf, maxw - 60) if sub else []
    lead = BRAND["type"]["leading"]
    th = len(tlines) * int(tf.size * lead)
    kh = 62 if kicker else 0
    sh = (46 + len(full_s) * int(sf.size * 1.34)) if full_s else 0
    total_full = kh + th + sh
    pw = G["panel_width"]
    ph_full = max(G["panel_min_height"], total_full + 150)
    px, py = (W - pw) // 2, (H - ph_full) // 2
    for k, t, s in steps:
        img = stage(footer_note)
        d = ImageDraw.Draw(img)
        slines = wrap(d, s, sf, maxw - 60) if s else []
        shown = kh + th + ((46 + len(slines) * int(sf.size * 1.34)) if slines else 0)
        # The lozenge keeps its top edge and loses exactly the band the
        # supporting line would occupy, so (ph - shown) is identical on both
        # stages and the title sits at the same y on each.
        ph = ph_full if (slines or not sub) else max(180, ph_full - sh)
        if panel:
            g = grad_panel(pw, ph, 30, _stops(), diagonal=False)
            img.paste(g, (px, py), g)
        cx = W // 2
        y = py + (ph - shown) // 2
        if k:
            d.text((cx - d.textlength(k.upper(), font=kf) / 2, y), k.upper(),
                   font=kf, fill=rgb("card_muted") if not panel else rgb("white"))
            y += kh
        ink = rgb("white") if panel else rgb("card_ink")
        y = block(d, tlines, tf, cx, y + th // 2, ink)
        if slines:
            block(d, slines, sf, cx,
                  y + 46 + (len(slines) * int(sf.size * 1.34)) // 2,
                  rgb("white") if panel else rgb("card_muted"))
        out.append(img)
    return out


def tile_timeline(n: int) -> list:
    """The states a tile card can hold, each one a whole-tile change.

    Returned as `(lit, spotlight)` per state:

        structure   no tile lit, the containers waiting
        build       tile 0 lit, then 0-1, then 0-1-2 ...
        walk        every tile lit, one spotlit at a time
        settle      every tile lit and level

    Every step lights or dims a whole gradient panel - about 150,000 pixels.
    That is what the hold detector needs. The previous timeline revealed one
    line of tile copy at a time, which is roughly 0.1 % of the frame, right on
    freezedetect's floor: two of those stages read as a single 7.7-second
    freeze on the first kit build and the gate failed the film for it.
    """
    states = [(set(), None)]
    for i in range(n):
        states.append((set(range(i + 1)), i))
    if n > 1:
        for i in range(n):
            states.append((set(range(n)), i))
    states.append((set(range(n)), None))
    return states


def tile_max_stages(spec: dict) -> int:
    return len(tile_timeline(len(spec["tiles"])))


def tile_stages(heading: str, tiles: list, icons: list | None = None,
                chevrons: bool = False, footer_note=None,
                stages: int | None = None) -> list:
    """The three-panel overview - the load-bearing frame.

    `tiles` is a list of {label, lines[]}. A lit tile carries the full
    pink-to-violet gradient the reference uses; an unlit one is the same panel
    dimmed back towards its container, so the card is whole from the first
    frame and the build is a matter of attention rather than of assembly.
    """
    from PIL import Image, ImageDraw
    n = len(tiles)
    gap, margin = 44, 150
    tw = (W - 2 * margin - (n - 1) * gap) // n
    th = 470
    top = 372
    pad = G["tile_pad"]
    radius = G["tile_radius"]
    out = []
    icon_imgs = []
    for name in (icons or []):
        p = JEWELS / f"{name}.png"
        icon_imgs.append(Image.open(p).convert("RGBA") if p.exists() else None)
    chev = None
    if chevrons and (JEWELS / "chevron.png").exists():
        chev = Image.open(JEWELS / "chevron.png").convert("RGBA")

    timeline = tile_timeline(n)
    if stages:
        want = max(2, min(stages, len(timeline)))
        idx = sorted({round(j * (len(timeline) - 1) / (want - 1))
                      for j in range(want)})
        timeline = [timeline[j] for j in idx]

    # Each gradient is rendered once, not once per stage.
    gw, gh = tw - 2 * pad, th - 150
    full = grad_panel(gw, gh, radius, _stops())
    # Three levels, not two. With only lit/unlit, state ({0,1}, spot 1) and
    # state ({0,1,2}, spot 1) render pixel-identical, and a downsampled
    # timeline lands on exactly that pair at four stages - which is how a
    # 9-second hold got through a gate that was measuring the right thing.
    mid = grad_panel(gw, gh, radius, _stops(), dim=0.45)
    faded = grad_panel(gw, gh, radius, _stops(), dim=0.80)

    for on_set, spot in timeline:
        img = stage(footer_note)
        d = ImageDraw.Draw(img)
        hf = font(56, "demi")
        hw = d.textlength(heading, font=hf)
        d.text((W // 2 - hw / 2, 208), heading, font=hf, fill=rgb("card_ink"))
        d.rectangle([W // 2 - hw / 2, 292, W // 2 + hw / 2, 296],
                    fill=rgb("grad_magenta"))
        for i, tile in enumerate(tiles):
            x = margin + i * (tw + gap)
            reached = i in on_set
            lit = reached and (spot is None or spot == i)
            d.rounded_rectangle([x, top, x + tw, top + th], radius + 6,
                                fill=rgb("card_panel"))
            g = full if lit else (mid if reached else faded)
            img.paste(g, (x + pad, top + 118), g)
            d2 = ImageDraw.Draw(img)
            head_col = rgb("card_ink") if lit else rgb("card_muted")
            iy = top + 30
            lx = x + pad
            if i < len(icon_imgs) and icon_imgs[i] is not None:
                ic = icon_imgs[i].resize((int(icon_imgs[i].width * 1.1),
                                          int(icon_imgs[i].height * 1.1)))
                if not lit:
                    ic = ic.copy()
                    ic.putalpha(ic.getchannel("A").point(lambda a: int(a * 0.45)))
                img.paste(ic, (lx, iy), ic)
                lx += ic.width + 18
            lf = font(38, "demi")
            d2.text((lx, iy + 6), tile["label"], font=lf, fill=head_col)
            # Tile copy stays on the panel at every stage. It is the panel
            # that lights, not the words that arrive: a card whose text
            # appears a line at a time is a card the hold detector cannot see
            # building.
            by = top + 118 + 30
            bf = font(29, "medium")
            body_col = rgb("white") if lit else rgb("card_muted")
            for line in tile["lines"]:
                for ln in wrap(d2, line, bf, gw - 56):
                    d2.text((x + pad + 28, by), ln, font=bf, fill=body_col)
                    by += 40
                by += 10
            if chev is not None and i < n - 1:
                cw = int(chev.width * 0.5)
                ch = int(chev.height * 0.5)
                c = chev.resize((cw, ch))
                img.paste(c, (x + tw + (gap - cw) // 2, top + th // 2 - ch // 2), c)
        out.append(img)
    return out


def title_overlay(title: str, kicker: str | None, size: int):
    """The title lozenge — transparent stage, for laying over graded b-roll."""
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    tf, kf = font(size, "demi"), font(S["kicker"], "medium")
    tlines = wrap(d, title, tf, 1368)
    th = len(tlines) * int(tf.size * BRAND["type"]["leading"])
    kh = 62 if kicker else 0
    total = kh + th
    pw, ph = G["panel_width"], max(G["panel_min_height"], total + 150)
    px, py = (W - pw) // 2, (H - ph) // 2
    # Magenta to violet, the gradient the reference puts its title in. The
    # harvester also keys on it: the magenta-to-violet fraction of the centre
    # band is how film/kit/harvest.py finds the frame a title lozenge clears.
    # Solid backing under the gradient. Without it the plate reads as
    # translucent over bright footage and a face shows through the title.
    d.rounded_rectangle([px, py, px + pw, py + ph], 30,
                        fill=rgb("card_bg") + (255,))
    g = grad_panel(pw, ph, 30, _stops(), diagonal=False)
    img.paste(g, (px, py), g)
    d = ImageDraw.Draw(img)
    y = py + (ph - total) // 2
    if kicker:
        d.text((W // 2 - d.textlength(kicker.upper(), font=kf) / 2, y),
               kicker.upper(), font=kf, fill=rgb("white") + (255,))
        y += kh
    block(d, tlines, tf, W // 2, y + th // 2, rgb("white") + (255,))
    return img


def chyron(text: str, tag: str | None = None):
    """Transparent lower third. It never sits over answer text."""
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    tf, gf = font(S["chyron"], "medium"), font(S["chyron_tag"], "demi")
    x, top = G["chyron_x"], G["chyron_y"]
    d.rounded_rectangle([x, top + 2, x + 6, top + 66], 3, fill=rgb("cyan") + (255,))
    # White, not ink. The lower third lives on the navy stage below the panel;
    # ink on navy is invisible, and it was invisible for a whole first cut.
    if tag:
        d.text((x + 26, top), tag.upper(), font=gf, fill=rgb("cyan") + (255,))
        d.text((x + 26, top + 30), text, font=tf, fill=rgb("white") + (255,))
    else:
        d.text((x + 26, top + 14), text, font=tf, fill=rgb("white") + (255,))
    return img


def card_capacity(spec: dict) -> int:
    """How many stages this card can actually hold apart.

    plan.py multiplies this by MAX_HOLD to cap a card beat. Sizing a card beat
    on its read alone is what produced a 23-second overview card asked to make
    six stages out of a build that could only make five distinguishable ones -
    two of them collapsed into one 7.7-second freeze and the film failed its
    own gate. A card that cannot hold its beat needs another tile or a shorter
    line, not a longer hold.
    """
    kind = spec.get("kind", "statement")
    if kind == "tiles":
        return tile_max_stages(spec)
    if kind == "statement":
        return statement_max_stages(spec)
    return 1          # title and chyron overlays are a single frame


def render(project: dict) -> dict:
    """Render every card the project declares. Returns {name: [paths]}."""
    out_dir = project["_work"] / "cards"
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.png"):
        old.unlink()
    note = project.get("footer_note")
    # plan.py sizes each card beat from its read; a long beat needs more
    # stages, never a longer hold.
    want = {b["card"]: b.get("stages") for b in project.get("beats", [])
            if b.get("card")}
    written, text_log = {}, {}

    for name, spec in project["cards"].items():
        kind = spec.get("kind", "statement")
        if kind == "statement":
            imgs = statement_stages(
                spec["title"], spec.get("kicker"), spec.get("sub"),
                spec.get("size", S["card"]), spec.get("panel", True), note,
                min(want.get(name) or spec.get("stages", 2),
                    card_capacity(spec)))
            text_log[name] = " | ".join(
                x for x in (spec.get("kicker"), spec["title"], spec.get("sub")) if x)
        elif kind == "tiles":
            imgs = tile_stages(spec["heading"], spec["tiles"], spec.get("icons"),
                               spec.get("chevrons", False), note,
                               min(want.get(name) or spec.get("stages")
                                   or card_capacity(spec),
                                   card_capacity(spec)))
            text_log[name] = " | ".join(
                [spec["heading"]] +
                [t["label"] + ": " + " ".join(t["lines"]) for t in spec["tiles"]])
        elif kind == "title":
            imgs = [title_overlay(spec["title"], spec.get("kicker"),
                                  spec.get("size", S["title"]))]
            text_log[name] = " | ".join(
                x for x in (spec.get("kicker"), spec["title"]) if x)
        elif kind == "chyron":
            imgs = [chyron(spec["text"], spec.get("tag"))]
            text_log[name] = " | ".join(
                x for x in (spec.get("tag"), spec["text"]) if x)
        else:
            raise SystemExit(f"card {name}: unknown kind {kind!r}")
        paths = []
        for i, img in enumerate(imgs):
            p = out_dir / f"{name}_{i}.png"
            img.save(p)
            paths.append(p.name)
        written[name] = paths
        print(f"[OK] {name:16s} {kind:10s} {len(paths)} stage(s)")

    (project["_work"] / "cardtext.json").write_text(json.dumps(text_log, indent=1))
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
