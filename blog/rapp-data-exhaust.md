---
title: RAPP data exhaust — reading the negative of the shape
date: 2026-08-05
author: AIBAST
tags: [method, lexicon, field-notes]
summary: The by-product of building something holds a cast of the thing that made it. Here is the term we use for that, why it is perishable, and three defects it caught in this repository.
---

# RAPP data exhaust

We keep needing a word for something, so we are going to name it and see if it
travels: **RAPP data exhaust**.

Data exhaust is the by-product of doing the work. Not the code and not the
documents — the *shape of how the work actually went*. Which correction had to
be given twice. Which review found a real defect and which found noise. Which
rename broke an installer. Which question a newcomer asks first, and which one
they never think to ask.

Most teams treat that as waste. It is the most information-dense thing they
produce.

## Exhaust is a negative

The useful idea is not that exhaust is *more data*. It is that exhaust is a
**negative of the shape that emitted it**.

You usually cannot observe the thing you most need to model. Actual intent. The
real constraint. The boundary between *fine* and *absolutely not*. The failure
mode that already happened here once. Nobody writes those down completely,
because to the person holding them they are obvious — and obvious things do not
get written down.

But every one of those shapes presses an impression into what it produces:

- a **correction** is a cast of the boundary that was crossed
- a **gate** is a cast of a defect that got through once
- a **rejected approach** is a cast of a constraint nobody stated
- a **repeated instruction** is a cast of something the system keeps failing to
  infer

So you do not need the positive to be described. Read the negative and the
positive is recoverable — at *higher* fidelity than a description would have
had, because a description is what someone remembered to say, and a negative is
what actually happened.

That is the whole method. An agent facing a problem model it cannot see directly
can still work with precision, because the exhaust around the problem already
carries its shape.

## Use it or lose it

The richest exhaust is perishable.

A session transcript is discarded. A rationale evaporates the moment a pull
request merges. The reason a gate exists is obvious for a week and mysterious a
year later — at which point somebody deletes it as flaky and reintroduces the
defect it was catching.

Exhaust that is not captured while it is warm is not expensive to recover. It is
**not recoverable**, because the impression was in a medium that no longer
exists. That is why we treat capture as part of the work rather than as
documentation debt.

## Three defects the exhaust caught here

None of these were found by planning. All three were found by paying attention
to the by-product.

**A rename broke the Windows installer, invisibly.** We renamed a component and
ran a text substitution across the tree. It also rewrote a PowerShell function
name into `Install-RAPP Cloud` — a space in a function name is a parse error, so
the advertised one-liner died before printing its first line. No prose review
could see it; it reads perfectly. The exhaust — *a defect class that survives
human reading* — became a gate that now refuses any space-bearing identifier
anywhere in the repository.

**A verification endpoint was about to lie by omission.** The first
implementation of badge revocation deleted the record, so the endpoint returned
404. Arguing it through produced the actual rule: **a 404 cannot be told apart
from an outage**. A verification system whose *no* is indistinguishable from its
*unreachable* verifies nothing, because every consumer has to guess and
consumers guess generously. Revoked entries are now retained and answer
`certified: false`. That argument is now a written decision, so it will not be
had again.

**Our documentation claimed something the code did not do.** A page stated that
the browser runtime never sends your token to a third party. The code fell back
to exactly that when the direct call failed. The exhaust of catching it became a
standing rule: *documentation claims are gated wherever a gate is possible*. A
document asserting something the repository does not do is now a failing test,
not a style problem.

Each started as something noticed in passing. Each is now a thing that cannot
silently regress. That conversion — noticed-in-passing to cannot-regress — is
what we mean by using the exhaust.

## What we actually do with it

Four rules, and they are in our constitution rather than in someone's head:

1. **A lesson becomes an artifact.** A gate, a decision note, or a
   constitutional rule — never a remembered preference, which is just exhaust
   that will evaporate a second time.
2. **Prefer the gate to the reminder.** If a lesson can be machine-checked,
   checking it *is* the way to remember it. Care does not survive a busy week;
   a failing test does.
3. **Record the why, not only the what.** A decision note states what was
   rejected and why. The rejected branch is the part that stops a question being
   reopened, and it is exactly the part a diff cannot carry.
4. **The boundary is absolute.** Exhaust is mined for shape and lesson. Raw
   transcripts, customer content, and personal data never become public
   artifacts — only the generalized lesson does. When in doubt the lesson ships
   and the source does not.

## Why we are publishing the term

ms-rapp is spreading through enterprises the way tools actually spread: one team
at a time, mostly by someone showing someone else. Shared vocabulary is what
makes that transmissible. If "we should capture the exhaust from that review"
lands in a hallway conversation without further explanation, the idea has
travelled — and the practice usually follows the word.

So take it. Argue with it. If your version is better, we would like the
exhaust from that too.

---

*Field Notes from the Frontier is where we write down how ms-rapp is actually
built. The full definition of this term lives in our documentation vault under
`concepts/rapp-data-exhaust`, and the practice is Article XV of the repository
constitution.*
