# RAPP in the real world — five strangers, one verdict

> 2026-07-14. Five cold personas (never heard of RAPP) were dropped onto the LIVE public
> surfaces and asked to solve a real problem from their actual life. None were told what
> to think. This is what they found. It exists so the estate stops being "a hollow house
> of specs" and starts being a set of products someone outside this repo would use.

## The one-sentence finding

**Every persona found the exact same real product — an answer machine that cites its
source and refuses to guess — and every persona bounced off the exact same wall: the
organism cosmology and the GitHub/Copilot/public-repo on-ramp.** The mechanism is a
product. The costume is the thing killing it. As the OSS maintainer put it: *"a brilliant
idea wearing a costume that scares off exactly the maintainers who need it."*

The real product, in their words, not ours:
- Marcus (HVAC): *"an answer machine that shows the invoice it got the answer from and
  shuts up when it doesn't know."*
- Elena (departing engineer): *"The honesty rule — receipts or refusal — is the real
  product. Ship it in a suit."*
- Sarah (caregiver): *"my kids could type 'tell me about Grandma's diner' into a box
  like that."*

**Receipts-or-refusal is the whole company.** Herald's honesty law — every claim resolves
to a frame, "My biography doesn't record that" when silent — is what all five wanted and
none had. Everything else (frames, membrane, races, the Lexicon) is scaffolding that
makes that one behavior trustworthy.

## The five worked use-cases (each a real market)

| Persona | Real problem | The RAPP piece that fits | Would pay |
|---|---|---|---|
| **Sarah, 52** — caregiver | Capture her mother's stories + voice as a 30-year, no-subscription heirloom | Herald-style door over a life record; the "AI you keep" thesis | **$300–500 once** (like photo restoration); never monthly |
| **Marcus, 41** — HVAC owner | 15 yrs of customer history trapped in techs' heads; new tech productive day one | Askable history with receipts, owned not rented | **$2–3k flat + ~$500/yr** support |
| **Priya, 38** — med-device compliance | Prove records weren't edited after the fact; explainable exceptions | Hash-chained records + the **waiver ledger = her deviation/CAPA register**; Art LIII = CAPA effectiveness | **$10–20k/yr** (replaces a Veeva line item) |
| **Dev, 34** — OSS maintainer | Succession: settled decisions get relitigated forever | FABLE-HANDOFF (ADRs **with rejected alternatives**) + drift-lint as "we settled this" CI; the door deflects issue #401 | Adopts patterns free; **"de-cosmologized, that's a 5k-star repo"** |
| **Elena, 45** — departing principal eng | Tribal knowledge leaves with her in 4 weeks | Door with receipts+refusal as an "askable exit interview"; local/owned survives tool churn | **$10–20k per departing senior** |

## The walls, verbatim (fix these or nothing ships)

1. **Vocabulary on the first screen.** "I run an HVAC company; I don't plant organisms"
   (Marcus). "Organism? I'm here for my mother" (Sarah). Priya couldn't cite Article LIII
   in a procedure because it opens *"at the close of the OPUS's sixth movement… chosen by
   the body's own first race."* The two-vocabulary Lexicon already exists — **the human
   register is simply not deployed on the public pages.**
2. **The on-ramp assumes a developer.** GitHub account + Copilot subscription + a public
   repo as the default trust anchor. Marcus's techs will never have GitHub accounts.
   Elena's company is *legally excluded* by the PolyForm Small Business license and can't
   put warts in a public repo. Sarah needs Option B (paste-a-prompt) first and audio she
   never found.
3. **The magic isn't free-standing.** Herald's freeform answers need a local brainstem on
   `/chat`; the public page is deterministic-only. Dev and Elena both caught this.
4. **"Approved by an AI" is a hard stop for regulated buyers.** Priya's auditor halts at
   `approved_by: Fable 5 adjudication`. Exceptions need a qualified *person* and a
   signature (`sig: null` today). This is also just correct governance.

## The shortest path to "real" (the backlog the strangers wrote)

- **One flagship worked example that is NOT about software.** Every persona asked for it
  independently. Build ONE: *Smith Plumbing — 900 customers, ask "what did we quote at 45
  Oak St" and get the answer with the invoice attached.* That single page converts Marcus,
  and its shape (record → door → receipts) is identical for Sarah's grandmother and
  Elena's exit interview. **This is the highest-leverage next build.**
- **Deploy the human vocabulary** on onboarding + a person/business-shaped door demo.
- **A "receipts-or-refusal" doorman as a standalone**: answers from `records/*.md` (or a
  CSV/invoice import) with any LLM key, no frame-chain, no organism vocabulary. Dev,
  Marcus, and Elena all asked for exactly this one-file thing.
- **Identity binding + human sign-off + RFC-3161 timestamps** for the compliance SKU;
  a compliance-vocabulary mapping (frame→record, waiver→deviation, sweep→effectiveness).
- **A private/on-prem posture + a commercial license + a boring name** — the enterprise
  procurement unlock (Elena, Priya).
- **Import + phone-entry** for the SMB SKU (QuickBooks/texts in; 30-second job note from a
  truck).

## What this validates about the week's work (not hollow)

- The **tamper-evidence is real to a skeptic**: Priya independently recomputed a live
  frame's sha256 and matched — no vendor trust required.
- The **honesty law is the product**, confirmed by five people who wanted it before they
  understood anything else.
- The **judgment-transfer artifacts** (FABLE-HANDOFF, drift-lint, waiver ledger) are the
  pieces professionals said they'd adopt *this week* — succession, compliance, and OSS
  governance are three markets, not one art project.

The specs weren't hollow — they were **unwrapped**. Same mechanisms, five suits.
