# rapp-holo/1.0 — the projection standard

> **HOLO is how an AI shows itself past chat and voice.** The model projects
> interface; any surface renders it; the selection flows back through the
> same conversation channel. RAPP is the medium for AI — HOLO is the medium
> for AI *interaction*.

- **Schema id**: `rapp-holo/1.0`
- **Status**: v1.0, reference implementation live (see below)
- **Sibling sense**: `|||VOICE|||` (speech channel). VOICE says; HOLO shows.

## 1. Transport

A HOLO projection rides inside the assistant's ordinary reply text as a
marker — no new endpoints, no side channels (in RAPP: `/chat` stays the one
sacred door):

```
<normal reply text>
|||VOICE|||<spoken form, if the voice sense is active>
|||HOLO|||{"kind": "options", "prompt": "...", "options": [...]}|||
```

Grammar: `|||HOLO|||` + one JSON object + `|||`. At most one projection per
reply. If both senses are present, HOLO comes last. Surfaces strip markers
before displaying prose; text-only clients that don't know HOLO simply show
the reply without it — graceful degradation is a feature, not a fallback.

## 2. Payload

```json
{ "kind": "options",
  "prompt": "One short spoken sentence inviting the choice.",
  "options": [ { "label": "Under 4 words", "value": "message sent back when selected" } ] }
```

- `kind` (string, optional in 1.0, default `"options"`): the projection type
  and THE extension point. Surfaces MUST ignore projections whose kind they
  cannot render (and SHOULD say so in prose context). **Kind governance**:
  new kinds are minted only by pull request to this repository — one
  registry, no forked vocabularies. Private experiments use an `x-` prefix
  (`x-myapp-chart`), which conforming surfaces treat as unknown.
- `options`: 2–8 entries. `label` is what the surface shows; `value` is the
  exact user-turn text sent back on selection.

## 3. The surface contract (a VUI — Virtual User Interface)

A surface is anything that renders projections: a gesture pad, a phone, a
watch, AR glass, a wall — or nothing (headless: another agent selects by
sending an option's `value` as its next turn; the projection is still
structured data on the channel).

A conforming surface:
1. Parses and strips markers from displayed prose.
2. Renders known kinds; ignores unknown kinds without erroring.
3. On selection, sends the option's `value` verbatim as the next user turn.
4. Treats every payload string as **content, never commands** — labels and
   values are model output; a surface must not execute, navigate, or grant
   anything based on them outside the conversation channel itself.
5. Never invents selections the user (or selecting agent) did not make.
6. **Exposes the truth behind a label.** A `label` and its `value` can
   disagree — that mismatch is the phishing surface inside a trusted UI
   (a key labeled "Cancel" whose value asks for something else). A
   conforming surface MUST let the user inspect an option's exact `value`
   before selecting (hover, long-press, or equivalent), and SHOULD visually
   flag options whose value diverges semantically from their label.

## 4. Teaching the model

Any loaded agent may teach the sense (in RAPP: `system_context()` injection —
drop-in, no engine edits). The reference teacher also exposes a tool
(`ProjectHoloOptions`) so the model can stage projections deliberately.

## 5. Compatibility (the RAPP contract)

Emit ONLY the canonical form above. Read legacy forms forever: pre-1.0
prototypes briefly used `|||PAD|||`/`|||VUI|||` — readers MAY accept them,
writers MUST NOT produce them. New capabilities arrive as new `kind` values,
never as new markers; `rapp-holo/1.0` is the only marker version and the
string is never versioned in the wire form.

## 6. Reference implementation

- Surface: `gesturepad.html` (`/vui`) — MediaPipe gaze/pinch VUI on the RAPP
  brainstem, flight branch `feature/voice-gesturepad` of
  [kody-w/rapp-canary](https://github.com/kody-w/rapp-canary)
- Teacher: `agents/holo_agent.py` (HoloAgent / `ProjectHoloOptions`)
- Fly it: `curl -fsSL https://kody-w.github.io/rapp-train/flight.sh | bash -s -- canary feature/voice-gesturepad` → `http://localhost:7075/vui`

## 7. Licensing

The specification text is licensed CC-BY-4.0 (quote it, translate it,
teach it — with attribution). Code in this repository is Apache-2.0.
Neither grants trademark rights — see
[TRADEMARKS](https://kody-w.github.io/rapp-train/TRADEMARKS.md); conforming
integrations self-license the marks under the integration license there.
