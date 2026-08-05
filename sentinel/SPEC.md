# RAPP Sentinel

> **Schema:** `rapp-sentinel-neighborhood/1.0` · `rapp-sentinel-run/1.0` ·
> `rapp-sentinel-packet/1.0` · **Status:** v1

Sentinel is how this library reviews submissions. It is built on one idea
borrowed from the RAPP network spec: **the neighborhood is data, and the
runtime is whatever you attach to it.**

## 1. What it is

A **neighborhood** is a roster of **residents**. Each resident has one lens and
one job. The roster lives in [`NEIGHBORHOOD.json`](NEIGHBORHOOD.json) — a plain
JSON file in this repository, with no code in it.

Two kinds of resident:

| Kind | Has | Runs under | Reproducible |
|---|---|---|---|
| `deterministic` | a `module` | Python, no model, no network | byte for byte, forever |
| `interpretive` | a `prompt` | any model you point at it | by attribution, not by digest |

That split is the whole design. The deterministic residents make a run
*checkable*. The interpretive residents make it *insightful*. Neither is
sufficient: static analysis cannot tell you an agent misrepresents what it
does, and a model cannot promise you it will say the same thing twice.

## 2. Why the neighborhood is data and not a service

Three properties fall out of storing the roster in the repository:

**Traceability.** Every run records the commit, the neighborhood digest, the
rubric version, and the digest of every input. A verdict can always be traced
back to exactly what produced it. When the rubric changes, the digest changes,
and every earlier verdict now visibly describes a rubric that no longer exists
— stale verdicts announce themselves rather than quietly aging into fiction.

**Reproducibility.** `sentinel.py verify --run <id>` re-runs the deterministic
residents and compares. If it does not reproduce, either the tree moved or the
run was not honest, and it says which.

**Portability.** Anyone can pull the neighborhood and run it themselves:

```bash
git clone https://github.com/microsoft/aibast-agents-library
cd aibast-agents-library
python3 scripts/sentinel.py run --agent my_new_agent
```

No token, no service, no account. The review a maintainer sees is the review
you can run before submitting — which is the only way "we reviewed it" means
anything to the person on the other end.

## 3. Awakening

**A dormant run has no verdicts.** `sentinel.py run` measures with its
deterministic residents and stops there, because measurement is not judgment.
Until a model has answered, the run carries evidence and `verdicts: null`, and
says so in `dormant_notice`. This is not a limitation to work around — a
pipeline that could approve a submission with no intelligence in the loop would
be an automated yes, and an automated yes is worth nothing to whoever relies on
it.

`scripts/wake_sentinel.py` is the injector, deliberately a separate file:
`sentinel.py` holds no credential and calls nothing, so the neighborhood stays
portable data that runs under any runtime. Point the injector at any
OpenAI-compatible endpoint — Azure OpenAI in CI, a local model on a laptop:

```bash
SENTINEL_ENDPOINT=http://localhost:11434/v1/chat/completions \
SENTINEL_MODEL=llama3.1 python3 scripts/wake_sentinel.py
```

With nothing configured it wakes nothing, exits zero, and reports the run as
dormant.


A neighborhood does nothing on its own. It is a data structure waiting for a
runtime, and there is more than one:

```bash
# 1. Local, no model. Deterministic residents only.
python3 scripts/sentinel.py run

# 2. Emit the work the interpretive residents need.
python3 scripts/sentinel.py run --packets-only

# 3. Hand a packet to any model — Claude, Copilot, a local model.
#    Feed the answers back with the model recorded as attribution.
python3 scripts/sentinel.py absorb --run <id> --resident honesty \
    --answers answers.json --model "claude-fable-5"

# 4. Prove the run reproduces.
python3 scripts/sentinel.py verify --run <id>
```

Step 3 is the injection. The packet carries the prompt, the subject list, and
each subject's source digest — the entire contract. `sentinel.py` never calls a
model and holds no API key, so which model answered is the operator's choice
and is recorded, not assumed.

## 4. The separation rule

**Every resident in this neighborhood produces machine review.** Nothing here
is a human opinion. Machine review and community rating are never combined,
never averaged, and never rendered as one number.

| | Human | Machine |
|---|---|---|
| Where | Discussions → *Community* | Discussions → *Automated Reviews* |
| Thread title | `@publisher/slug` | `[machine review] @publisher/slug` |
| Answers | Is this liked and used? | Is this built correctly? |
| Signal | reactions, replies, install tally | rubric scores, findings, verdict |
| Endpoint | `api/v1/agents.json` → `engagement` | `api/v1/reviews.json`, `api/v1/sentinel.json` |
| On a one-pager | left panel, blue, "People" | right panel, violet, "Machine" |

