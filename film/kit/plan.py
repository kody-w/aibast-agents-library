#!/usr/bin/env python3
"""Derive the beatmap from the narration that was actually synthesised.

Hand-tuned beat lengths are the reason a film takes a day. You write the copy,
guess the window, build, discover the read overruns by 1.4s, nudge, rebuild.
Ten films is that loop ten times, and it is the loop that produces a rushed
read, because nudging copy is slower than nudging the rate and nobody is
watching.

So the beatmap is computed, not written. Every narrated beat is exactly as
long as its read plus its lead-in plus a tail of air, which makes the fit-gate
green by construction and makes speeding a read up structurally impossible -
there is no knob for it. The fixed beats (sting, title, disclaimer, footer)
keep the house lengths measured off the corpus.

The b-roll under each narrated beat is filled from the film's industry bucket,
shot by shot at house length, cycling the bucket if the beat is longer than
the material. A beat that cannot be filled honestly is reported rather than
padded.

Output: film/projects/<slug>/project.json  (the "beats" array, in place)
Usage:
    python3 film/kit/plan.py --project supplier-risk-monitoring
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cards import card_capacity  # noqa: E402
from common import BROLL, PROJECTS, load_project, probe_duration  # noqa: E402
from screens import max_states  # noqa: E402

# Fixed beats, measured off the corpus (film/GRAMMAR.md section 1).
# 2.40, not 2.57. The recording this sting was cut from begins fading its
# own agent title up over the white field at 2.45s, and two frames of another
# product's name is still another product's name.
STING = 2.40
TITLE = 5.00
DISCLAIMER = 3.60
FOOTER = 4.00
# The corpus closes on the logo, 2-3s of it, in all 19 recordings. The kit
# shipped the asset and referenced it from nowhere, so every kit film ended on
# a text card instead. 3.00 is the measured median.
OUTRO = 3.00

# Air after a read finishes, before the beat cuts. Below about 0.6s the cut
# clips the tail of the last word.
TAIL = {"broll": 1.20, "card": 0.90, "demo": 1.30, "close": 0.80}
LEAD = {"broll": 0.30, "card": 0.40, "demo": 1.10, "close": 0.55}

SHOT_MIN, SHOT_MAX = 2.20, 5.20
MAX_HOLD = 4.60          # per demo/card stage; the gate fails at 5.0
# A data frame has to be readable, not merely present. The corpus gives its
# demo 56.4% of the runtime (film/GRAMMAR.md, 18 films, range 51.0-60.0%) with
# narration running all the way through; a storyboard-derived script has less
# to say there, so the difference is bought back as reading time on the answer
# rather than left as a faster cut. At 0.85 the kit built demos of 37-42% and
# the films did not have the shape of the catalog; 2.20 puts a three-question
# demo in the high forties, which is as close as an answer with six or seven
# reveal states can get. The lever beyond that is richer answers, not a longer
# hold - the hold is capped at MAX_HOLD either way.
# 0.0, deliberately. Reading time was bought here at 2.2s a stage, which
# stretched a 12s read into a 30s beat and left three 15-18s holes of bed-only
# audio inside the demo of every film. A blind reviewer called it "the room
# watches a white rectangle in silence three times". The gate measured the
# LEVEL of those gaps and passed them, because it never measured their LENGTH.
# Reading time now comes from writing more narration, not from silence.
READ_HOLD = 0.0


def bucket_clips(bucket: str) -> list:
    d = BROLL / bucket
    if not d.is_dir():
        raise SystemExit(f"no b-roll bucket {bucket!r} - harvest one with "
                         f"python3 film/kit/harvest.py --cut <recording> "
                         f"--bucket {bucket}")
    out = [(f"{bucket}/{p.name}", round(probe_duration(p), 2))
           for p in sorted(d.glob("*.mp4"))]
    if not out:
        raise SystemExit(f"b-roll bucket {bucket!r} is empty")
    return out


def fill(clips: list, target: float, cursor: int) -> tuple:
    """Lay shots end to end until the beat is exactly full.

    The beat length is set by the read, so the montage has to meet it to the
    frame. A shortfall is absorbed by lengthening shots that have unused
    source, never by leaving a gap and never by a sub-2.4s flash of a shot -
    a beat that comes up short against its read clips the last word.
    """
    picked, used, source = [], 0.0, {}
    tried = 0
    while target - used > 0.05 and tried < len(clips) * 4:
        name, dur = clips[cursor % len(clips)]
        cursor += 1
        tried += 1
        # A clip shorter than a readable shot is skipped, not a reason to stop.
        # Treating it as a stop condition truncated a 12s montage to one 3.8s
        # shot the moment a 2.3s clip came round in the bucket.
        if dur < SHOT_MIN:
            continue
        if target - used < SHOT_MIN and picked:
            break
        source[len(picked)] = dur
        take = min(dur, SHOT_MAX, target - used)
        picked.append({"file": name, "dur": round(take, 2)})
        used += take
    # Spread any remainder over shots that still have source left.
    short = round(target - used, 3)
    while short > 0.01:
        grew = False
        for i, shot in enumerate(picked):
            room = min(source[i], SHOT_MAX) - shot["dur"]
            if room > 0.01:
                add = min(room, short)
                shot["dur"] = round(shot["dur"] + add, 2)
                used += add
                short = round(short - add, 3)
                grew = True
                if short <= 0.01:
                    break
        if not grew:
            break
    # Still short and nothing can grow: add one more shot and take the
    # difference off its neighbour, so both stay above the flash threshold.
    if short > 0.01:
        name, dur = clips[cursor % len(clips)]
        cursor += 1
        need = max(SHOT_MIN, short)
        borrow = round(need - short, 2)
        donor = next((x for x in reversed(picked)
                      if x["dur"] - borrow >= SHOT_MIN), None)
        if donor is not None and need <= min(dur, SHOT_MAX):
            donor["dur"] = round(donor["dur"] - borrow, 2)
            picked.append({"file": name, "dur": round(need, 2)})
    return picked, cursor, round(sum(s["dur"] for s in picked), 2)


def card_beat(project: dict, bid: str, card: str, slot: str, kind: str,
              dur: float, note: str, floor: int = 2) -> dict:
    """One narrated card beat, sized so no stage is held past MAX_HOLD.

    A card beat was the one beat plan.py never capped. Demo beats were capped
    at `states x MAX_HOLD` from the first version; card beats were sized on the
    read alone, so an 18.5-second read produced a 23-second overview card whose
    build could only make five distinguishable frames - 4.6s each was fine, six
    was not, and two of them collapsed into one 7.7-second freeze. The cap is
    the same arithmetic the demo already used.
    """
    spec = project["cards"][card]
    capacity = round(card_capacity(spec) * MAX_HOLD, 2)
    stages = max(floor, math.ceil(dur / MAX_HOLD))
    if dur > capacity:
        print(f"[WARN] {card}: the read needs {dur:.2f}s but the card can only "
              f"hold {card_capacity(spec)} stages apart ({capacity:.2f}s) - "
              f"add a tile, or break the line into two")
    else:
        stages = min(stages, card_capacity(spec))
    return {"id": bid, "kind": "card", "card": card, "dur": dur, "vo": slot,
            "off": LEAD[kind], "stages": stages, "note": note}


def plan(project: dict) -> list:
    vo = json.loads((project["_work"] / "vo" / "manifest.json").read_text())["slots"]
    clips = bucket_clips(project["broll_bucket"])
    cursor = 0
    beats = []

    def dur_for(slot: str, kind: str) -> float:
        return round(vo[slot]["dur"] + LEAD[kind] + TAIL[kind], 2)

    beats.append({"id": "b00", "kind": "sting", "clip": "sting-intro-logo.mp4",
                  "dur": STING, "note": "Microsoft logo sting"})
    beats.append({"id": "b01", "kind": "title", "clip": clips[0][0],
                  "card": "c_title", "dur": TITLE,
                  "note": "title over industry b-roll"})

    n = 2
    for slot, note in (("vo01", "the job to be done"),
                       ("vo02", "the manual status quo")):
        if slot not in vo:
            continue
        target = dur_for(slot, "broll")
        picked, cursor, used = fill(clips, target, cursor)
        if not picked:
            raise SystemExit(f"{slot}: no b-roll could fill {target:.2f}s")
        beats.append({"id": f"b{n:02d}", "kind": "broll", "dur": used,
                      "vo": slot, "off": LEAD["broll"], "clips": picked,
                      "note": note})
        n += 1

    beats.append(card_beat(project, f"b{n:02d}", "c_overview", "vo03", "card",
                           dur_for("vo03", "card"),
                           "sources, flow of work, actions", floor=3))
    n += 1
    beats.append({"id": f"b{n:02d}", "kind": "card", "card": "c_synthetic",
                  "dur": DISCLAIMER,
                  "note": "synthetic-data card, before the first data frame"})
    n += 1

    for q in project["demo"]["questions"]:
        slot = q["vo"]
        blocks = max_states(q["answer"])
        # +1 for the thinking frame. A beat may never be longer than its
        # reveal points can fill at MAX_HOLD each - that is what produced two
        # 5.25s holds through a gate sized on duration alone.
        capacity = round(blocks * MAX_HOLD, 2)
        bare = dur_for(slot, "demo")
        want = round(min(bare + READ_HOLD * min(blocks, 8), capacity), 2)
        if bare > capacity:
            print(f"[WARN] {slot}: the read needs {bare:.2f}s but the answer "
                  f"has only {blocks} reveal points ({capacity:.2f}s) - "
                  f"add an answer block")
            want = bare
        # Stages, not hold length. The screen renderer reveals the answer one
        # step at a time, so a long read buys more stages rather than a frame
        # held past the gate - up to the number of steps the answer has.
        stages = min(blocks, max(3, math.ceil(want / MAX_HOLD)))
        beats.append({"id": f"b{n:02d}", "kind": "demo", "question": q["id"],
                      "chyron": f"c_{q['id']}", "dur": want, "vo": slot,
                      "off": LEAD["demo"], "stages": stages,
                      "note": q["prompt"][:60]})
        n += 1

    if "vo_payoff" in vo:
        target = dur_for("vo_payoff", "broll")
        picked, cursor, used = fill(clips, target, cursor)
        beats.append({"id": f"b{n:02d}", "kind": "broll", "dur": used,
                      "vo": "vo_payoff", "off": LEAD["broll"], "clips": picked,
                      "note": "payoff"})
        n += 1
    beats.append(card_beat(project, f"b{n:02d}", "c_helps", "vo_helps", "card",
                           dur_for("vo_helps", "card"),
                           "how the agent helps", floor=3))
    n += 1
    beats.append(card_beat(project, f"b{n:02d}", "c_cta", "vo_cta", "close",
                           dur_for("vo_cta", "close"), "call to action"))
    n += 1
    beats.append({"id": f"b{n:02d}", "kind": "card", "card": "c_footer",
                  "dur": FOOTER, "note": "synthetic-data footer"})
    n += 1
    # All 19 reference recordings close on the logo. Ending on a text card is
    # the difference between a film that belongs to the catalog and one that
    # looks like it was made somewhere else.
    beats.append({"id": f"b{n:02d}", "kind": "sting",
                  "clip": "sting-outro-logo.mp4", "dur": OUTRO,
                  "note": "Microsoft logo outro"})
    return beats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", required=True)
    args = ap.parse_args()
    project = load_project(args.project)
    beats = plan(project)
    path = PROJECTS / args.project / "project.json"
    raw = json.loads(path.read_text())
    raw["beats"] = beats
    raw["beats_generated_by"] = "film/kit/plan.py"
    path.write_text(json.dumps(raw, indent=1) + "\n")
    total = sum(b["dur"] for b in beats)
    demo = sum(b["dur"] for b in beats if b["kind"] == "demo")
    share = demo / total * 100
    # The reference gives its demo 56.4% of the runtime (film/GRAMMAR.md,
    # 18 films, 51.0-60.0%). Below 45% the film is a deck with a screenshot in
    # it; 45 is the fail line, not the goal.
    print(f"[OK] {len(beats)} beats, {total:.2f}s, demo {share:.1f}% "
          f"(reference 56.4%, floor 45%)")
    if share < 45.0:
        print(f"[WARN] demo is {share:.1f}% of the film - the reference is "
              f"56.4%. Give the answers more reveal states, or cut a card.")
    # The windows were computed from the reads, so this can only fail if a
    # slot was synthesised that no beat claims. Report it rather than assume.
    raw["_work"] = PROJECTS / args.project / "work"
    raw["_dir"] = PROJECTS / args.project
    from narrate import fit_gate
    vo = json.loads((raw["_work"] / "vo" / "manifest.json").read_text())["slots"]
    problems = fit_gate(raw, vo)
    if problems:
        print(f"[WARN] {len(problems)} fit problem(s):")
        for p in problems:
            print("  ", p)
        return 1
    print("[OK] fit gate green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
