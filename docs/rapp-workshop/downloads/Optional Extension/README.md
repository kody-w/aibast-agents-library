# Optional Copilot Studio extension

The required workshop ends with a working, tested local `agent.py`. This folder
supports an optional facilitator-led extension.

## Recommended Teams-share file

Share:

`rapp_copilot_studio_extension_agent.py`

Participants drop/import that one file into the local Brainstem. It embeds the
workshop prototyper and connected-solution packager.

## Participant flow

1. Import the extension file into Brainstem.
2. Run `action=setup`.
3. Use `start`, `build`, and `test` with the approved scenario.
4. Use `package` to produce:
   - a local M365-style HTML/rapplication demo; and
   - an import-ready Copilot Studio solution ZIP.
5. Use `deploy` only when the participant separately has:
   - a licensed Copilot Studio instance;
   - access to the target environment;
   - maker/deployment rights; and
   - an approved local settings file.

Never paste credentials or secrets into chat.

## Advanced facilitator files

- `transcript2prototype_agent.py` - full local transcript-to-prototype pipeline
- `connected_solution_agent.py` - connected-agent solution packager

The single-file extension already embeds both. The separate files are provided
for advanced facilitation, review, and maintenance.
