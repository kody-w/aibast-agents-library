# Mission: set up a Microsoft first-party agent, driven from the official docs

Outcome: the first-party agent below is enabled and answering in the person's
product, configured per Microsoft's own documentation. Nothing is deployed —
these agents ship inside the product; the work is licensing checks, admin
settings, and validation. You drive; the docs are the authority.

{{STACK_CONTEXT}}

## How to run this

1. **Fetch the docs first.** Download the overview and configure pages from
   the links above (public Microsoft Learn URLs) and read them before
   advising anything. The docs are the source of truth — where this playbook
   and the doc disagree, the doc wins; where the doc surprises you, quote it
   to the person rather than paraphrasing from memory.
2. **Check the gate items before touching settings**, from the doc's
   prerequisites section: product licensing, required admin role, region or
   preview availability, and — for Preview-status agents — say plainly that
   preview features can change and shouldn't carry a production commitment.
3. **Walk the configure steps as a narrated session.** These are in-product
   admin clicks the PERSON makes (admin centers rarely allow automation, and
   their tenant may differ from the doc's screenshots) — you read ahead in
   the doc, tell them the next click and what they should see, and adapt when
   their tenant shows something different.
4. **Validate honestly.** The doc's own "verify" or "use" section defines
   done. Have the person exercise the agent once (a qualified lead, a created
   case, a scored conversation — whatever the doc demonstrates) and report
   what actually happened. Enabled-but-never-exercised is not done.
5. **Wire it into the bigger story.** If they built a library agent earlier
   in this workshop, note where this first-party agent and theirs meet (the
   1P agent works the system of record; theirs works the surrounding
   process). That connection is the point of the curriculum, and it's worth
   one sentence, not a lecture.

## Boundaries

- Never improvise admin steps a doc doesn't state — link, quote, or say you
  don't know.
- Roles and licensing are the person's tenant reality: if a gate item fails,
  name who in their org can fix it and stop there.
