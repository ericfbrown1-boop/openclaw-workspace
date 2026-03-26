---
name: salesforce-analytics
description: >
  Cohesity Salesforce pipeline analytics. Extract open opportunities,
  deal stages, competitor overlap, win/loss trends, and forecast accuracy
  via the Salesforce REST API. Feeds into 6 AM daily briefing and on-demand
  pipeline reviews for Eric (CFO & COO).
---

# Salesforce Pipeline Analytics

## When to Use
- Daily briefing (6 AM PT) — pipeline section
- Eric asks for pipeline, forecast, or competitive deal data
- Board prep or QBR materials
- Weekly/monthly sales reporting
- Forecast accuracy tracking (called vs actual)

## Architecture Overview

```
Salesforce REST API (OAuth 2.0 JWT Bearer)
    |
    v
sfdc_analytics.py (simple-salesforce + SOQL)
    |
    +---> memory/sfdc-pipeline-snapshot.json   (daily state)
    +---> memory/sfdc-forecast-history.json    (rolling 8-quarter log)
    +---> stdout (markdown tables for briefing)
    +---> gog gmail send (daily briefing integration)
```

---

## Prerequisites

### 1. Salesforce Connected App (one-time, requires Salesforce admin)

A Connected App in the Cohesity Salesforce org enables server-to-server API access without interactive login.

**Steps for Salesforce admin:**
1. Go to **Setup > App Manager > New Connected App**
2. Name: `Jarvis Pipeline Analytics`
3. Enable OAuth Settings:
   - Callback URL: `https://login.salesforce.com/services/oauth2/callback` (not actually used for JWT flow)
   - Selected OAuth Scopes: `api`, `refresh_token`, `offline_access`
4. Enable **"Use digital signatures"** and upload the public key (see step 2 below)
5. Under **Manage > Policies**: set "Permitted Users" to **"Admin approved users are pre-authorized"**
6. Add Eric's Salesforce user (or a dedicated integration user) to the Connected App's profile/permission set
7. Record:
   - **Consumer Key** (client_id)
   - **Consumer Secret** (client_secret — needed only for refresh-token flow, not JWT)

### 2. Authentication — Two Options

#### Option A: JWT Bearer Flow (preferred for automation)

No refresh tokens to manage. Uses a private key to mint assertions.

**Generate keypair:**
```bash
openssl genrsa -out sfdc_jwt_private.pem 2048
openssl rsa -in sfdc_jwt_private.pem -pubout -out sfdc_jwt_public.pem
# Upload sfdc_jwt_public.pem to the Connected App (step 1.4 above)
# Store sfdc_jwt_private.pem in 1Password (Jarvis vault) as "SFDC JWT Private Key"
```

**How it works at runtime:**
1. Build a JWT with `iss=consumer_key`, `sub=salesforce_username`, `aud=https://login.salesforce.com`, `exp=now+300`
2. Sign with the private key (RS256)
3. POST to `https://login.salesforce.com/services/oauth2/token` with `grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=<jwt>`
4. Receive `access_token` and `instance_url` — valid for ~2 hours

#### Option B: Refresh Token Flow (simpler initial setup)

One interactive login, then automated refresh forever.

**Initial token acquisition (one-time, interactive):**
```bash
# Open in browser — log in and authorize:
# https://login.salesforce.com/services/oauth2/authorize?response_type=code&client_id=<CONSUMER_KEY>&redirect_uri=https://login.salesforce.com/services/oauth2/callback&scope=api+refresh_token

# After redirect, capture the ?code= parameter, then:
curl -X POST https://login.salesforce.com/services/oauth2/token \
  -d "grant_type=authorization_code" \
  -d "code=<AUTH_CODE>" \
  -d "client_id=<CONSUMER_KEY>" \
  -d "client_secret=<CONSUMER_SECRET>" \
  -d "redirect_uri=https://login.salesforce.com/services/oauth2/callback"
# Response: { "access_token": "...", "refresh_token": "...", "instance_url": "..." }
```

Store `refresh_token`, `client_id`, `client_secret` in 1Password (Jarvis vault) as "SFDC OAuth Refresh Token".

**Credential storage in 1Password:**
```bash
# Store (once):
op item create --vault "Jarvis" --category "API Credential" \
  --title "SFDC OAuth" \
  "consumer_key=3MVG8..." \
  "consumer_secret=..." \
  "refresh_token=..." \
  "username=eric.brown@cohesity.com" \
  "instance_url=https://cohesity.my.salesforce.com"

# Retrieve at runtime:
SFDC_CONSUMER_KEY=$(op read "op://Jarvis/SFDC OAuth/consumer_key")
SFDC_REFRESH_TOKEN=$(op read "op://Jarvis/SFDC OAuth/refresh_token")
```

---

## Installation

```bash
pip install simple-salesforce PyJWT cryptography requests tabulate
```

- `simple-salesforce` — Salesforce REST API / SOQL client
- `PyJWT` — JWT minting for OAuth JWT bearer flow
- `cryptography` — RSA key loading for JWT signing
- `tabulate` — Markdown table formatting
- `requests` — HTTP (already a dependency of simple-salesforce)

