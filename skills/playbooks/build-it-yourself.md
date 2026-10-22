# Build it yourself

This playbook is fetched at run time by the AIBAST Easy Mode workshop skills,
from the same pinned commit as the workshop. Use it when nothing in the
library comes close to the user's need, or when the user wants to build their
own agent from the start. It follows the same method the library templates
were built with, so the result can go through the same Copilot Studio steps.

## 1. Describe the need and plan before building

1. Ask the user to describe the business problem in two or three sentences:
   who does the work today, what goes wrong, and what a good answer looks like.
2. Propose the smallest version worth showing first, in one paragraph.
3. Before writing any code, list the operations the agent needs, one line
   each, and write them to `PLAN.md`. Wait for the user to agree.

## 2. Write fictional example data

1. Never ask for, accept, or store real customer records, names, or
   credentials. Ask for field and column names instead.
2. Create small, realistic, fictional example data: just enough to prove the
   idea. When the user works with a Microsoft application, such as Dynamics
   365, shape the records like that application's own records.
3. Write the full real-world scale (volumes, systems, regions) to `SCALE.md`
   for later, without real names.

## 3. Write the tests, then build

1. Write test cases first, as questions a real person would ask, in the
   user's own words. For each, list the facts the answer must include.
2. Build one agent file that follows the library's single-file pattern: a
   class that extends `BasicAgent`, a `metadata` description that says
   plainly when to use it, and a `perform` method with one operation per
   line in `PLAN.md`.
3. Numbers, totals, and dates are calculated by the agent's code from the
   data, never written by the model from memory. Reports and slides take
   their figures from that calculation.
4. The agent recommends; people approve anything that changes a record.
5. Run every test case and show which passed and which failed. When an
   answer fails because the agent was not used, fix the agent's `metadata`
   description so it matches how people ask, then run all cases again.

## 4. Raise the bar, then share

1. Ask the user whether each test sounds like a real person. Rewrite any that
   do not, and keep that standard for new tests.
2. Write a one-page summary: the problem, what the agent does, the operations,
   and the test results. Suggest sharing it with the account team first, then
   the customer.

## 5. Move it into Copilot Studio

Continue with the workshop skill's `Deploy it into Copilot Studio for me`
step, using the new agent, its fictional data as knowledge, and its test cases
as the Preview cases. Stay in Draft. To connect live systems later, follow
`adapt-and-connect.md`, section "Connect live systems".

To ask the AIBAST team to consider adding this as a library workshop, share
`https://microsoft.github.io/aibast-agents-library/request-use-case.html`.
Requests are reviewed; not every request becomes a workshop.
