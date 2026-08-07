# Call Transcript Corpus

> SYNTHETIC — DEMO DATA. Every call, participant, company, and dollar figure in
> this document is fictional. This file exists so the agent has a working world
> to answer from on day one. In production, replace this file with tools that
> read your real speech-to-text engine and call recording store (see the
> README's production section).

## Calls

| ID | Date | Duration | Participants | Transcription Confidence |
|----|------|----------|--------------|--------------------------|
| CALL-T001 | 2025-11-14 | 1847 sec (30m 47s) | Alex Rivera (Sales), Jennifer Walsh (TechVantage Solutions) | 0.96 (96%) |

## CALL-T001 transcript

| Timestamp | Speaker | Text |
|-----------|---------|------|
| 00:00:15 | Alex Rivera | Hi Jennifer, thanks for making time today. I wanted to follow up on our demo last Tuesday. |
| 00:00:28 | Jennifer Walsh | Hi Alex, yes absolutely. We really liked what we saw, especially the analytics dashboard. Our team has been struggling with reporting. |
| 00:00:45 | Alex Rivera | That's great to hear. Can you tell me more about the reporting challenges? How many people are affected? |
| 00:01:02 | Jennifer Walsh | About 150 people across our operations and finance teams. We spend roughly 20 hours a week manually compiling reports from three different systems. |
| 00:01:25 | Alex Rivera | That's significant. At your team's average cost, that's roughly $50,000 a year in labor just on reporting. Our platform could automate about 80% of that. |
| 00:01:48 | Jennifer Walsh | That ROI is compelling. We have budget approval for up to $200,000 for this initiative. Our CEO, Mark Davidson, wants to see a formal proposal by December 15th. |
| 00:02:15 | Alex Rivera | Perfect. I'll have a proposal ready by December 10th. Should we schedule a review meeting with your team for December 12th? |
| 00:02:30 | Jennifer Walsh | That works. Include our IT Director, Sam Patel, in that meeting. He'll need to evaluate the technical integration with our SAP system. |

## Entity type definitions

| Type | Pattern | Examples |
|------|---------|----------|
| person | Named individuals mentioned | Jennifer Walsh, Mark Davidson, Sam Patel |
| organization | Company or department names | TechVantage Solutions, Operations, Finance |
| money | Dollar amounts or budget references | $200,000, $50,000 |
| date | Dates and deadlines | December 15th, December 10th, December 12th |
| product | Product or feature mentions | analytics dashboard, reporting, platform |
| pain_point | Challenges or problems described | manually compiling reports, three different systems, 20 hours a week |
| action_item | Commitments or next steps | formal proposal, review meeting, evaluate technical integration |
| competitor | Competitor or alternative mentions | SAP |
