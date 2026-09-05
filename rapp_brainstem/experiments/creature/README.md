# RAPP Brainstem: creature terrarium

One Brainstem. Several standalone creature agent files. Real, bounded programs and recorded evidence, not a chatbot pretending that a simulation ran.

This is an **experimental, opt-in experience**, not a change to the production installer or Grail kernel. It uses the official macOS/Linux installer advertised at [aka.ms/rapp](https://aka.ms/rapp), inside a separate home directory, then adds the creature files and a local evidence view.

## Install and open

Requires macOS or Linux, Python 3.11+, and GitHub Copilot access for Brainstem chat.

```bash
curl -fsSL https://raw.githubusercontent.com/kody-w/aibast-agents-library/astra/brainstem-creature/rapp_brainstem/experiments/creature/install.sh | bash
```

The installer leaves your existing `~/.brainstem`, port 7071, shell configuration, and Copilot plugins untouched. Its own files live under `~/.brainstem-creature`. The standard installer's shell-profile changes are confined to `~/.brainstem-creature/bootstrap-home`.

Open the terrarium at **http://127.0.0.1:7082**. The isolated Brainstem's original UI remains at **http://127.0.0.1:7081**. At launch, an existing standard Brainstem login can be reused through a read-only file reference; its credential values are not copied into the installation manifest, agent files or eggs, and the original login is never changed. Otherwise authentication uses the new Brainstem's `/login` flow. Use `--independent-auth` when installing or starting to sign in separately.

The command runs in the foreground. Stop it with Ctrl-C; nothing in the terrarium's history is erased. Start it again with:

```bash
~/.brainstem-creature/start
```

Install without starting by appending `--no-start` after `bash -s --`. For a local source checkout:

```bash
python3 rapp_brainstem/experiments/creature/setup.py --source-root "$PWD" --no-start
```

## A creature is a file

The installer introduces Astra with all sensors, Ember without hazard sensing, and Moss without distance sensing. Those restrictions apply to the executable programs, not just the labels. They start unhatched: the UI does not invent genomes, scores, movement or history for them.

Each file contains the complete agent implementation and a literal `CREATURE_PROFILE` with its stable identity, display name, unique Brainstem tool name and capabilities. Each creature has independent state beneath `data/<id>`. New creatures can be introduced through the caretaker, `CreatureTwin`, which changes only the profile in a trusted template.

```text
~/.brainstem-creature/
  agents/                 Active standalone *_agent.py files
  dormant/                Sleeping agent files
  data/<id>/              Separate state, memory and lineage
  data/<id>/public/       Public-to-this-local-view evidence and exported egg
  payload/                Installed template, file reader and view
  bootstrap-home/         Separate installation of the official Brainstem
  logs/                   Local installation and Brainstem logs
```

Move a file out of `agents/` and its creature becomes dormant. The evidence view reads the actual directory, rather than a hardcoded creature list. Restoring the original file restores its discoverable capability and retained state.

```bash
mv ~/.brainstem-creature/agents/ember_agent.py ~/.brainstem-creature/dormant/
mv ~/.brainstem-creature/dormant/ember_agent.py ~/.brainstem-creature/agents/
```

Moving a file to an arbitrary folder also preserves its data. The view reports the missing executable and asks for the original file to be restored; it does not invent a replacement or silently reset the creature. Removing a file prevents subsequent discovery; an already-running bounded invocation may finish.

**Only install Python agent files you trust.** Brainstem executes their Python. The evolving genome has a separate restricted interpreter; that restriction is not a sandbox for arbitrary host Python files.

## Observe real behavior

Hatch a creature, run twelve bounded generations, then race its descendant against its ancestor on held-out courses. The inspector exposes the executable genome, accepted changes, unchanged generations, capabilities, memory and measured results.

Movement comes from actual recorded step traces. A replay is labeled as a replay and stops at its end. Idle and dormant creatures do not secretly run. Training, primitive-control comparisons and final races use disjoint seed domains; race courses have not already been used by the evolutionary comparison.

The creature engine uses the actual [LisPy runtime from `kody-w/lisppy`](https://github.com/kody-w/lisppy/tree/5e3a2e3275825ffecdbc4b12541aff48d7ff235e), pinned to commit `5e3a2e3275825ffecdbc4b12541aff48d7ff235e`. The installer adds `rappterbook-lispy-runtime` once to the twin's private Python environment; each creature remains a standalone agent file using that shared VM, just as it uses Brainstem's shared `BasicAgent`.

The VM uses its safe **core** profile, never the trusted profile. The creature adds a restricted genome grammar and bounded arithmetic on top of the runtime's actual instruction, call-depth, reader, source, collection and output limits. Host networking, filesystem access and Python execution are not genome capabilities. These are deterministic in-process limits, not a claim of adversarial operating-system isolation.

Reusable tool definitions belong to the genome and its inherited history. The evidence view exposes actual invention attempts, their source and outcomes, and the primitive-only comparison when available. Both lineages receive the same selection fuel ceiling, including an equal diagnostic allowance. Actual usage includes the tool-cost probes; unused allowance is not counted as spent. A tool-capable lineage is not automatically declared better than its baseline.

Lisppy increments its counter before rejecting an over-limit step. Receipts therefore expose both admitted `used` steps and the untouched upstream `attempted_used` count, including the rejected attempt. A fuel-exhausted replay stops without performing another world action.

### Recorded example, seed 41

The three initial profiles completed twelve generations and then raced on twelve untouched courses. These are scores in this toy environment, not general intelligence benchmarks.

| Creature | Founder race score | Generation 12 race score | Inherited tools | Separate primitive-only comparison |
| --- | ---: | ---: | ---: | --- |
| Astra | 9,553 | 9,345 | 1 | Primitive-only won |
| Ember | 9,553 | 9,553 | 0 | Tie |
| Moss | 2,102 | 7,792 | 1 | Primitive-only won |

Moss collected 73 food units versus its founder's 24, but that does not establish an advantage over the independently evolved primitive-only control. Astra's regression and Ember's unchanged program remain visible alongside the improvement. The interface preserves failed inventions and the actual limits that ended a replay.

## Eggs and fresh processes

An exported egg contains creature state, program, memory, lineage and reproducibility information. The checksum detects accidental changes; it is **not** a signature proving who authored the egg. Import also validates the permitted program and bounded state. Existing creatures are never overwritten by an import.

Download an egg from the creature inspector. Resume into a fresh installation root and unused ports:

```bash
~/.brainstem-creature/bootstrap-home/.brainstem/venv/bin/python ~/.brainstem-creature/payload/setup.py \
  --root ~/.brainstem-creature-resumed \
  --port 7083 --ui-port 7084 \
  --egg /path/to/creature.egg.json
```

The installer stages the complete egg in the new creature's private inbox. The fresh Brainstem receives only its SHA-256 content identifier through `/chat`, so a model never needs to reproduce a large genome/history verbatim. The creature reads that fixed, bounded inbox file, checks its content identifier, then validates the entire egg. Arbitrary paths are not accepted. An HTTP success alone is not treated as successful restoration: the runner requires resumed-state evidence matching the supplied generation and genome.

## Boundaries

The view is a loopback-only file reader and same-origin proxy, not a second AI runtime. All creature and caretaker actions go to the unchanged Brainstem `POST /chat`. Read-only polling reads real agent files and public snapshots; it does not spend model calls or trigger evolution.

The original core's hash and source commit are recorded in `terrarium.json`. The launcher refuses an unexpected core change. No service, login item, cloud deployment, scheduled evolution or production update is installed.

This is a software simulation. There are no claims of sentience, biological life, or guaranteed evolutionary progress.

## Focused tests

From the repository root, using an environment with the existing pytest dependency and the pinned optional runtime in `requirements.txt`:

```bash
python3 -m pytest -q \
  rapp_brainstem/tests/test_genome_creature_agent.py \
  rapp_brainstem/tests/test_creature_twin_agent.py \
  rapp_brainstem/tests/test_creature_terrarium.py
```
