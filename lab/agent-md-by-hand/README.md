# Three by hand: pointer agent files (2026-11-18)

A hand run, kept as the record a generator must reproduce. Not part of the library yet.

Each folder holds one solution:
- `<name>.agent.md`: a GitHub Copilot custom agent file that points at the solution's `agent.py`.
- `SKILL.md`: the same pointer as a skill.
- `host-run.txt`: what a real Copilot did when given only the agent file and the recipe's test question.

Both files fetch the `agent.py` and `basic_agent.py` by a link pinned to one commit, check each
SHA-256, ask the agent what it can do, run one operation and relay the output unchanged.

Findings from the hand run:
1. A colon inside an unquoted `description` breaks the file header. Always quote it.
2. The agent file needs `basic_agent.py` beside it. Two files, two fingerprints.
3. The agent's own `metadata` lists its operations, so the pointer never copies them.
4. One recipe (`emission-tracking`) has no `operations` list. The agent file's metadata had it.
5. Only solutions with their own `agent.py` can use this: 47 of 72 today.
