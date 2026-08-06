# Batches

A batch is a set of films built from one source in one pass. Every
`project.json` carries a `batch` field, `film/kit/make.py --all --batch <name>`
builds one, and `film/kit/publish.py --batch <name>` collects the results into
`film/out/<batch>/` with a manifest that records what each film measures.

| Batch | Source | Count | What it is |
|---|---|---|---|
| `library` | `media/walkthroughs/agent-<slug>.json` | 12 | catalog agents that have no demo recording |
| `fy27` | `_batches/fy27-source.json` | 14 | agents named in an internal priority briefing |

## `library`

Composed from the storyboards CI already generates for every catalog entry.
Those storyboards are qualitative by construction — the honesty rules in
`media/RAPPVISION.md` forbid an invented figure — so the narration in these
films is the library's own description of its own agents, not new copy.

Selected by taking the registry, removing every agent that already has a
recording in `media/videos/`, and picking the widest spread of categories
available. Ten distinct categories are covered.

## `fy27`

Composed from `_batches/fy27-source.json`, which is a **sanitised** extract of
an internal priority briefing. The briefing itself is not in this repository
and must not be.

Everything below was removed at extraction, before anything was committed:

| Removed | Replaced with |
|---|---|
| named customers and organisations | a sector descriptor — "a national bank", "a public broadcaster" |
| people's names | roles |
| every figure — counts, durations, headcounts, volumes, deal values, dates | the qualitative form, or nothing |
| third-party and competitor product names | "the CRM", "the ticketing system", "an existing assistant" |
| internal program, team and tooling names | nothing |
| customer-internal agent codenames | nothing |
| internal competitive commentary | nothing |

The sanitised source is what is tracked and what the films are built from. It
carries no digits outside the schema string, the batch name and Microsoft
product names.

**Four of the fourteen are thin.** Once the customer specifics were removed,
the residue in the source document was not enough to describe a scenario, so
the scenario in these four is illustrative rather than derived:
`rd-scientific-discovery-and-innovation`,
`healthcare-clinical-documentation-and-data-ring`,
`requirements-and-innovation-authoring`, and
`industry-compliance-and-risk-monitoring`. They are filmable and honest — every
frame is badged illustrative and synthetic — but they are not a faithful
rendering of what the briefing said, because the briefing did not say enough
that could travel.

The healthcare one additionally deals with clinical records. Name-scrubbing is
not a clinical-governance review, and it should have one before it is shown to
anyone.

## Status

Every film in both batches is a **draft**. Each `project.json` carries
`approval.required_before_publishing`, and nothing here has been promoted into
`media/videos/`, which is what the site serves. Promotion is a person reading
the script.
