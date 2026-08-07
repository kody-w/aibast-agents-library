# Clinical Criteria by CPT Code

> SYNTHETIC — DEMO DATA. These payer rule sets are fictional and are not any
> real payer's medical policy. This file exists so the agent's criteria checks
> are grounded in a citable document on day one. In production, replace this
> file with tools that read your payers' current medical policy and utilization
> management rules (see the README's production section).

## How a payer rule set is resolved

Each CPT record holds rule sets keyed `BCBS`, `Aetna`, and `Medicare`. For a
given authorization, the keys are tested in that order and the first key whose
text appears inside the request's recorded payer name wins.

| Recorded payer on the request | Key that resolves |
|-------------------------------|-------------------|
| Aetna | Aetna |
| Medicare Part B | Medicare |
| Blue Cross Blue Shield of Illinois | none - the literal string `BCBS` does not appear in the payer name |

When no key resolves, there is no rule set for that request: the requirement
list is empty and the auto-approve flag reads `No`. That is the honest answer.
The rules of a non-matching key are never substituted.

## CPT 73721 - Knee MRI

Historical approval rate 92%. Average turnaround 1.5 days.

| Payer Key | Auto-Approve | Requirements |
|-----------|--------------|--------------|
| BCBS | Yes | Physical exam documented; X-ray completed; Conservative therapy >= 4 weeks |
| Aetna | No | Physical exam documented; X-ray completed; Conservative therapy >= 6 weeks; Specialist referral |
| Medicare | Yes | Physical exam documented; Imaging appropriate per LCD |

## CPT 78452 - Nuclear Cardiac Stress Test

Historical approval rate 78%. Average turnaround 3.2 days.

| Payer Key | Auto-Approve | Requirements |
|-----------|--------------|--------------|
| BCBS | No | Cardiac risk factors documented; EKG performed; Symptoms documented |
| Aetna | No | Cardiac risk factors documented; EKG performed; Peer-to-peer if age < 55 |
| Medicare | Yes | Symptoms documented; EKG performed |

## CPT 27130 - Total Hip Arthroplasty

Historical approval rate 85%. Average turnaround 5.0 days.

| Payer Key | Auto-Approve | Requirements |
|-----------|--------------|--------------|
| BCBS | No | Failed conservative therapy >= 3 months; Imaging confirming severe OA; Functional impairment documented |
| Aetna | No | Failed conservative therapy >= 3 months; Imaging; Functional assessment; BMI < 40 |
| Medicare | Yes | LCD criteria met; Pre-op clearance; Imaging |

## CPT 72149 - Lumbar MRI with Contrast

Historical approval rate 74%. Average turnaround 2.0 days.

| Payer Key | Auto-Approve | Requirements |
|-----------|--------------|--------------|
| BCBS | Yes | Conservative therapy >= 4 weeks; Red flags absent; Physical exam documented |
| Aetna | No | Conservative therapy >= 6 weeks; Physical therapy documented; Red flags absent |
| Medicare | Yes | Symptoms documented; Exam documented |

## Reading the flags

- **Auto-Approve** is the payer's configuration for that CPT, not the outcome
  of any request. `Yes` does not mean this authorization is approved; `No` does
  not mean it will be denied.
- **Requirements** are what the payer demands be documented. Whether a given
  patient's record satisfies them is a clinical reviewer's judgment, never the
  agent's. Thresholds are reproduced exactly as written.
- **Approval rate and turnaround** belong to the CPT code and are reported even
  when no payer rule set resolves for the request.
