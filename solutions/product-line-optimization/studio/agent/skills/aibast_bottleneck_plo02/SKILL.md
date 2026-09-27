---
name: constraining-station-identification
description: Routes the Production Engineer prompt "Where is the bottleneck on each line, and which station should the plant team address first?" using cycle-versus-takt and defect evidence.
---
<!-- bic:source=blank -->
# Constraining station identification

Read listed entity facts with the SharePoint list tools, using the global instructions' Evidence locations and List columns. Read all unlisted record facts, calculations, policies, thresholds and response contracts from the retained knowledge files. Never claim an omitted email field or an unlisted record set is available from a list.

Use this skill for constraint questions such as "Where is the bottleneck on
each line, and which station should the plant team address first?", "what is
slowing each line," or "which station is over takt." Evaluate all three lines.

## Inputs (from the packaged synthetic records)

For each line read the per-station table: station name/ID, cycle time, takt
time, delta (cycle − takt), and defect rate; plus the defect category mix.

## Procedure

1. For each line, the constraining station is the one with the longest cycle
   time. Fixed results:
   - Electronics Assembly Line A → **Functional Test (A5)**, 25.3s vs 20.0s
     takt, +5.3s over takt (26.5%), defect 0.04%.
   - Metal Fabrication Line B → **Robotic Welding (B3)**, 14.2s vs 12.0s takt,
     +2.2s over takt (18.3%), defect 0.30%.
   - Polymer Molding Line C → **Injection Molding (C2)**, 18.4s vs 15.0s takt,
     +3.4s over takt (22.7%), defect 0.45%.
2. Present each line's full station table with the delta column and the
   bottleneck flagged, so the evidence supports the pick.
3. Add the top defect categories per line as supporting evidence
   (e.g., LINE-C: short_shot 35%, flash 25%, sink_mark 20%).
4. Recommend which station to address first across the plant: Functional
   Test (A5) first because its 26.5% over-takt margin is the largest, then
   Injection Molding (C2), then Robotic Welding (B3).

## Output

Per-line: the named constraining station with cycle/takt/over-takt and defect
rate, then the supporting station table and defect mix. Close with the
cross-plant "address first" recommendation.

## Grounding and safety

- Use only the packaged station figures; never invent stations or numbers.
- Recommend only; never reconfigure or stop a station.
- Never say you lack access and never ask the user to name a line.
- End with:
  `> Synthetic pilot data; figures are planning estimates, not a live ERP, IoT, or Power BI reading.`

## Fallback

If the user asks about a station or line not in the records, say it is not in
the pilot and list the known stations for the relevant line.

Apply the following phrase requirements only to the matching request below; do not include evidence from unrelated cases.

## Required evidence

Include each phrase below in the answer exactly as written (same words, same order):

For: Where is the bottleneck on each line, and which station should the plant team address first?

- Functional Test
- Robotic Welding
- Injection Molding

Report only figures and conclusions found in the list records, the rules knowledge or this operation's canonical output, or simple arithmetic on those figures that you label as computed. Beyond what the canonical output itself states, do not say or imply that one amount covers, closes, exceeds, offsets or is sufficient for another, and do not rank or recommend options; those judgements belong to the authorized reviewer.
