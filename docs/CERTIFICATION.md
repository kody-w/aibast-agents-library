# RAPP Certified

**RAPP Certified** marks a publisher who has shipped an agent to this library
that passed review. It is verifiable by anyone, in real time, from the static
API — no login, no key, no support ticket.

Try it: [the verification page](https://microsoft.github.io/aibast-agents-library/api.html#certified).

## How to earn it

1. Become a publisher — [docs/PUBLISHING.md](PUBLISHING.md). Your GitHub
   username is your handle.
2. Ship at least one agent that passes review: a single self-contained file
   with a valid `__manifest__`, no secrets, configuration through
   `requires_env`, and a description that states the business problem it
   solves. The CI gates run on your pull request.
3. On merge, a maintainer adds you to [`certified.json`](../certified.json)
   in a follow-up pull request. That file is the only hand-edited part of the
   system; everything else is generated.

Two levels:

| Level | Means |
|---|---|
| `certified` | Has published at least one reviewed agent to the library. |
| `maintainer` | Certified, and reviews submissions from other publishers. |

## How anyone verifies it

Every roster entry gets its own endpoint keyed to the GitHub username
(lowercase — GitHub usernames are case-insensitive):

```bash
BASE=https://microsoft.github.io/aibast-agents-library/api/v1

# is this person certified?
curl -s $BASE/certified/<username>.json | jq '{username, certified, level, certified_on}'

# the whole roster
curl -s $BASE/certified.json | jq '.members[] | select(.certified) | .username'
```

```js
const r = await fetch(`${BASE}/certified/${username.toLowerCase()}.json`);
const verified = r.ok && (await r.json()).certified === true;
```

**A username with no roster entry is not certified** — treat a 404 as
"unverified", never as an error to retry.

## Badge

Certified publishers can display a live badge that reads from the API, so it
reflects current status rather than a claim frozen in a README:

```markdown
[![RAPP Certified](https://img.shields.io/endpoint?url=https%3A%2F%2Fmicrosoft.github.io%2Faibast-agents-library%2Fapi%2Fv1%2Fcertified%2F<username>%2Fbadge.json)](https://microsoft.github.io/aibast-agents-library/api.html#certified)
```

The verification page generates this line for you when you look a username up.

## Revocation

Certification can be withdrawn — for a security problem in a published agent,
a licensing violation, or a maintainer's request. Revocation sets
`status: "revoked"` on the roster entry; the entry is **never deleted**.

That matters: the endpoint keeps resolving and answers `certified: false`, so
a badge already embedded in someone's README flips to *not certified* within a
build. If entries were deleted instead, the URL would 404 — indistinguishable
from an outage, which is exactly the ambiguity a verification system must not
have.

## What certification does not mean

It says a submission met this library's review bar. It is **not** a Microsoft
endorsement of the publisher, their employer, or their other work, and it
carries no warranty — see [DISCLAIMER.md](../DISCLAIMER.md). Agents remain
community content that you should read before you run.
