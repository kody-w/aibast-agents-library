---
description: Compare real local Brainstem and native Copilot Studio responses for functional parity, allowing natural wording differences.
argument-hint: Conversion run or local Brainstem URL, native target, and shared test cases
---

# RAPP response parity

Read `skills/rapp-to-studio/SKILL.md` and execute its compare/repair/retest loop
against the existing conversion run. Reuse the same native target and frozen
source contract; do not restart intake or create another agent.

Inputs: $ARGUMENTS

Send the same cases through the real local Brainstem `/chat` surface and the
exact deployed native Copilot Studio API. API testing is the default; browser
testing is optional. Prefer Microsoft's Direct-to-Engine client for CLI agents;
use Direct Line only when the target exposes that supported channel. Obtain
explicit permission before publishing a dedicated test target, and preserve its
authentication. Retain both actual responses and tool/state evidence.

Delegate paired-response evaluation to
`rapp-studio:response-parity-reviewer`. Require equivalent meaning and task
outcomes, not identical wording. Exact facts, calculations, safety decisions,
state changes, error handling, and required actions remain strict invariants.
Missing execution evidence is `blocked`, never a fabricated pass.

On functional differences, send the reviewer evidence to the existing
Microsoft Architect session, have it repair the native agent, and have
Microsoft Manage update the same target. For published-API tests, republish
only under the user's recorded test-publication permission, and verify the
tested published revision changed. Rerun the shared cases after each
repair. Continue until all required cases pass or a genuine prerequisite or
native-platform blocker prevents progress. Never edit the local source,
weaken expected outcomes, drop cases, or echo canned baseline responses to
manufacture a match.