---


> **Full implementation script:** See [IMPLEMENTATION.md](IMPLEMENTATION.md) for the complete `sfdc_analytics.py` source code.


## SOQL Query Reference

These are the key queries. Adjust field names after running `--mode discover` on the live org.

### Pipeline by Stage (Open)
```sql
SELECT StageName, COUNT(Id) OppCount, SUM(Amount) TotalAmount, AVG(Amount) AvgAmount
FROM Opportunity
WHERE IsClosed = FALSE AND Amount > 0
GROUP BY StageName
ORDER BY SUM(Amount) DESC
```

### Top Open Deals
```sql
SELECT Id, Name, Account.Name, StageName, Amount, CloseDate, Probability, Owner.Name
FROM Opportunity
WHERE IsClosed = FALSE AND Amount > 0
ORDER BY Amount DESC
LIMIT 20
```

### Competitive Deals (via OpportunityCompetitor)
```sql
SELECT Opportunity.Name, Opportunity.Account.Name, Opportunity.StageName,
       Opportunity.Amount, Opportunity.IsWon, CompetitorName
FROM OpportunityCompetitor
WHERE CompetitorName IN ('Rubrik','Commvault','Veeam','Dell','Veritas')
ORDER BY Opportunity.Amount DESC
```

### Win/Loss Last 90 Days
```sql
SELECT IsWon, COUNT(Id) DealCount, SUM(Amount) TotalAmount
FROM Opportunity
WHERE IsClosed = TRUE AND CloseDate >= LAST_N_DAYS:90 AND Amount > 0
GROUP BY IsWon
```

### Win Rate by Rep
```sql
SELECT Owner.Name, IsWon, COUNT(Id) DealCount, SUM(Amount) TotalAmount
FROM Opportunity
WHERE IsClosed = TRUE AND CloseDate >= LAST_N_DAYS:90 AND Amount > 0
GROUP BY Owner.Name, IsWon
ORDER BY SUM(Amount) DESC
```

### Forecast Category Rollup by Quarter
```sql
SELECT ForecastCategory, FISCAL_QUARTER(CloseDate) FQ, FISCAL_YEAR(CloseDate) FY,
       SUM(Amount) TotalAmount, COUNT(Id) DealCount
FROM Opportunity
WHERE CloseDate >= LAST_N_QUARTERS:4 AND Amount > 0
GROUP BY ForecastCategory, FISCAL_QUARTER(CloseDate), FISCAL_YEAR(CloseDate)
ORDER BY FISCAL_YEAR(CloseDate) DESC, FISCAL_QUARTER(CloseDate) DESC
```

### Stale Deals (no activity in 14+ days)
```sql
SELECT Id, Name, Account.Name, StageName, Amount, CloseDate, Owner.Name, LastActivityDate
FROM Opportunity
WHERE IsClosed = FALSE AND Amount > 0
  AND LastActivityDate < LAST_N_DAYS:14
ORDER BY Amount DESC
LIMIT 20
```

### New Pipeline Created This Week
```sql
SELECT Owner.Name, COUNT(Id) NewDeals, SUM(Amount) NewAmount
FROM Opportunity
WHERE CreatedDate = THIS_WEEK AND Amount > 0
GROUP BY Owner.Name
ORDER BY SUM(Amount) DESC
```

### Deals Closing This Quarter
```sql
SELECT Id, Name, Account.Name, StageName, Amount, CloseDate, Probability, Owner.Name
FROM Opportunity
WHERE IsClosed = FALSE AND CloseDate = THIS_FISCAL_QUARTER AND Amount > 0
ORDER BY Amount DESC
```

---

## Error Handling

### Authentication Failures
- `SalesforceAuthenticationFailed` — refresh token expired or Connected App deauthorized
  - Action: Re-run browser OAuth flow, update 1Password
  - For JWT: Check key expiry, re-upload public key to Connected App
- Log auth failures to `memory/incidents.jsonl` per INCIDENTS.md protocol

### Rate Limits
- Salesforce API limit: typically 15,000-100,000 calls/24h depending on org edition
- `simple-salesforce` raises `SalesforceGeneralError` with `REQUEST_LIMIT_EXCEEDED`
- Mitigation: Use `query_all()` (auto-paginates via `nextRecordsUrl`) to minimize calls
- The full briefing mode makes ~6 API calls total — well within limits
- If rate-limited, back off 60 seconds and retry once; then fail and log

### SOQL Errors
- Field doesn't exist: Run `--mode discover` first, adjust field names
- `MALFORMED_QUERY`: Check that custom field API names end in `__c`
- Object not accessible: Connected App user needs read permission on Opportunity, Account, User

### Network/Timeout
- `simple-salesforce` default timeout: 30 seconds
- For large orgs, `query_all()` may paginate many times — set `sf.timeout = 120`

---

## Integration Points

### Daily Briefing Email (6 AM PT)

