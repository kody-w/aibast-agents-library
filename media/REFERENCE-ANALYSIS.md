# What the professional recordings actually do

Extracted from `#1-Product Line Optimization Agent.mp4` by transcription and
measurement, not by watching and guessing. This is the design truth a generated
film has to hit; every number here was measured.

## Timing

| | Measured |
|---|---|
| Duration | 135.5s |
| Picture | 1920×1080, 30fps, H.264 ~6.2 Mbps |
| Audio | AAC 192k, 48kHz stereo |
| Loudness | **−18.62 LUFS**, true peak −3.23 dBTP |
| Narration | 254 words, **9.4s → 130.1s** |
| Speech rate | **2.1 words/sec** — measured, including pauses |
| Silence | 8.1s total (94% narrated) |
| Narration beats | 3 (pauses > 0.55s at 33.5s and 119.5s) |

**The first 9.4 seconds are silent.** Title card and the opening of the b-roll
carry no voice. I had narration starting at 5.6s.

## The script is a customer narrative, not a description

This is where my generated script was wrong in *register*, not just length. The
reference never talks about how it was made. It tells a before/after story with
escalating asks and closes on business results.

Its shape, with the slots each entry fills:

1. **Premise** — "There's an agent to guide *{industry}* through these processes."
2. **Capability** — "It pulls data from *{sources}*, engages you directly in
   *{surface}*, and delivers *{primary action}*."
3. **Scenario** — "Let's say a *{persona}* needs to *{task}*."
4. **Before** — "Before, they would have needed to jump across multiple systems
   to manually gather insights."
5. **After** — "Now, in an instant, an agent can deliver *{output}*, as well as
   automatically highlight *{finding}*."
6. **Escalation** — "But what if the *{persona}* wants to go a step further and
   understand how to *{next step}*?"
7. **Depth** — "The agent handles *{capability}* and offers targeted
   recommendations right in his workflow, like *{examples}*."
8. **Unification** — "…used to require cross-referencing different systems. Now,
   with unified data context in their *{systems}*, the agent can rapidly
   generate *{artifact}*."
9. **Risk** — "For risk mitigation, the agent helps as well by outlining a
   strategy that keeps the project on track."
10. **On demand** — "When the manager needs *{detail}*, he simply asks, and the
    agent quickly compiles *{summary}*."
11. **Sustain** — "Finally, the agent creates a real-time monitoring plan…"
12. **Summary** — "With a *{agent name}*, *{industry}* get guided assistance
    embedded directly into their workflows."
13. **Results** — "The result? *{value 1}*, *{value 2}*, and better *{value 3}*."
14. **Close** — "Get started on your agentic journey today. Talk to your
    Microsoft representative to learn more." (fixed, verbatim)

Beat 2 runs 34.1s → 119.5s as one continuous 205-word block over the whole
walkthrough. It is not chopped per screen state; the picture follows the
narration, not the other way round.

## The walkthrough screen

Measured from the frame at 0:55, which is the frame a viewer studies longest:

- An opening sentence stating what the agent will do and what it is reading.
- **Two labelled sections** of 3–4 short bullets each ("Current Performance:",
  "Holiday Requirement:").
- **A highlighted callout** carrying the headline finding, a `Source:` line
  naming the systems, and a closing question.
- An `Agent Calls: <tool>` line.
- The whole answer is on screen and then **held** while narration continues.

## Plate

- The laptop sits with its keyboard visible; the screen is not cropped to the
  frame edge.
- Screen interior: **1654×973 at x=128, y=51** of the 1920×1080 frame, measured
  by bright-region detection. Edge width varies 6px top to bottom, so a straight
  composite holds without a perspective warp.

## Open gaps in the generated films

Recorded honestly, because they are the reason the current cut is not
releasable:

1. **Script register is wrong.** Generated narration describes the pipeline
   ("everything you have seen was generated from the agent's own manifest").
   It must instead follow the 14-beat customer narrative above.
2. **Speech rate.** Budgets assumed 3.49 w/s; the reference is 2.1 w/s with
   deliberate pauses. Generated VO is rushed by comparison.
3. **Narration entry.** Must start at ~9.4s, not 5.6s.
4. **Walkthrough pacing.** Even-splitting four turns across 78s left the screen
   empty until 61.5s. The answer must land by ~53s and hold.
5. **Product jewels.** The reference shows real product glyphs (Dynamics 365,
   Teams, SharePoint, Power BI) under the overview panels; generated films have
   none.
6. **B-roll.** Duration must fill the act in one continuous take with no loop
   or restart.
7. **Overview card.** Panels occupy the top 45% of frame, leaving dead space;
   the reference fills it.

## How to build it

Through HyperFrames (`videos/rappvision-film/`), not the ad-hoc
Playwright-plus-ffmpeg path: the narration beats above are the timeline, the
composition declares the acts, and `hyperframes check` gates the result.
