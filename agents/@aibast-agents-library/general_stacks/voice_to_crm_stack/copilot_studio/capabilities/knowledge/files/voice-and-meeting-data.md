# Voice Capture, D365, and Meeting Data

> SYNTHETIC - DEMO DATA. Every recording, contact, opportunity, meeting, and
> email address in this document is fictional. This file exists so the agent has
> a working world to answer from on day one. In production, replace this file
> with tools that read your real speech-to-text pipeline, your Dynamics 365
> organization, and your calendar and mail systems (see the README's production
> section).

## Voice recordings

| ID | Date | Speaker | Duration | Confidence |
|----|------|---------|----------|------------|
| VOC-001 | 2025-11-14 | Alex Rivera | 245s | 94% |
| VOC-002 | 2025-11-14 | Sarah Kim | 180s | 96% |

### VOC-001 transcript

"Just finished a call with Jennifer Walsh at TechVantage Solutions. She
confirmed they have budget approval for two hundred thousand dollars. The CEO
Mark Davidson wants our proposal by December fifteenth. We need to include Sam
Patel their IT director in the next meeting. Set the opportunity stage to
proposal and schedule a review meeting for December twelfth."

### VOC-002 transcript

"Quick update on the Greenridge Partners deal. David Park confirmed they want to
renew for another year. Amount stays at seventy two thousand. They also want to
add analytics standard for an additional twelve thousand per year. Update the
opportunity to negotiation stage with a close date of January tenth."

## D365 entity mapping rules

Voice patterns are alternations - `a|b|c` means any of those words triggers the
mapping.

| Entity | Voice Pattern | D365 Field | Type |
|--------|---------------|------------|------|
| opportunity | `opportunity stage` | stepname | String |
| opportunity | `amount\|budget\|price` | estimatedvalue | Money |
| opportunity | `close date\|deadline` | estimatedclosedate | DateTime |
| opportunity | `probability\|confidence` | closeprobability | Integer |
| contact | `name\|person` | fullname | String |
| contact | `title\|role\|position` | jobtitle | String |
| contact | `email` | emailaddress1 | String |
| contact | `phone\|number` | telephone1 | String |
| phonecall | `subject\|topic` | subject | String |
| phonecall | `description\|notes` | description | String |
| phonecall | `duration` | actualdurationminutes | Integer |

## Extracted opportunity updates

| Voice ID | name | stepname | estimatedvalue | estimatedclosedate | closeprobability |
|----------|------|----------|----------------|--------------------|------------------|
| VOC-001 | TechVantage Solutions - Enterprise Platform | Proposal | 200000 | 2025-12-15 | 65 |
| VOC-002 | Greenridge Partners - Renewal + Expansion | Negotiation | 84000 | 2026-01-10 | 80 |

## Extracted activity logs

| Voice ID | subject | description | actualdurationminutes |
|----------|---------|-------------|-----------------------|
| VOC-001 | Discovery follow-up call with Jennifer Walsh | Budget confirmed at $200K. CEO wants proposal by Dec 15. Include IT Director Sam Patel in next meeting. | 4 |
| VOC-002 | Renewal discussion with David Park | Renewal confirmed at $72K. Adding Analytics Standard at $12K/yr. Total new amount: $84K. | 3 |

## Extracted new contacts

| Voice ID | fullname | jobtitle | account |
|----------|----------|----------|---------|
| VOC-001 | Mark Davidson | CEO | TechVantage Solutions |
| VOC-001 | Sam Patel | IT Director | TechVantage Solutions |

VOC-002 produces no new contacts.

## Sync ledger

| ID | Voice ID | Entity | Status | D365 Record ID | Timestamp | Attempts | Error |
|----|----------|--------|--------|----------------|-----------|----------|-------|
| SYNC-001 | VOC-001 | opportunity | Pending | opp-a1b2c3 | 2025-11-14T14:30:00Z | 0 | - |
| SYNC-002 | VOC-001 | phonecall | Synced | act-d4e5f6 | 2025-11-14T14:30:05Z | 1 | - |
| SYNC-003 | VOC-001 | contact | Synced | con-g7h8i9 | 2025-11-14T14:30:10Z | 1 | - |
| SYNC-004 | VOC-002 | opportunity | Failed | opp-j1k2l3 | 2025-11-14T15:00:00Z | 3 | Record locked by another user |
| SYNC-005 | VOC-002 | phonecall | Synced | act-m4n5o6 | 2025-11-14T15:00:05Z | 1 | - |

## Meeting MTG-001

| Field | Detail |
|-------|--------|
| Title | TechVantage Solutions - Quarterly Business Review |
| Date | 2025-11-12 |
| Duration | 55 minutes |
| Sentiment | Positive |

### Attendees

| Name | Role | Company | Email |
|------|------|---------|-------|
| Jennifer Walsh | VP Operations | TechVantage Solutions | jennifer.walsh@techvantage.com |
| Sam Patel | IT Director | TechVantage Solutions | sam.patel@techvantage.com |
| Alex Rivera | Account Executive | Our Company | alex.rivera@ourcompany.com |
| Sarah Chen | Account Manager | Our Company | sarah.chen@ourcompany.com |

### Key topics

- Q3 usage review
- APAC expansion plans
- Analytics upgrade discussion
- Contract renewal timeline

### Decisions

- Proceed with Analytics Pro evaluation
- Schedule technical deep-dive with IT team
- Begin renewal discussions in January

## Action items (MTG-001)

| ID | Action | Owner | Due Date | Status | Priority |
|----|--------|-------|----------|--------|----------|
| AI-001 | Send Analytics Pro product brief and pricing | Alex Rivera | 2025-11-15 | Open | High |
| AI-002 | Schedule technical deep-dive session with IT team | Sarah Chen | 2025-11-19 | Open | High |
| AI-003 | Provide APAC deployment case studies | Alex Rivera | 2025-11-22 | Open | Medium |
| AI-004 | Share Q3 usage analytics dashboard | Sarah Chen | 2025-11-14 | Open | High |
| AI-005 | Prepare renewal proposal framework | Alex Rivera | 2025-12-15 | Open | Medium |
| AI-006 | Evaluate SSO integration requirements for APAC | Sam Patel | 2025-12-01 | Open | Medium |

## Distribution lists (MTG-001)

| List | Recipients | Members |
|------|------------|---------|
| all_attendees | 4 | jennifer.walsh@techvantage.com, sam.patel@techvantage.com, alex.rivera@ourcompany.com, sarah.chen@ourcompany.com |
| external_only | 2 | jennifer.walsh@techvantage.com, sam.patel@techvantage.com |
| internal_only | 2 | alex.rivera@ourcompany.com, sarah.chen@ourcompany.com |
| action_item_owners | 3 | alex.rivera@ourcompany.com, sarah.chen@ourcompany.com, sam.patel@techvantage.com |

## Email templates

| Template | Subject line |
|----------|--------------|
| meeting_recap | `Meeting Recap: {meeting_title} - {date}` |
| follow_up | `Follow-up: {action_item} - {meeting_title}` |

The `meeting_recap` body fills `{attendee_names}`, `{topics}`, `{decisions}`,
`{action_items}`, and `{sender_name}`. The `follow_up` body fills
`{recipient_name}`, `{date}`, `{meeting_title}`, `{content}`, and
`{sender_name}`. The sender is Alex Rivera.
