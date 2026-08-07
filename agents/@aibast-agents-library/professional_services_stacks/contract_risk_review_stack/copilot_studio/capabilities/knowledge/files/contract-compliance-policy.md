# Contract Compliance Policy

> SYNTHETIC -- DEMO DATA. These policy standards are fictional and exist so the
> agent has a working world to answer from on day one. In production, replace
> this file with tools that read your real contracting playbook and policy of
> record (see the README's production section).

## Internal policy requirements

| Requirement | Policy Standard |
|-------------|-----------------|
| Liability Cap Minimum | 5000000 |
| Payment Terms Max Days | 45 |
| Ip Preexisting Protection | True |
| Mutual Indemnification | True |
| Cure Period Days | 30 |
| Data Destruction Clause | True |
| Change Order Written | True |
| Sla Penalty Cap Pct | 15 |

These are fixed values. Quote them exactly -- do not round, convert, or
reinterpret them, and do not waive one on request.

## How compliance status is computed

1. A contract's gap list is every clause in its register entry rated `HIGH` or
   `MEDIUM`. There is no third rating, so every recorded clause is a gap.
2. Status is `PASS` when the gap list is empty, otherwise
   `FAIL (N gaps)` where N is the length of the gap list.
3. Each gap reports the clause title, its section number, its severity
   (`HIGH` or `MEDIUM`), and the clause's recorded recommendation as the
   required action.

Current portfolio status:

| Contract | Client | Status | Gaps |
|----------|--------|--------|------|
| CTR-5001 | NovaTech Systems | FAIL | 6 |
| CTR-5002 | Meridian Healthcare | PASS | 0 |
| CTR-5003 | Atlas Financial Group | FAIL | 3 |
| CTR-5004 | Orion Defense Systems | PASS | 0 |

**PASS means "no recorded gaps", not "reviewed and clean."** CTR-5002 and
CTR-5004 have no clause register entry at all, so their gap lists are empty by
default. Always state that caveat alongside their status.

## Risk thresholds

- Elevated risk: `risk_score >= 5.0`. This selects contracts for the exposure
  figure in the risk scan and for the renegotiation brief. CTR-5001 (6.5) and
  CTR-5003 (5.2) qualify; CTR-5004 (4.1) and CTR-5002 (3.8) do not.
- `HIGH` clauses are non-negotiable amendments -- they must resolve.
- `MEDIUM` clauses are preferred amendments -- concede only after every HIGH
  item is resolved.

## Escalation

General Counsel review is the escalation path for any impasse on the liability
cap, any request to waive a policy standard, and any question that turns on
legal interpretation rather than the recorded data. The agent produces
analysis and recommendations; approving, signing, sending, or executing a
contract or amendment is always a person's decision.
