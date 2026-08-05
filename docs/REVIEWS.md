# How reviews work

Every agent in this library carries **two independent reviews**. They are never
combined, never averaged, and never shown in the same panel.

## The two channels

| | **Community rating** | **Automated review** |
|---|---|---|
| Produced by | people | static analysis, plus any model you attach |
| Answers | *Is this liked and used?* | *Is this built correctly?* |
| Lives in | Discussions → **Community** | Discussions → **Automated Reviews** |
| Published at | `api/v1/agents.json` → `engagement` | `api/v1/reviews.json` |
| On a one-pager | left panel, marked **People** | right panel, marked **Machine** |

Both are useful. Neither substitutes for the other, and a reader who cannot
tell which one they are looking at is being misled by both — which is why they
are separated everywhere, down to the endpoint they are served from.

## Why not one score

A single blended number fails in both directions at once. A widely-used agent
can still hardcode a credential; a flawlessly-structured agent can be useless
in practice. Averaging popularity with correctness produces a figure that is
wrong about both and reassuring about neither.

So: two numbers, two panels, two threads. If you want one answer, read both.

## The automated review

Machine reviews come from **RAPP Sentinel** — see
[`sentinel/SPEC.md`](../sentinel/SPEC.md). The short version:

- The rubric is data (`sentinel/NEIGHBORHOOD.json`), not code.
- Source is parsed with `ast`. Agent code is **never imported and never run**.
- Every failed check carries a *teachable* note: what the principle is, why it
  matters, and what to do instead. The review is meant to be read, not just
  scored.
- Anyone can run it: `python3 scripts/sentinel.py run --agent <name>`. No
  token, no service. Run it before you submit and there are no surprises.

### The five principles

| Principle | Question |
|---|---|
| Quality | Is it built the way a maintained agent is built? |
| Usability | Can a model — and a human — tell what this does and how to call it? |
| Effectiveness | Does it actually do the work, or only describe it? |
| Safety | Can installing this hurt the person who installed it? |
| Portability | Will it run somewhere other than the machine that wrote it? |

Interpretive residents (clarity, honesty, blast-radius, teachability) need a
model. Sentinel emits their work as a **packet** rather than calling anything
itself, so which model reviewed your agent is recorded on the finding instead
of assumed.

## Dormant until a model is attached

A Sentinel run with no model configured produces **evidence and no verdicts**.
The deterministic residents measure; nothing judges. That is deliberate: a
review pipeline that can approve something with no intelligence in the loop is
an automated yes, which is worth nothing to whoever relies on it.

Waking a run is a separate, attributed act — `scripts/wake_sentinel.py` injects
a model, and the answer is recorded with the model that produced it. You can
run the identical thing locally against your own model; nothing about the
review depends on our infrastructure.

## Verdicts

`approved` · `changes-requested` · `advisory-only` · `framework`

A verdict is a **queue position, not a judgment**. Nothing here certifies an
agent for production use in your tenant. Community submissions are not
certified by Microsoft, and an automated score is not an endorsement by
anybody — see [`DISCLAIMER.md`](../DISCLAIMER.md).

## Disagreeing with a finding

Reply on the machine-review thread. A check that produces false positives is a
defect in the rubric, and the rubric is a JSON file anyone can read and send a
pull request against. A reviewer nobody trusts catches nothing, so a false
positive is treated as a real bug.
