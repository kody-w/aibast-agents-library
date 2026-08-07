# Deployment Targets and Pricing

> SYNTHETIC — DEMO DATA. Every requirement, price, and SLA in this document is
> fictional. This file exists so the agent has a working world to answer from
> on day one. In production, replace this file with tools that read your real
> infrastructure requirements and cloud cost calculator (see the README's
> production section).

## Deployment target requirements

| Target | Min RAM (GB) | Min Cores | GPU VRAM (GB) | Max Model Size (MB) | Max Latency (ms) | Max Cold Start (ms) | Cost / 1K Inferences |
|--------|--------------|-----------|---------------|---------------------|------------------|---------------------|----------------------|
| cpu_inference | 4 | 2 | — | — | 200 | — | $0.020 |
| gpu_inference | 8 | — | 8 | — | 50 | — | $0.150 |
| edge_deployment | 2 | — | — | 200 | 30 | — | $0.005 |
| serverless | — | — | — | 500 | — | 3000 | $0.050 |

A dash means the target does not define that requirement.

## Which requirements are actually checked

Readiness evaluates two checks only, and only when the target defines the
matching limit:

| Target | Model Size check | Latency check | Total checks |
|--------|------------------|---------------|--------------|
| cpu_inference | not defined | latency_ms vs 200 ms max | 1 |
| gpu_inference | not defined | latency_ms vs 50 ms max | 1 |
| edge_deployment | size_mb vs 200 MB max | latency_ms vs 30 ms max | 2 |
| serverless | size_mb vs 500 MB max | not defined | 1 |

Min RAM, min cores, GPU VRAM, and max cold start are recorded but not
evaluated. A model is Ready for a target only when it passes every check that
target defines.

## Pricing tiers

| Tier | Monthly Cost | Inference Limit | Support | SLA |
|------|--------------|-----------------|---------|-----|
| Development | $0/mo | 10,000 | Community | None |
| Standard | $499/mo | 500,000 | Email (48h) | 99.5% |
| Professional | $1,999/mo | 5,000,000 | Priority (4h) | 99.9% |
| Enterprise | $7,999/mo | Unlimited | Dedicated (1h) | 99.99% |

## Monthly infrastructure cost at 100K inferences

`monthly = cost_per_1k_inferences * 100`

| Target | Cost / 1K | Monthly at 100K |
|--------|-----------|-----------------|
| cpu_inference | $0.020 | $2.00 |
| gpu_inference | $0.150 | $15.00 |
| edge_deployment | $0.005 | $0.50 |
| serverless | $0.050 | $5.00 |

Tier subscription and infrastructure cost are separate line items and are not
summed into a single total.
