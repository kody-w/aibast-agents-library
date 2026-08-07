# ServiceNow and SharePoint Data

> SYNTHETIC - DEMO DATA. Every incident, knowledge article, assignment group,
> document, and URL in this document is fictional. This file exists so the agent
> has a working world to answer from on day one. In production, replace this
> file with tools that read your real ServiceNow instance and your SharePoint
> document libraries (see the README's production section).

## ServiceNow incidents

| Number | Short Description | Category / Subcategory | Impact | Urgency | Priority | State | Assigned To | Group | Caller | Opened | SLA Breach |
|--------|-------------------|-----------------------|--------|---------|----------|-------|-------------|-------|--------|-----------|------------|
| INC-20001 | Email server unresponsive - 500+ users affected | Infrastructure / Email | 1 | 1 | P1-Critical | In Progress | Sarah Chen | Network Operations | Marcus Thompson | 2025-11-14T08:20:00Z | 2025-11-14T09:20:00Z |
| INC-20002 | VPN authentication failing for remote workers | Network / VPN | 2 | 2 | P2-High | Assigned | Mike Torres | Network Operations | Lisa Wong | 2025-11-14T08:45:00Z | 2025-11-14T12:45:00Z |
| INC-20003 | Printer offline on Floor 3 - Board room | Hardware / Printer | 3 | 2 | P3-Medium | Open | unassigned | Desktop Support | Jennifer Walsh | 2025-11-14T09:00:00Z | 2025-11-14T17:00:00Z |

### Incident descriptions and work notes

| Number | Description | Work Notes |
|--------|-------------|------------|
| INC-20001 | Exchange Online hybrid connector failing. Users unable to send/receive emails since 8:15 AM. Cloud-to-on-prem sync broken. | Exchange hybrid connector logs show certificate expiry. Renewing certificate now. |
| INC-20002 | Pulse Secure VPN returning authentication errors for users with MFA enabled. Started after last night's Azure AD update. | Investigating Azure AD conditional access policy changes from last night. |
| INC-20003 | HP LaserJet Pro M428 in Board Room 3A showing offline. Executive presentation at 10 AM requires printing. | (empty) |

## Knowledge base

Articles are indexed by category. The four categories present are Email,
Network, Hardware, and Process. **There is no Infrastructure article**, so
INC-20001 (category Infrastructure) matches nothing.

| Article | Title | Category | Views | Rating | Last Updated |
|---------|-------|----------|-------|--------|--------------|
| KB0010234 | Exchange Hybrid Connector - Certificate Renewal | Email | 1,247 | 4.8 | 2025-10-15 |
| KB0010198 | VPN MFA Authentication Troubleshooting | Network | 2,340 | 4.5 | 2025-11-01 |
| KB0010156 | HP LaserJet Printer Offline Recovery | Hardware | 3,890 | 4.2 | 2025-09-20 |
| KB0010301 | ServiceNow Incident Escalation Procedures | Process | 890 | 4.6 | 2025-10-28 |

### Resolution steps

| Article | Steps |
|---------|-------|
| KB0010234 | 1. Open Exchange Admin Center 2. Navigate to Organization > Sharing 3. Renew federation certificate 4. Restart MSExchangeHybridService 5. Verify mail flow with Test-MailFlow cmdlet |
| KB0010198 | 1. Check Azure AD Conditional Access policies 2. Verify MFA service health at status.azure.com 3. Clear VPN client cached credentials 4. Re-register MFA method at aka.ms/mfasetup 5. Test with basic authentication first |
| KB0010156 | 1. Power cycle the printer (30 second wait) 2. Check network cable / WiFi connection 3. Run printer troubleshooter on client PC 4. Reinstall printer driver if needed 5. Clear print queue and restart spooler |
| KB0010301 | 1. Verify incident priority matrix 2. Contact assignment group lead 3. Update incident with escalation notes 4. Notify management per escalation policy 5. Track response time against SLA |

## Assignment groups

| Group | Manager | Members | Active Incidents | Avg Resolution | SLA Met |
|-------|---------|---------|------------------|----------------|---------|
| Network Operations | David Kim | 6 | 8 | 3.5h | 96.2% |
| Desktop Support | Lisa Park | 8 | 22 | 5.2h | 92.8% |
| Application Support | James Mitchell | 5 | 12 | 4.8h | 94.5% |
| Database Administration | Maria Santos | 3 | 4 | 6.1h | 97.0% |
| Security Operations | Frank O'Brien | 4 | 3 | 2.8h | 98.5% |

## SLA targets

| Priority | Response | Resolution | Notification | Update Frequency |
|----------|----------|------------|--------------|------------------|
| P1-Critical | 15m | 1h | VP IT + On-Call Manager | 15m |
| P2-High | 30m | 4h | Assignment Group Manager | 30m |
| P3-Medium | 60m | 8h | Assignment Group | 60m |
| P4-Low | 240m | 24h | Queue | 240m |

## SharePoint document library

| ID | Title | File Name | Library | Folder | Type | Size | Modified | Modified By | Tags |
|----|-------|-----------|---------|--------|------|------|----------|-------------|------|
| DOC-001 | Enterprise Platform - Product Brief | Enterprise_Platform_Brief_v3.pdf | Sales Collateral | /Products/Platform | PDF | 2,450 KB | 2025-10-28 | Marketing Team | product, platform, enterprise, brief |
| DOC-002 | Q3 2025 Sales Playbook | Q3_2025_Sales_Playbook.pptx | Sales Enablement | /Playbooks/2025 | PowerPoint | 8,900 KB | 2025-09-15 | Sales Ops | playbook, sales, q3, 2025 |
| DOC-003 | Competitive Analysis - Competitor B | Competitive_Analysis_CompB_2025.xlsx | Competitive Intel | /Competitors | Excel | 1,200 KB | 2025-11-05 | Product Marketing | competitive, analysis, competitor-b |
| DOC-004 | ROI Calculator Template | ROI_Calculator_Template_v2.xlsx | Sales Tools | /Calculators | Excel | 350 KB | 2025-08-20 | Finance Team | roi, calculator, template, pricing |
| DOC-005 | Customer Reference - Meridian Corp Case Study | Meridian_Corp_Case_Study.pdf | Customer Success | /Case Studies/Technology | PDF | 1,800 KB | 2025-10-10 | Customer Success | case-study, meridian, technology, reference |
| DOC-006 | MSA Template - Enterprise Agreement | MSA_Enterprise_Template_2025.docx | Legal Templates | /Contracts/Templates | Word | 420 KB | 2025-07-01 | Legal Team | contract, msa, enterprise, template, legal |
| DOC-007 | HIPAA Compliance Whitepaper | HIPAA_Compliance_Whitepaper.pdf | Compliance | /Healthcare | PDF | 3,200 KB | 2025-09-20 | Compliance Team | hipaa, compliance, healthcare, whitepaper |

### Document URLs

| ID | URL |
|----|-----|
| DOC-001 | https://contoso.sharepoint.com/sites/sales/Shared%20Documents/Products/Platform/Enterprise_Platform_Brief_v3.pdf |
| DOC-002 | https://contoso.sharepoint.com/sites/sales/Shared%20Documents/Playbooks/2025/Q3_2025_Sales_Playbook.pptx |
| DOC-003 | https://contoso.sharepoint.com/sites/sales/Shared%20Documents/Competitors/Competitive_Analysis_CompB_2025.xlsx |
| DOC-004 | https://contoso.sharepoint.com/sites/sales/Shared%20Documents/Calculators/ROI_Calculator_Template_v2.xlsx |
| DOC-005 | https://contoso.sharepoint.com/sites/sales/Shared%20Documents/Case%20Studies/Technology/Meridian_Corp_Case_Study.pdf |
| DOC-006 | https://contoso.sharepoint.com/sites/legal/Shared%20Documents/Contracts/Templates/MSA_Enterprise_Template_2025.docx |
| DOC-007 | https://contoso.sharepoint.com/sites/compliance/Shared%20Documents/Healthcare/HIPAA_Compliance_Whitepaper.pdf |

### URL patterns

| Type | Pattern |
|------|---------|
| direct_download | `https://{tenant}.sharepoint.com/sites/{site}/_layouts/15/download.aspx?SourceUrl={encoded_path}` |
| web_view | `https://{tenant}.sharepoint.com/sites/{site}/_layouts/15/Doc.aspx?sourcedoc={doc_id}` |
| sharing_link | `https://{tenant}.sharepoint.com/:b:/s/{site}/{share_id}` |
| embed | `https://{tenant}.sharepoint.com/sites/{site}/_layouts/15/embed.aspx?UniqueId={doc_id}` |

### Metadata fields available

| Category | Fields |
|----------|--------|
| standard | Title, File Name, Modified, Modified By, File Size, Content Type |
| custom | Document Category, Target Audience, Approval Status, Expiration Date, Confidentiality Level |
| search | Tags, Full Text Index, Associated Account, Deal Stage |

## Link validation ledger

| Doc ID | Status | HTTP | Accessible | Permissions | Last Checked |
|--------|--------|------|------------|-------------|--------------|
| DOC-001 | Valid | 200 | Yes | Organization | 2025-11-14T10:00:00Z |
| DOC-002 | Valid | 200 | Yes | Sales Team | 2025-11-14T10:00:01Z |
| DOC-003 | Valid | 200 | Yes | Sales Team | 2025-11-14T10:00:02Z |
| DOC-004 | Valid | 200 | Yes | Organization | 2025-11-14T10:00:03Z |
| DOC-005 | Valid | 200 | Yes | Organization | 2025-11-14T10:00:04Z |
| DOC-006 | Restricted | 403 | No | Legal Team Only | 2025-11-14T10:00:05Z |
| DOC-007 | Valid | 200 | Yes | Organization | 2025-11-14T10:00:06Z |
