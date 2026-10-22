# Adapt a workshop template, and connect live systems

This playbook is fetched at run time by the AIBAST Easy Mode workshop skills,
from the same pinned commit as the workshop itself. Follow it step by step.
It is optional: the library version on fictional data is the standard path.

The templates start from fictional data. When the learner works with a
Microsoft application, such as Dynamics 365, the adapted fictional data takes
that application's shape, so the later move to live data is a swap rather
than a rebuild. GitHub Copilot and this playbook turn the template into
whatever the learner needs.

## Adapt it (optional)

The library version is the standard path. When the user's need is different,
for example another process, other columns, another report, or a system they
already use, help them turn the tested template into their own version. Start
when the user says `Adapt it to <what I need>`, or describes a difference after
a successful test.

1. Ask at most two short questions: what should change (the job, the data, or
   the system it should work with), and what a good answer looks like to them.
2. Never ask for, accept, or store real customer records, names, or
   credentials. Ask for field and column names and a description of the data
   instead, and write new fictional example data in that shape.
3. When the user names a Microsoft application, such as Dynamics 365 Field
   Service, Dynamics 365 Sales, Dataverse, SharePoint, Excel, or Teams, shape
   the fictional data like that application's own records and field names, so
   the later move to live data is a swap rather than a rebuild.
4. Work on a copy named `<solution>-adapted` in the workspace. Never change
   the library original.
5. Change as little as possible: keep the operations that still fit, rename or
   add only what the new need requires, and keep the safety boundary (the
   agent recommends; people approve anything that changes a record).
6. Numbers, totals, and dates must be calculated by the agent's code from the
   data, never written by the model from memory. Reports and slides take their
   figures from that calculation.
7. Rewrite the test cases in the user's own words, keep the original cases
   that still apply, and run every case the same way the workshop skill ran
   the originals (in the Brainstem lane, import the adapted agent through
   `POST http://localhost:7071/agents/import` first). Show which passed and which failed.
8. Persist `status: adapted-tested` with the list of changes, then offer:
   `Deploy it into Copilot Studio for me.` Deploy the adapted copy when one
   exists.

## Connect live systems (optional, after the Draft works)

Only when the user asks, and only after the adapted or original Draft passes
its Preview cases:

1. Confirm the user has an environment their Power Platform admin approved
   for this, with the data loss prevention policy that allows the needed
   connectors. If not, stop here and help them write the request to their
   admin.
2. List each connection point from `deployment.json` (production replacement
   connections or required connections) next to the system the user named,
   then list the real system's fields and map each one to the fictional
   field it replaces. Real systems have custom fields and permissions; this
   is a mapping step, not a swap.
3. Prefer the standard connector: Dataverse or the Dynamics 365 connector for
   Dynamics applications, the matching Microsoft 365 connector for Excel,
   SharePoint, Outlook, or Teams, and otherwise the system's own Power Platform
   connector or a custom connector the user's IT team approves.
4. Add each connector to the Draft agent as a tool, read-only first, against a
   test environment. Remove only the fictional knowledge file that the tool
   replaces.
5. Keep the questions and the answer shape unchanged, and rerun the Preview
   cases. Every answer must now come from the tool's result.
6. Never store keys, passwords, or tokens in files or chat. Sign-in happens in
   Copilot Studio with the user's own account and their organization's
   permissions.
7. Any action that creates or changes a record needs the system owner's
   approval and asks the person to confirm before it runs.
8. Stay in Draft. Publishing is the organization's decision.

The local agent, including any Brainstem copy, stays on fictional data. Live data is only
used inside Copilot Studio, where the organization's sign-in and permissions
apply.

