---
description: Run the default real deployment test: map the RAPP OOTB agents, deploy a native Studio Draft, and repair until local-vs-native functional parity passes.
argument-hint: Optional target environment or existing OOTB test run
---

# Default RAPP Studio test

Read `skills/test-ootb/SKILL.md` relative to this plugin's installation.
Execute it, using these supplied choices where present:

$ARGUMENTS

No arguments means the complete OOTB deployment/parity example, not manifest
linting or mocked transcripts. Reuse the user's existing authentication and
selected environment; otherwise present interactive sign-in and an environment
picker. API testing is the default; browser checks are optional. If the API
needs a published runtime, obtain explicit permission for publication of only
the dedicated test agent and its repair iterations.
