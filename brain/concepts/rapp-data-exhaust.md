---
title: RAPP data exhaust
tags: [ms-rapp, concept, method]
summary: The by-product of doing the work holds a negative of the shape that produced it — read the negative and you recover the shape.
updated: 2026-08-05
---

# RAPP data exhaust

**RAPP data exhaust** is the by-product of building the platform: not the code
and not the documents, but the *shape of how the work actually went*. Which
correction had to be given twice. Which review found a real defect and which
found noise. Which rename broke an installer. Which question a newcomer asks
first, and which one they never think to ask.

Most projects treat this as waste. It is the most information-dense thing they
produce.

## The negative

The useful part is not that exhaust is *extra data*. It is that exhaust is a
**negative of the shape that emitted it**.

You usually cannot observe the thing you most need to model: the maintainer's
actual intent, the real constraints, the boundary between "fine" and
"absolutely not", the failure mode that has already happened once here. Nobody
writes those down completely, because to the person holding them they are
obvious.

But every one of those shapes presses an impression into what it produces. A
correction is a cast of the boundary that was crossed. A gate is a cast of a
defect that got through once. A rejected approach is a cast of a constraint
nobody stated. Repeated instruction is a cast of something the system keeps
failing to infer.

So you do not need the positive to be described. **Read the negative and the
positive is recoverable** — and it comes back at higher fidelity than a
description would have had, because a description is what someone remembered to
say, while a negative is what actually happened.

That is the whole method: an agent facing a problem model it cannot see
directly can still work with precision, because the exhaust around the problem
already carries its shape.

## Use it or lose it

The richest exhaust is perishable.

A session transcript is discarded. A rationale evaporates the moment a pull
request merges. The reason a gate exists is obvious for a week and mysterious a
year later — at which point someone deletes it as "flaky" and reintroduces the
defect it was catching.

Exhaust that is not captured while it is warm is not recoverable later. Not
expensive to recover — **not recoverable**, because the impression was in a
medium that no longer exists.

## What this repository does about it

1. **A lesson becomes an artifact.** When exhaust teaches something, it lands as
   a durable thing: a gate, a decision note, a constitutional rule. Never as a
   remembered preference, which is exhaust that will evaporate again.
2. **Prefer the gate to the reminder.** If a lesson can be machine-checked,
   checking it *is* the way to remember it. See
   [[decisions/why-extensions-are-discovered]] — a rule that survives because it
   is enforced, not because anyone recalls it during a merge.
3. **Record the why, not only the what.** A decision note states what was
   rejected and why. The rejected branch is the part that stops the question
   being reopened — and it is exactly the part a diff cannot carry.
4. **The boundary is absolute.** Exhaust is mined for shape and lesson. Raw
   transcripts, customer content, private-estate detail, and personal data never
   become public artifacts — only the generalized lesson does. When in doubt the
   lesson ships and the source does not.

## Worked examples from this repository

- A blanket text substitution once turned a PowerShell function name into
  `Install-RAPP Cloud`, and the Windows installer stopped parsing. The exhaust —
  a defect that a prose review structurally could not see — became the
  `T-IDENT` gate, which now refuses any space-bearing identifier anywhere in the
  tree.
- A verification endpoint was first written to delete revoked entries. The
  exhaust of arguing it through became
  [[decisions/why-revocation-retains-the-entry]]: a 404 cannot be told apart
  from an outage. The rule is now in the specification and probed end to end.
- Documentation once claimed the browser runtime never sent tokens to a third
  party, while the code fell back to exactly that. The exhaust of catching it
  became a rule that documentation claims are gated where a gate is possible.

Each of those started as something someone noticed in passing. Each is now a
thing that cannot silently regress.

Related: [[concepts/extensions]], [[concepts/kernel-and-distribution]].
