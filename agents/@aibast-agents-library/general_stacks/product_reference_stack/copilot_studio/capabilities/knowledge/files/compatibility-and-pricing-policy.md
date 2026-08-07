# Compatibility and Pricing Policy

> SYNTHETIC — DEMO DATA. The dependency matrix, bundle math, and discount
> language below are fictional and exist so the agent has a working rule set on
> day one. In production, replace this file with tools that read your real
> product dependency service and pricing engine (see the README's production
> section).

## Compatibility matrix

| Product | Requires | Recommended | Incompatible |
|---------|----------|-------------|--------------|
| Core Platform (CORE) | - | ANLYT-STD, INTGR | - |
| Enterprise Platform (ENT) | - | ANLYT-PRO, INTGR, SECUR | - |
| Analytics Standard (ANLYT-STD) | CORE | INTGR | ANLYT-PRO |
| Analytics Pro (ANLYT-PRO) | ENT | INTGR, SECUR | ANLYT-STD |
| Integration Hub (INTGR) | CORE | SECUR | - |
| Security Suite (SECUR) | ENT | INTGR | - |

Rules that follow from the matrix:

- `Requires` is a hard gate. A bundle containing ANLYT-STD or INTGR is invalid
  without CORE. A bundle containing ANLYT-PRO or SECUR is invalid without ENT.
- `Incompatible` is symmetric. ANLYT-STD and ANLYT-PRO are the only
  incompatible pair in the catalog and are never quoted together.
- `Recommended` is advisory. It never becomes a requirement and is never added
  to a total unless the user asks for it.
- Core Platform and Enterprise Platform are both standalone. Nothing in the
  matrix blocks holding both.

## Bundle pricing math

For each product in a bundle, on annual billing:

- Per-seat product: `annual_per_user x users x 12`.
- Flat-rate product: add `annual_flat` once — it is already a yearly figure.

On monthly billing:

- Per-seat product: `monthly_per_user x users x 12`.
- Flat-rate product: `monthly_flat x 12`.

Both terms are annualized over 12 months, so the difference between them is
exactly the published annual saving.

### Worked reference bundle — Enterprise full suite (ENT + ANLYT-PRO + INTGR + SECUR)

| Component | 100 users | 500 users |
|-----------|-----------|-----------|
| Enterprise Platform (ENT) | 65 x 100 x 12 = $78,000 | 65 x 500 x 12 = $390,000 |
| Analytics Pro (ANLYT-PRO) | 40 x 100 x 12 = $48,000 | 40 x 500 x 12 = $240,000 |
| Integration Hub (INTGR) | $15,000 flat | $15,000 flat |
| Security Suite (SECUR) | $12,500 flat | $12,500 flat |
| **Total, annual billing** | **$153,500/year** | **$657,500/year** |

This bundle is valid under the matrix: ANLYT-PRO and SECUR both require ENT,
which is present, and it contains no incompatible pair.

## Discount policy

| Program | Published terms |
|---------|-----------------|
| Annual billing | 17-21% saving versus monthly, set per product in the rate card |
| Multi-year commitment | Additional 10-20% discount |
| Volume | Available for 50+ users — no published percentage |
| Non-profit and education | Available — no published rate |

Anything outside these published terms is not a price. Volume, non-profit, and
education pricing is quoted by sales; the agent states that it is available and
stops there.

## Boundaries

- List pricing only. The agent never issues a quote, applies a custom
  discount, creates an order, changes entitlements, or sends anything to a
  customer.
- The catalog is closed at six products. A product, feature, connector, or
  limit that is not in this file does not exist — say so rather than
  substituting the nearest match.
