# AIBAST Public Badge Program Rules

> **Status: planned, not operational.**
>
> The program launches only when `.github/workflows/badge-profile.yml` and
> `docs/badges/` are introduced together and pass the governance gate.

## Purpose

The badge program gives participants a public, GitHub-linked record of approved
course progress for learning and professional bragging rights. It does not grant
employment status, certification by Microsoft, tenant authorization, SharePoint
access, or guaranteed leaderboard placement.

## Canonical account-linkage proof

The first submission gate is a public fork of
<https://github.com/microsoft/aibast-agents-library>. The fork relationship and
fork owner publicly link the submission to that GitHub account.

The fork is consent to enter badge submission and eligibility review. It is not
consent to publish course results. Publication requires the later completion
payload preview and explicit confirmation.

## Completion gate

1. The participant submits achievement evidence at the end of the course.
2. The participant completes a three-question, open-book knowledge check.
   Revisiting course material and retrying are allowed because the goal is
   learning and demonstrated comprehension.
3. The course UI evaluates the check without publishing raw answers.
4. The UI shows the exact public completion payload, including the course,
   GitHub account, approved evidence summary, agreement status, and pass result.
5. The participant explicitly confirms that public payload.
6. The background API validates the schema and prohibited-data rules, then
   creates or updates the public completion issue.
7. The issue-triggered workflow validates the fork, evidence, agreement, and
   pass result before recording completion.

## Public record and attribution

The accepted completion issue and workflow result are authoritative. The static
profile under `docs/badges/` is a generated view. It may show:

- the public GitHub account;
- approved courses and progress;
- approved public badges;
- publisher/program attribution;
- the completion issue or proof reference.

It must not show raw quiz answers, credentials, tenant IDs, customer data,
private evidence, private agreement content, or unnecessary personal data.

## Updates and reconciliation

The planned `.github/workflows/badge-profile.yml` contract includes:

- an issue-triggered path for the participant-specific real-time update;
- a nightly scheduled full reconciliation;
- manual `workflow_dispatch` recovery;
- explicit least-privilege permissions;
- concurrency control for competing writers;
- idempotent regeneration from authoritative records.

The nightly true-up repairs missed or failed individual updates and keeps every
published profile whole and current.

## Review and moderation

The fork and completion submission are proposals, not guarantees. Maintainers
may approve, reject, correct, suspend, deprecate, or remove a badge or
leaderboard entry under these rules. Inclusion and retention are not rights
created by the fork.

## SharePoint and tenant access

Badge automation may produce an approved roster. It never grants SharePoint or
tenant access. Maintainers add approved participants to the SharePoint library
manually.

## Appeals and corrections

Use the structured public issue forms or GitHub Discussions for non-sensitive
questions and corrections. Security vulnerabilities and private evidence follow
`SECURITY.md` and must not be posted publicly.