The briefing script calls `generate_briefing_section(sf)` and inserts the markdown into the email body. Integration with the existing briefing workflow:

```bash
# In the daily briefing cron/script:
SFDC_SECTION=$(python3 ~/.openclaw/workspace/scripts/sfdc_analytics.py --mode briefing 2>/dev/null)

# If SFDC fails, note it but don't block the briefing
if [ $? -ne 0 ]; then
    SFDC_SECTION="**Salesforce section unavailable** — check auth and retry."
fi

# Insert into the full briefing markdown alongside other sections
# Then send via gog:
gog gmail send \
  --to ericfbrown1@gmail.com \
  --cc Eric.brown@cohesity.com \
  --subject "Jarvis Daily Briefing — $(date +'%A, %B %d, %Y')" \
  --body "$FULL_BRIEFING_BODY"
```

### Memory/State Files

| File | Purpose | Update Frequency |
|------|---------|-----------------|
| `memory/sfdc-pipeline-snapshot.json` | Daily pipeline state (amount, count by stage) | Daily via `--mode snapshot` |
| `memory/sfdc-forecast-history.json` | Rolling forecast accuracy log | Weekly or end-of-quarter |
| `memory/sfdc-schema-discovery.json` | Opportunity field map from `--mode discover` | Once, or after schema changes |

### Google Sheets (optional historical tracking)

```bash
# Push pipeline summary to a tracking sheet
gog sheets append <SHEET_ID> "Pipeline!A:D" \
  --values-json "[
    [\"$(date +%Y-%m-%d)\", \"$TOTAL_PIPELINE\", \"$DEAL_COUNT\", \"$WIN_RATE\"]
  ]" \
  --insert INSERT_ROWS
```

---

## First-Time Setup Checklist

1. [ ] Salesforce admin creates Connected App (see Prerequisites section)
2. [ ] Choose auth flow (JWT or refresh token) and complete initial authentication
3. [ ] Store credentials in 1Password Jarvis vault as "SFDC OAuth"
4. [ ] `pip install simple-salesforce PyJWT cryptography requests tabulate`
5. [ ] Copy `sfdc_analytics.py` to `~/.openclaw/workspace/scripts/`
6. [ ] Run `python3 sfdc_analytics.py --mode discover` to map Cohesity's actual Opportunity fields
7. [ ] Adjust `COMPETITORS`, `STAGE_ORDER`, and any custom field names in the script based on discovery output
8. [ ] Test: `python3 sfdc_analytics.py --mode pipeline` — confirm data returns
9. [ ] Test: `python3 sfdc_analytics.py --mode briefing` — confirm full output
10. [ ] Add `--mode snapshot` to daily cron (after briefing send)
11. [ ] Wire `generate_briefing_section()` into the 6 AM briefing pipeline

---

## Salesforce Objects Reference (for extending)

| Object | Use Case | Key Fields |
|--------|----------|------------|
| `Opportunity` | Pipeline, deals, win/loss | Amount, StageName, CloseDate, IsWon, IsClosed, ForecastCategory, Probability |
| `OpportunityCompetitor` | Competitive analysis | CompetitorName, Strengths, Weaknesses |
| `OpportunityHistory` | Stage progression tracking | StageName, Amount, CreatedDate |
| `Account` | Customer/prospect info | Name, Industry, AnnualRevenue, BillingCountry |
| `ForecastingItem` | Collaborative Forecasts | ForecastAmount, ForecastCategory (requires CF enabled) |
| `User` | Rep performance | Name, UserRole.Name, IsActive |
| `Task` / `Event` | Activity tracking | Subject, ActivityDate, WhoId, WhatId |

---

## Extending the Script

### ARR / ACV / TCV Custom Fields
Cohesity likely has custom fields for ARR, ACV, or TCV on Opportunity. After running `--mode discover`, look for fields like:
- `ARR__c`, `Annual_Recurring_Revenue__c`
- `ACV__c`, `Annual_Contract_Value__c`
- `TCV__c`, `Total_Contract_Value__c`

Add these to the SELECT clauses and summary tables. For a data protection company, ARR is the north-star metric — prioritize it over one-time Amount.

### Segment / Region Breakdowns
Add groupings to existing queries:
```sql
SELECT Account.Industry, StageName, COUNT(Id), SUM(Amount)
FROM Opportunity WHERE IsClosed = FALSE AND Amount > 0
GROUP BY Account.Industry, StageName
```

### Deal Velocity (Days in Stage)
```sql
SELECT StageName, AVG(CALENDAR_MONTH(CloseDate) - CALENDAR_MONTH(CreatedDate)) AvgMonths,
       COUNT(Id)
FROM Opportunity WHERE IsWon = TRUE AND CloseDate >= LAST_N_QUARTERS:2
GROUP BY StageName
```

### Renewal Pipeline
```sql
SELECT Id, Name, Account.Name, Amount, CloseDate, Type
FROM Opportunity
WHERE Type = 'Renewal' AND IsClosed = FALSE
ORDER BY CloseDate ASC
```
