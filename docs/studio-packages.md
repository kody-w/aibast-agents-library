# Generating a studio edition

`tools/build_studio_package.py` turns a workshop's existing portable-agent
literals or authoritative Markdown entity records, retained rules knowledge, operation
skills, and locked demo cases into a SharePoint-backed studio edition. It does
not execute the agent, use a browser, contact a tenant, deploy, or publish.

```sh
python3 tools/build_studio_package.py asset-maintenance-forecast
python3 tools/build_studio_package.py --all
python3 tools/build_studio_package.py --check
python3 tools/build_studio_data.py --check
python3 tools/render_studio_walkthrough.py --check
```

`--all` attempts every **advertised** workshop except the hand-authored
`emission-tracking` reference. The unfinished `grid-outage-response` is not
advertised and is always rejected. A workshop without matching literal JSON or
clean entity tables/uniform record headings is reported as **BLOCKED**, with a
reason, and is not written. Other workshops continue; any blocked or failed
workshop makes that invocation return a nonzero exit status. Unlisted knowledge
is retained rather than silently treated as a complete record export. Synthetic email addresses may use
`example.com` (including its subdomains), `.test`, or `.invalid` only. Other email
domains are explicitly omitted at the column boundary with `omitted_columns`
and an `email privacy gate` reason; the source file is never changed. Non-placeholder
tenant identities remain errors. Retained knowledge marks excluded contacts
explicitly rather than inventing replacement addresses.

`--check` without slugs compares all existing generated editions, excluding the
hand-authored reference. It does not claim that blocked workshops have packages.
It returns nonzero for missing, stale, or obsolete generated artifacts and never
repairs them. Pass explicit slugs to check selected workshops.

## Output and source fidelity

Each generated package contains:

- `studio/data/schema.json` and one CSV per named source record set.
- `studio/agent/GLOBAL-INSTRUCTIONS.md` and derived `skills/*/SKILL.md`.
- `studio/managed-app/app.json`, a read-only `scenario-workspace` spec.
- `studio/walkthrough.json` and the rendered `studio-tutorial.html`.

Records are read with `ast.literal_eval` and checked against named Markdown JSON
blocks before any output is written. Plain headings, backticked headings, `Exact
dataset` headings, and explicit `Canonical source constant` declarations are
supported. JSON string keys correspond to Python string/integer keys; tuples
become arrays, and sets become deterministically sorted arrays without changing
membership. A data mismatch is an error, not a blocked-workshop exemption.

Mapping keys remain separate text identifiers immediately after `Title`.
Sequences use a unique source ID when present, otherwise a stable one-based row
number, not an invented business identifier. `Title` uses a source human label
when available and the source key otherwise. Scalar/key-value record sets retain
one row per entry. Dictionaries inside records are flattened into bounded,
letters-and-digits column names. Arrays of scalars join with `; `; structured
arrays and other structured values use compact JSON and are excluded from
displayed app columns. Booleans become `Yes`/`No`; nulls and explicitly optional
missing fields become empty cells. Unknown, unmapped source fields are errors.

Dates, years/vintages, identifiers, postal codes, and phone numbers stay text.
The Manual list steps name the text columns on SharePoint's Customize screen.
Both the app and the agent map CSV column order to **`Title`, `field_1`, ...**;
CSV headers are display names, not the imported SharePoint internal names.
In literal mode, the agent uploads only the separate rules knowledge, not the
records file. Table-backed editions upload generated retained-knowledge copies:
listed entity rows become pointers to their lists, while every unlisted record,
rule, policy, calculation and response contract remains available as knowledge.

## Markdown authority and literal corroboration

`tools/studio_knowledge_tables.py` reads actual pipe-table headers, separators
and rows, trims cells, and handles escaped pipes. Entity keys may be structured
IDs or natural entity names; repeated keys retain their source row order instead
of overwriting one another. Whole-cell code/bold formatting is presentation,
not part of an ID. Currency cells become numbers; an entirely percentage-valued
column becomes numeric with `percent1` app formatting. Mixed percentages, ISO
dates, plain numeric text and all other text remain text.

Record-per-heading sections are accepted only when all records have the same
field set. Inline field labels ignore Markdown emphasis and the purely
presentational phrase "in source order"; nested bullet structures and genuinely
different field sets remain knowledge. Standalone narrative bullets are not
silently converted into records.

Each listed section records `source_of_truth: knowledge-table`, its original
file, heading, selector and record form in `schema.json`. Fresh parsing, literal
corroboration and byte-for-byte CSV comparison happen again in
`build_studio_data.py --check`. The schema records how many rows have matching
agent literals and which literal containers corroborate them.

When matching literal entity records exist, every imported value must agree.
Small reviewed `knowledge_tables` overrides can map human labels to source
fields or reproduce documented display/arithmetic transformations from those
literal fields. They do not supply replacement data: cells still come from the
Markdown. A mismatch fails; a presentation that cannot be corroborated stays in
knowledge and is named in `retained_knowledge`. A previously listed table that
stops corroborating fails regeneration rather than disappearing silently.

Rule, policy, threshold, rate and locked-response tables never become lists.
The generated **Evidence locations** section and each studio skill distinguish
listed entity facts from retained knowledge. This includes partially listed
workshops; an app is not presented as the complete original evidence inventory.

The app uses conservative scalar columns, a row count, and at most two
meaningful additive metrics. It does not sum prices, rates, years, identifiers,
percentages, or mixed key/value controls. All screenshots start **pending**.
Regeneration preserves existing screenshot objects or arrays, including reviewed
captures and their metadata, by surviving step ID. Nothing generated is proof
of a live run. Text/JSON values over 255 characters are named explicitly in the
Manual import step with their maximum source length and require **Multiple lines
of text**, not a single-line column. If the import screen cannot create those
columns losslessly, the learner must stop and report the limitation rather than
continue with truncated records. Full-cell comparison remains required; local
CSV fidelity does not establish tenant-side import fidelity.

