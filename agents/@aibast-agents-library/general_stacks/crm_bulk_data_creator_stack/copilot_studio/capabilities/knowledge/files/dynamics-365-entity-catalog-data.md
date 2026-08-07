# Dynamics 365 Entity Catalog Data

> SYNTHETIC — DEMO DATA. Every entity, attribute, record, and import template
> in this document is fictional. This file exists so the agent has a working
> world to answer from on day one. In production, replace this file with tools
> that read your real Dynamics 365 metadata and Web API (see the README's
> production section).

## Entity catalog

| Entity | Display Name | Primary Key | Primary Name | Attributes | Records |
|--------|--------------|-------------|--------------|------------|---------|
| account | Account | accountid | name | 12 | 1,247 |
| contact | Contact | contactid | fullname | 8 | 4,532 |
| opportunity | Opportunity | opportunityid | name | 9 | 892 |

## Account attributes

| Name | Type | Required | Details |
|------|------|----------|---------|
| accountid | Uniqueidentifier | Yes | |
| name | String | Yes | max: 160 |
| accountnumber | String | No | max: 20 |
| industrycode | Picklist | No | |
| revenue | Money | No | |
| numberofemployees | Integer | No | |
| telephone1 | String | No | max: 50 |
| emailaddress1 | String | No | max: 100 |
| websiteurl | String | No | max: 200 |
| address1_city | String | No | max: 80 |
| address1_stateorprovince | String | No | max: 50 |
| ownerid | Lookup | Yes | -> systemuser |

## Contact attributes

| Name | Type | Required | Details |
|------|------|----------|---------|
| contactid | Uniqueidentifier | Yes | |
| firstname | String | No | max: 50 |
| lastname | String | Yes | max: 50 |
| emailaddress1 | String | No | max: 100 |
| telephone1 | String | No | max: 50 |
| jobtitle | String | No | max: 100 |
| parentcustomerid | Lookup | No | -> account |
| ownerid | Lookup | Yes | -> systemuser |

## Opportunity attributes

| Name | Type | Required | Details |
|------|------|----------|---------|
| opportunityid | Uniqueidentifier | Yes | |
| name | String | Yes | max: 300 |
| estimatedvalue | Money | No | |
| estimatedclosedate | DateTime | No | |
| stepname | String | No | max: 200 |
| parentaccountid | Lookup | No | -> account |
| parentcontactid | Lookup | No | -> contact |
| closeprobability | Integer | No | |
| ownerid | Lookup | Yes | -> systemuser |

## Sample account records

| accountid | name | accountnumber | industrycode | revenue | numberofemployees | address1_city | address1_stateorprovince |
|-----------|------|---------------|--------------|---------|-------------------|---------------|--------------------------|
| a1b2c3d4-0001 | Contoso Ltd | ACC-10001 | Technology | 45000000 | 320 | Seattle | WA |
| a1b2c3d4-0002 | Fabrikam Inc | ACC-10002 | Manufacturing | 89000000 | 650 | Portland | OR |
| a1b2c3d4-0003 | Adventure Works | ACC-10003 | Retail | 12000000 | 95 | Denver | CO |

## Sample contact records

| contactid | firstname | lastname | emailaddress1 | jobtitle | parentcustomerid |
|-----------|-----------|----------|---------------|----------|------------------|
| c1d2e3f4-0001 | Alex | Rivera | alex.rivera@contoso.com | CTO | a1b2c3d4-0001 |
| c1d2e3f4-0002 | Kim | Park | kim.park@fabrikam.com | VP Operations | a1b2c3d4-0002 |
| c1d2e3f4-0003 | Jordan | Hayes | jordan.hayes@adventureworks.com | Purchasing Manager | a1b2c3d4-0003 |

## Sample opportunity records

| opportunityid | name | estimatedvalue | stepname | closeprobability | parentaccountid | estimatedclosedate |
|---------------|------|----------------|----------|------------------|-----------------|--------------------|
| o1p2q3r4-0001 | Contoso - Cloud Migration | 125000 | Proposal | 60 | a1b2c3d4-0001 | 2025-12-15 |
| o1p2q3r4-0002 | Fabrikam - IoT Platform | 89000 | Qualification | 30 | a1b2c3d4-0002 | 2026-02-28 |

## Bulk import templates

| Template | Entity | Format | Required columns | Max batch size | Est. time per 1000 | Duplicate detection |
|----------|--------|--------|------------------|----------------|--------------------|---------------------|
| account_import | account | CSV | name, accountnumber | 1,000 | 45 seconds | name, accountnumber |
| contact_import | contact | CSV | lastname | 2,000 | 30 seconds | emailaddress1, firstname+lastname |
| opportunity_import | opportunity | CSV | name | 500 | 60 seconds | name, parentaccountid |

### Optional columns per template

| Template | Optional columns |
|----------|------------------|
| account_import | industrycode, revenue, numberofemployees, telephone1, emailaddress1, websiteurl, address1_city, address1_stateorprovince |
| contact_import | firstname, emailaddress1, telephone1, jobtitle, parentcustomerid |
| opportunity_import | estimatedvalue, estimatedclosedate, stepname, parentaccountid, closeprobability |

## Simulated import preview figures

These figures are fixed demo values, identical for every entity. They are not a
scan of a user-supplied file.

| Metric | Value |
|--------|-------|
| Records to import | 500 |
| Duplicates detected | 12 |
| Records to create | 488 |
| Estimated time | 23 seconds |