The rule exists because the two kinds of review fail in opposite directions. A
popular agent can leak a credential. A perfectly-structured agent can be
useless. Averaging them produces a number that is wrong in both directions at
once and reassuring in neither.

Reactions are deliberately absent from machine-review threads: you cannot
agree a static analysis into being correct. Those threads are for arguing with
the finding — and a check that produces false positives is a defect in the
rubric, fixed in `NEIGHBORHOOD.json` where everyone can see the change.

## 5. Verdicts

| Verdict | Means |
|---|---|
| `approved` | No blocking resident objected and static analysis scored ≥ 85 |
| `changes-requested` | A blocking resident objected, or static analysis < 60 |
| `advisory-only` | Only advisory residents had anything to say |
| `framework` | Not an agent (a base class); the rubric does not apply |

A verdict is a **queue position, not a judgment**. Nothing Sentinel produces
approves an agent for use in anyone's tenant — see [`DISCLAIMER.md`](../DISCLAIMER.md).

## 6. Adding a resident

Add an object to `residents` in `NEIGHBORHOOD.json`. That is the whole change:
no code, no deployment, and the digest shift makes every prior verdict
visibly older than the rubric.

- `id`, `lens`, `kind`, `authority` (`blocking` | `advisory`) are required.
- A `deterministic` resident names a `module` in `scripts/` exposing
  `review_one(path) -> dict` and a `RUBRIC_VERSION`.
- An `interpretive` resident carries a `prompt` that must specify its exact
  return JSON. Write it to be answerable from source alone, and tell the model
  not to praise — a reviewer that hedges produces findings nobody acts on.

## 7. Learning a source before aggregating from it

Every skill repository is shaped differently — `skills/`, `src/content/skills/`,
one file per directory. Aggregating before you know which is guessing, and a
crawler that guesses fails in the worst way: it silently returns fewer skills
than the repository holds, and "0 found" looks exactly as plausible as "300
found" from outside.

So a source is **scouted before it is crawled**. `scripts/profile_source.py`
walks the repository, clusters its markdown by directory, measures how
consistently each cluster carries frontmatter, and records the shape with the
alternatives it rejected:

```bash
python3 scripts/profile_source.py microsoft/cat-agent-skills --id cat-agent-skills
```

The result lands in `sentinel/sources/<id>.json`, and `crawl_skills.py` refuses
to touch a source that has none. Size alone would pick a documentation folder in
most repositories, so the ranking requires frontmatter: on `cat-agent-skills`
that chose `src/content/skills` (78 files, frontmatter on every one) over the
larger `src/content/guides` (53 files, frontmatter on none).

Fields the scout cannot map confidently are **listed, never guessed** — a wrong
mapping corrupts every skill taken from that source afterwards. Those go to the
`source-shape` resident, whose packet the scout emits alongside the shape. Until
a model confirms it the shape is `provisional`, and it says so.

Two more guards, both learned the hard way:

- A crawl returning less than half the previous snapshot **refuses to write**.
  A source that changed shape, a rate limit, and a partial fetch all look like
  a smaller catalog, and overwriting quietly would lose it while the job stayed
  green. `--allow-shrink` is the deliberate override.
- The shape records `expected_count`, and a gate compares it against what
  aggregation actually produced. Drift between the two is the signal that the
  source moved.

## 8. One pipeline, not two

Aggregating and reviewing are the same act in two forms — shaping raw material,
then judging the shape. `.github/workflows/metrics.yml` runs them as one pass:

```
crawl → convert to skill.md → mirror to agent.py → storyboard
      → sentinel run (evidence) → wake (inject the model) → publish
```

Splitting them would let a freshly crawled skill sit in the catalog unshaped
and unreviewed, which is the naked-link problem the library exists to solve. A
skill is not aggregated here until it has been shaped, mirrored, given a demo,
and actually reviewed.

## 9. Real-time review of new submissions

`.github/workflows/sentinel.yml` runs Sentinel on pull requests that touch
`agents/**`, posts the deterministic findings to the pull request, and uploads
the interpretive packets as an artifact for a maintainer (or a model) to
execute. Submitters get the same review before they open the pull request by
running it locally, so nothing in the loop is a surprise.
