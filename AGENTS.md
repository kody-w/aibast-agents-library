# AGENTS.md

Guidance for autonomous agents working **on** this repository. If you are an
agent trying to *use* the library rather than change it, start at
[`llms.txt`](llms.txt) or fetch
[`api/v1/agent.json`](https://microsoft.github.io/aibast-agents-library/api/v1/agent.json).

## What this repository is

The AIBAST Agents Library (**ms-rapp**): a catalog of single-file AI agents, the
runtime that executes them, a pinned mirror of the RAPP/1 protocol corpus, and a
static API over all of it. Read [`CLAUDE.md`](CLAUDE.md) for the architecture.

## Before you change anything

Run the gates. They are fast and they encode the rules that are easy to break:

```bash
python3 -m pytest tests -q                  # agent contracts (841 cases)
bash tests/test_library_frontend.sh         # release gates
python3 scripts/corpus_sync.py --check      # pinned corpus integrity
```

## Rules that will fail the build

- **Never edit kernel content.** `rapp_brainstem/**` and the root installers are
  locked by SHA-256 in `rapp/BRAINSTEM-LOCK.json`. Fixes flow down from upstream
  through a sync pull request that regenerates the lock in the same commit.
- **Never edit a pinned mirror.** Files under `rapp/spec/`, `rapp/handbook/`, and
  `rapp/standards/` are byte-exact copies; the manifest verifies them.
- **Never commit a secret.** Configuration goes through `requires_env`. A gate
  scans for signed URLs, keys, tokens, and real tenant endpoints.
- **Never regenerate by hand.** `registry.json`, `api/**`, `llms.txt`, and
  `llms-full.txt` are generated. Run `python3 build_registry.py` and
  `python3 scripts/build_api.py`; a gate fails if they are stale.
- **Never add a feature by editing shared code.** New capability is an
  extension under `rapp/ext/` — see [`rapp/ext/PATTERN.md`](rapp/ext/PATTERN.md).
  A gate proves that removing every extension leaves the core byte-identical.

## Adding an agent

One file under `agents/@<publisher>/`, with a `__manifest__`. See
[`docs/PUBLISHING.md`](docs/PUBLISHING.md). The contract tests import it,
instantiate it, and run it, so it must work standalone.

## Adding documentation

Write a note in `brain/` with YAML frontmatter and `[[wikilinks]]`. Indexes,
backlinks, tags, and the graph are derived — never hand-maintain an index.

## Conventions

- Python 3.11, standard library only in build scripts.
- Generated documents carry `schema` and `generated`; extension output also
  carries `protocol`.
- Builds are stable-write: rerunning with no input change produces no diff.
