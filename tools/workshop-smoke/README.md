# Workshop smoke tests

The automation checks that keep the one-page workshop honest. Run them after
any change to the twin, the playbooks, the scaffolds, or the workshop page —
they are the tests that caught real defects during the first live run.

| Test | Command | What it catches (real examples) |
|------|---------|--------------------------------|
| 1. Scaffold validity | `python3 tools/workshop-smoke/validate_scaffolds.py` | Manifest schema drift, missing listed files, unparseable YAML, missing SYNTHETIC banners, verification expectations whose numbers aren't traceable to the captured agent outputs |
| 2. Twin payload | `python3 tools/workshop-smoke/twin_payload_test.py` | Mission matching (twin once matched itself on "copilot studio"), raw-URL `@`→`%40` encoding 404s, mirror-chain fallback, playbook + live-context assembly |
| 3. Hotload + /chat | `bash tools/workshop-smoke/hotload_chat_test.sh` | The tool-name bug: a function name containing `@`/`/` silently never registers with the Copilot API and the brainstem LLM freelances to another agent |
| 4. Headless mission (one stack) | `bash tools/workshop-smoke/run_one_mission.sh <slug> "<name>"` | The whole buzzsaw: twin doctrine → Copilot CLI executes → published agent. Exit line must be `MISSION RESULT: SUCCESS — <schemaName> published` |
| 5. Workshop page | `node tools/workshop-smoke/workshop_page_test.mjs` (needs `npm i playwright`) | Picker loads from raw, personalization, per-agent verification cards, deep links, verdict persistence |

Environment: tests 2–4 accept `AIBAST_REPO` / `AIBAST_REF` to point at a
staging fork; defaults are the upstream repo. Test 3 needs a running
brainstem on :7071; test 4 needs pac auth and a real environment and
publishes an agent — run it in a test environment only.

Known service signature (not a test failure): if Copilot Studio's Preview
pane bounces to /home or the canvas shows `javascripterror`, the ecs.office.com
config service is down — build-side checks still stand, runtime chat
verification waits for recovery.

## first_party_track_test.mjs
The first-party branch must be a real guide, not a dead end. Asserts the track
renders (surface, prerequisites, GA/Preview caveat, hazard warning), that both
Microsoft Learn links are present with explanatory context, that the
Copilot Studio build steps hide themselves, and that switching back to a custom
agent fully restores them. Every URL, status and prerequisite in
`twin/first_party.json` was verified against Learn — corrections belong in that
file, not in the page.

    node first_party_track_test.mjs [pageUrl] [repoRoot]

`repoRoot` routes `first_party.json` to your local copy so edits can be tested
before they are pushed (the page always reads library data from the raw mirrors).

## personalization_test.mjs
The page's premise is that every agent in the library runs through it. An
adversarial review found Steps 3, 6 and 7 describing Field Service Dispatch for
all 104 agents, including copy-paste CLI blocks that would scaffold a project
with the wrong name. This asserts no default-agent vocabulary survives a
different selection, that bad deep links explain themselves instead of dying,
and that switching picker modes never leaves an empty page.

    node personalization_test.mjs [pageUrl]

Note the leak regex deliberately excludes bare "dispatch" and "technician":
IT Helpdesk's own scaffold uses both, and flagging them reported the page for
correctly showing the right agent.