## Explicit SharePoint arguments

Every generated global-instructions file ends with a **SharePoint site** section,
after the routing block, containing exactly one `YOUR_SITE_ADDRESS` token and
every list title. Keep that token in the repository. The Manual paste step tells
the learner to replace it with their site's address; the Easy workspace builder
must substitute its `--site` value and reject a missing or duplicated token.

The agent must supply the exact site as `dataset` and the list **title** as
`table` on every call. The new runtime can ignore Custom preset inputs and expose
schema-generated tool names and platform descriptions instead of display names,
so those presets and names are not sufficient routing evidence. The section
forbids Get datasets and guessing another site. It says to read all items without
a filter only when **every list has at most 50 items**; otherwise it requires a
filter using the mapped internal column names. The preset site and list-GUID
bindings may remain in the runtime workspace as a compatibility fallback.

## Overrides and the reference oracle

Small overrides may live in `solutions/<slug>/studio/overrides.json` or
`tools/studio_overrides/<slug>.json`. They can set a naming prefix, agent names,
an opening paragraph, list labels/column aliases/tool names, app presentation
choices, or explicit qualified literal-source aliases. They cannot supply
replacement record values.

The emission-tracking override is kept under `tools/studio_overrides/`, outside
the read-only reference package. It records the hand-picked labels and shortened
column names, plus the original app's computed columns, metrics, and ordering.
The regression oracle generates into a temporary directory and compares the
schema, all CSVs, global instructions, skills, and app spec **byte-for-byte** with
the hand-authored files. Its controlled-mutation test proves a changed output
fails that comparison. The hand-authored walkthrough wording and screenshot
reviews are not the oracle's generated-content contract.

The protected checkpoint predates the lead's explicit-site change. Until that
reference update is merged, the oracle combines its unchanged instructions with
the independently copied, reviewed suffix in
`tests/fixtures/studio/emission-tracking-site-section.md`. Once the committed
reference has that section, the oracle compares its complete bytes directly.
The generator's complete emission-tracking output is also checked against the
lead's updated read-only reference during the handoff.

For a reference comparison without changing its files:

```sh
python3 tools/build_studio_package.py emission-tracking --out /tmp/aibast-studio-reference
```

The utility-billing override names the exact method-local `fpl_table` literal
that its Markdown calls `FPL_REFERENCE_2025`; it is still parsed, never executed.

## Validation and journey regeneration

Use the same validator as the managed-app lifecycle when brainfreeze studio is
available locally:

```sh
export AIBAST_BRAINFREEZE_ROOT=/path/to/brainfreeze-studio
python3 tools/build_studio_package.py asset-maintenance-forecast
python3 -m pytest -q tests/test_studio_package.py tests/test_studio_data.py tests/test_studio_walkthrough.py
```

`--brainfreeze-root` is the equivalent explicit option. It imports
`brainfreeze_studio.managed_app.check_spec` through the supplied local path and
validates every emitted app. Without that option/environment variable, generation
still runs local data, mapping, privacy, and walkthrough checks; the external
validator tests are explicitly skipped if brainfreeze studio is not installed.
That is not a substitute for running the lifecycle validator before handoff.

## Readable agent and app names

Except for emission-tracking's fixed live names, names use the deployment
display name with a trailing ` Agent` removed. Agents end in ` Studio` or
` Manual` and are at most 30 characters. Apps end in ` Workspace` or
` Workspace Manual` and are at most 40 characters. Whole trailing words are
dropped only as needed; generic trailing words are removed first, and dangling
`and`/`&`-style joiners are not left at the end. No initials, abbreviations,
partial words or hash suffixes are invented.

Names are allocated across all 51 advertised workshops, including those with
record-source blockers. If truncation creates a collision, both colliding names
recover a distinguishing title word, dropping a different whole word when
necessary. Original word order and spelling are preserved. An impossible
whole-word allocation fails explicitly instead of creating an unreadable name.
For example, asset-maintenance-forecast is **Asset Maintenance Studio** /
**Asset Maintenance Manual**, with **Asset Maintenance Forecast Workspace** /
**Asset Maintenance Workspace Manual** as its app names.
Non-reference agent-name overrides are rejected; emission-tracking alone keeps
its fixed live agent and app names.

## Runtime instruction budget

Repository GLOBAL-INSTRUCTIONS templates are capped at 7,000 characters. This
reserves room for a 1,000-character site URL while staying below the runtime's
8,000-character limit after replacing the single `YOUR_SITE_ADDRESS` token.
The generator rejects an over-budget result rather than truncating it.

When the full instructions exceed that template budget, the generator preserves
the complete source-adapted instruction contract in
`studio/agent/knowledge/<slug>-instruction-controls.md` and adds it to the agent's
required knowledge and Manual uploads. The shorter global instructions retain
every list-column mapping, the exact site section, routing sections, mandatory
review/footer sections and safety boundaries. They require retrieving and
following the complete control file before each answer; no policy is silently
dropped. Data, extraction provenance, skill files and app definitions do not
change as a result of this compaction.

Regenerate the existing journey surfaces and source bundle for each new edition:

```sh
python3 tools/scaffold_solution_journey.py asset-maintenance-forecast --allow-pending --build-export
```

This adds the conditional Studio edition links to the workshop README and quest
and refreshes the source ZIP. Never hand-edit generated HTML. Do not regenerate
the emission-tracking reference or its bundle as part of an unrelated batch.
