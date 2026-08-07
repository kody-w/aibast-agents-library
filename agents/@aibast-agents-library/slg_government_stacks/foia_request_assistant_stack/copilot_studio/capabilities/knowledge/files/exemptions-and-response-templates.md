# Exemption Catalog and Response Templates

> SYNTHETIC — DEMO DATA. The exemption catalog, keyword mapping, and template
> language in this document are a fictional demonstration set, not legal advice
> and not your agency's adopted disclosure policy. This file exists so the agent
> has a working world to answer from on day one. In production, replace this
> file with tools that read your adopted exemption schedule and approved
> response letter templates (see the README's production section).

## Exemption categories

| Code | Category | Description | Statute |
|---|---|---|---|
| EX-1 | Personnel Privacy | Personal information of employees (SSN, home address, medical) | Gov. Code 6254(c) |
| EX-2 | Law Enforcement | Records of investigations, intelligence, or security procedures | Gov. Code 6254(f) |
| EX-3 | Attorney-Client Privilege | Communications between agency and legal counsel | Gov. Code 6254(k) |
| EX-4 | Deliberative Process | Preliminary drafts, notes, and internal deliberations | Gov. Code 6255(a) |
| EX-5 | Trade Secrets | Proprietary business information submitted by third parties | Gov. Code 6254(k) |
| EX-6 | Critical Infrastructure | Security plans, vulnerability assessments | Gov. Code 6254(aa) |

## Exemption mapping rule

Applicable exemptions are derived deterministically from the request's subject
and scope text, lowercased, evaluated in this order:

| Order | Condition | Exemptions added |
|---|---|---|
| 1 | `police` or `officer` appears in the subject | EX-1, EX-2 |
| 2 | `correspondence` or `memo` appears in the scope | EX-3, EX-4 |
| 3 | `development` appears in the subject, or `developer` appears in the scope | EX-5 |
| 4 | Nothing above matched | EX-1 (default) |

More than one condition can fire, so a request can carry three exemption codes.
EX-6 is in the catalog but no keyword rule produces it for the current caseload.

### Applicable exemptions per request

| Request ID | Matched conditions | Applicable exemptions |
|---|---|---|
| FOIA-2025-0301 | `police` in subject | EX-1, EX-2 |
| FOIA-2025-0302 | `correspondence` in scope; `development` in subject | EX-3, EX-4, EX-5 |
| FOIA-2025-0303 | none matched | EX-1 (default) |
| FOIA-2025-0304 | `memo` in scope | EX-3, EX-4 |

These are candidates for review, not withholding decisions. A records officer
decides what is withheld.

## Response templates

| Template | Language |
|---|---|
| Full Grant | All responsive documents are provided herein. No exemptions have been applied. |
| Partial Grant | Responsive documents are provided with redactions applied pursuant to the exemptions noted below. |
| Denial | After thorough review, the requested records are exempt from disclosure under the exemptions cited below. |
| No Records | A diligent search has been conducted and no records responsive to your request were located. |
| Fee Notice | The estimated cost for processing this request is {fee}. Please remit payment to proceed. |

The Fee Notice `{fee}` placeholder is filled with the specific request's own
fee estimate — for example, $6.75 for FOIA-2025-0303.

## Redaction best practices

| Practice |
|---|
| Apply exemptions narrowly — redact only information covered by statute |
| Log each redaction with exemption code and page reference |
| Use Vaughn index format for withheld documents |
| Review redactions for consistency across document set |
| Verify no metadata leakage in redacted PDFs |

## Response checklist

| # | Step |
|---|---|
| 1 | Responsive documents identified and compiled |
| 2 | Exemption review completed |
| 3 | Redactions applied and logged |
| 4 | Vaughn index prepared (if applicable) |
| 5 | Fee calculation finalized |
| 6 | Response letter drafted |
| 7 | Supervisory review completed |
| 8 | Response mailed/emailed to requester |
