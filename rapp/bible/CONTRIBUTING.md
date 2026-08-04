# Contributing to RAPP Bible

The Bible aggregates content from canonical repos. **Two sources of truth**
is the model: each canonical repo is authoritative for its content; the
Bible holds a verified snapshot plus the index that ties everything
together.

## Where to make changes

### To change a spec

Edit the spec in its canonical repo, not here.

| Spec | Canonical repo |
|------|----------------|
| CONSTITUTION.md, NEIGHBORHOOD_PROTOCOL.md, kernel SPECs | https://github.com/kody-w/RAPP |
| Network SPEC | https://github.com/kody-w/RAPP-Network |
| Catalog SPEC | https://github.com/kody-w/RAPP_Store |
| Registry SPEC | https://github.com/kody-w/RAR |
| Senses SPEC | https://github.com/kody-w/RAPP_Sense_Store |

The Bible's nightly sync (`scripts/mirror_sync.py`) will pull your change
within 24 hours, or open a PR sooner via the nightly-sync GitHub Action.

### To add a new repo to the index

Edit `scripts/build_repo_pages.py` and add an entry to `INVENTORY`. Then
run `python3 scripts/build_repo_pages.py` and commit the generated files.

### To change the landing page, quickstart, or any Bible-native content

Edit it here, in this repo. These are written-here-not-mirrored:

- `README.md`
- `index.html`
- `CONTRIBUTING.md`
- `quickstart/*.md`
- `repos/*.md` (regenerate via `scripts/build_repo_pages.py`)
- `repos/_index.md` (regenerated)
- `SPEC/_index.md`

### To add a customer reference, a private-repo link, or an engagement name

Don't. The Bible is public. PII and private content are blocked by tests:

- `tests/test_no_pii.py` — blocks a list of engagement names from ever
  appearing in committed files.
- `tests/test_no_private.py` — blocks references to private repos as
  content sources.

If you have a legitimate need (e.g. a new generic example), open an issue
first.

## Running the tests

```bash
cd RAPP-Bible
pytest tests/
```

All tests should pass. `test_spec_freshness.py` prints drift as warnings
when run with `--allow-drift`; without that flag it fails on drift.

## Re-syncing specs

```bash
python3 scripts/mirror_sync.py            # fetch + write all mirrored specs
python3 scripts/mirror_sync.py --check    # check drift without writing
```

The nightly GitHub Action runs the sync and opens a PR if anything
changed.

## Style

- No emojis in committed files.
- ATX headers (`#`, `##`, ...).
- Tables for structured data.
- Code fences with language tags.
- Mirrored files keep their `<!-- MIRRORED FROM ... -->` provenance line.
