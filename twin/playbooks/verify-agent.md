# Mission: verify the deployed agent, honestly

Outcome: a pass/fail verdict per verification question, with what the agent
actually answered — evidence, not vibes. A failing gate means the deployment
is NOT done, and saying so is the deliverable.

{{STACK_CONTEXT}}

## How to run it

1. Open the agent in Copilot Studio (Agents list in the target environment)
   and use the **Test pane** — or, if it is shared into Teams, test where the
   person will actually demo it.
2. Ask each verification question from the context block, in order, exactly
   as written.
3. Compare the agent's actual answer to the expected result. Quote the
   relevant line of the actual answer in your report.
4. The refusal-style questions matter most: an agent that answers when it
   should refuse is a liability, not a demo.

## Verdict rules

- Every question passes → report "verified" with the evidence.
- Any gate question fails → report exactly which, what the agent said instead,
  and the likely fix (a component that never pushed is the usual culprit —
  re-run the deploy mission's push step). Do not soften a fail into a "mostly
  works".
