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

## Core Script: `sfdc_analytics.py`

Location: `~/.openclaw/workspace/scripts/sfdc_analytics.py`

```python
#!/usr/bin/env python3
"""
Salesforce Pipeline Analytics for Cohesity CFO/COO.
Extracts pipeline, competitive deals, win/loss, and forecast data.

Usage:
    python3 sfdc_analytics.py --mode pipeline        # Open pipeline by stage
    python3 sfdc_analytics.py --mode competitive      # Deals with competitors
    python3 sfdc_analytics.py --mode winloss          # Win/loss trends
    python3 sfdc_analytics.py --mode forecast          # Forecast vs actual
    python3 sfdc_analytics.py --mode briefing          # All sections, markdown for email
    python3 sfdc_analytics.py --mode snapshot          # Save daily state to memory/
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from simple_salesforce import Salesforce, SalesforceAuthenticationFailed
    from tabulate import tabulate
except ImportError:
    print("ERROR: pip install simple-salesforce tabulate", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE",
                                os.path.expanduser("~/.openclaw/workspace")))
MEMORY_DIR = WORKSPACE / "memory"
SNAPSHOT_FILE = MEMORY_DIR / "sfdc-pipeline-snapshot.json"
FORECAST_HISTORY_FILE = MEMORY_DIR / "sfdc-forecast-history.json"

# Cohesity fiscal calendar: FY ends July 31.
# FY2026 = Aug 1 2025 — Jul 31 2026.  Q1=Aug-Oct, Q2=Nov-Jan, Q3=Feb-Apr, Q4=May-Jul.
FISCAL_YEAR_START_MONTH = 8  # August

COMPETITORS = ["Rubrik", "Commvault", "Veeam", "Dell", "Veritas", "Arcserve"]

# Stage ordering for pipeline display (adjust to match Cohesity's actual stage names)
STAGE_ORDER = [
    "Prospecting",
    "Discovery",
    "Qualification",
    "Solution Validation",
    "Proposal/Negotiation",
    "Contract Sent",
    "Closed Won",
    "Closed Lost",
]

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
def get_credentials_from_op():
    """Pull SFDC credentials from 1Password CLI."""
    def op_read(field):
        result = subprocess.run(
            ["op", "read", f"op://Jarvis/SFDC OAuth/{field}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            raise RuntimeError(f"1Password read failed for {field}: {result.stderr.strip()}")
        return result.stdout.strip()

    return {
        "consumer_key": op_read("consumer_key"),
        "consumer_secret": op_read("consumer_secret"),
        "refresh_token": op_read("refresh_token"),
        "username": op_read("username"),
        "instance_url": op_read("instance_url"),
    }


def connect_sfdc():
    """
    Connect to Salesforce using refresh token flow.
    Returns a simple_salesforce.Salesforce instance.
    """
    creds = get_credentials_from_op()

    try:
        sf = Salesforce(
            instance_url=creds["instance_url"],
            consumer_key=creds["consumer_key"],
            consumer_secret=creds["consumer_secret"],
            refresh_token=creds["refresh_token"],
            domain="login",  # use "test" for sandbox
        )
    except SalesforceAuthenticationFailed as e:
        print(f"SFDC AUTH FAILED: {e}", file=sys.stderr)
        print("Action: Re-authenticate via browser flow and update 1Password.", file=sys.stderr)
        sys.exit(1)

    return sf


def connect_sfdc_jwt():
    """
    Alternative: Connect via JWT bearer flow.
    Requires sfdc_jwt_private.pem accessible via 1Password or local file.
    """
    import jwt as pyjwt
    import requests
    from datetime import timezone

    creds = get_credentials_from_op()

    # Load private key — from 1Password document or local secure file
    key_path = WORKSPACE / "config" / "sfdc_jwt_private.pem"
    if not key_path.exists():
        # Try fetching from 1Password
        result = subprocess.run(
            ["op", "document", "get", "SFDC JWT Private Key", "--vault", "Jarvis"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            raise RuntimeError("Cannot load SFDC JWT private key from 1Password or local file")
        private_key = result.stdout
    else:
        private_key = key_path.read_text()

    now = datetime.now(timezone.utc)
    payload = {
        "iss": creds["consumer_key"],
        "sub": creds["username"],
        "aud": "https://login.salesforce.com",
        "exp": int((now + timedelta(minutes=5)).timestamp()),
    }
    assertion = pyjwt.encode(payload, private_key, algorithm="RS256")

    resp = requests.post("https://login.salesforce.com/services/oauth2/token", data={
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": assertion,
    }, timeout=15)

    if resp.status_code != 200:
        raise RuntimeError(f"JWT auth failed ({resp.status_code}): {resp.text}")

    token_data = resp.json()
    sf = Salesforce(
        instance_url=token_data["instance_url"],
        session_id=token_data["access_token"],
    )
    return sf


# ---------------------------------------------------------------------------
# SOQL Queries
# ---------------------------------------------------------------------------

def query_open_pipeline(sf):
    """
    Open opportunities grouped by stage, with amounts.
    Returns list of dicts with: StageName, OppCount, TotalAmount, AvgAmount, Opportunities (detail list).
    """
    # Summary by stage
    summary_soql = """
        SELECT StageName,
               COUNT(Id) OppCount,
               SUM(Amount) TotalAmount,
               AVG(Amount) AvgAmount
        FROM Opportunity
        WHERE IsClosed = FALSE
          AND Amount > 0
        GROUP BY StageName
        ORDER BY SUM(Amount) DESC
    """
    summary = sf.query_all(summary_soql)["records"]

    # Top 20 largest open deals (detail)
    detail_soql = """
        SELECT Id, Name, Account.Name, StageName, Amount,
               CloseDate, Probability, Owner.Name,
               CreatedDate, LastModifiedDate
        FROM Opportunity
        WHERE IsClosed = FALSE
          AND Amount > 0
        ORDER BY Amount DESC
        LIMIT 20
    """
    top_deals = sf.query_all(detail_soql)["records"]

    return {"summary": summary, "top_deals": top_deals}


def query_competitive_deals(sf):
    """
    Opportunities where a competitor is mentioned.
    Looks at the standard Competitor__c custom field and the CompetitorName
    on OpportunityCompetitor junction object.

    IMPORTANT: Adjust field names to match Cohesity's actual schema.
    Common patterns:
      - Custom field on Opportunity: Competitor__c, Primary_Competitor__c
      - Standard junction: OpportunityCompetitor (if Competitors related list is enabled)
      - Custom multi-select: Competitors_Involved__c
    """
    # Attempt 1: OpportunityCompetitor junction (standard Salesforce)
    try:
        comp_soql = """
            SELECT Opportunity.Id, Opportunity.Name, Opportunity.Account.Name,
                   Opportunity.StageName, Opportunity.Amount, Opportunity.CloseDate,
                   Opportunity.IsClosed, Opportunity.IsWon,
                   CompetitorName
            FROM OpportunityCompetitor
            WHERE CompetitorName IN ('Rubrik', 'Commvault', 'Veeam',
                                      'Dell', 'Veritas', 'Arcserve')
            ORDER BY Opportunity.Amount DESC NULLS LAST
        """
        results = sf.query_all(comp_soql)["records"]
        return {"source": "OpportunityCompetitor", "records": results}
    except Exception:
        pass

    # Attempt 2: Custom field on Opportunity (common pattern)
    try:
        custom_soql = """
            SELECT Id, Name, Account.Name, StageName, Amount, CloseDate,
                   IsClosed, IsWon, Primary_Competitor__c
            FROM Opportunity
            WHERE Primary_Competitor__c != NULL
              AND Amount > 0
            ORDER BY Amount DESC
            LIMIT 200
        """
        results = sf.query_all(custom_soql)["records"]
        return {"source": "Primary_Competitor__c", "records": results}
    except Exception:
        pass

    # Attempt 3: Describe Opportunity to find the correct competitor field
    desc = sf.Opportunity.describe()
    comp_fields = [f["name"] for f in desc["fields"]
                   if "compet" in f["name"].lower() or "competitor" in f["label"].lower()]
    if comp_fields:
        field = comp_fields[0]
        fallback_soql = f"""
            SELECT Id, Name, Account.Name, StageName, Amount, CloseDate,
                   IsClosed, IsWon, {field}
            FROM Opportunity
            WHERE {field} != NULL AND Amount > 0
            ORDER BY Amount DESC LIMIT 200
        """
        results = sf.query_all(fallback_soql)["records"]
        return {"source": field, "records": results}

    return {"source": "none_found", "records": [],
            "error": "No competitor field found. Run schema discovery (see below)."}


def query_win_loss(sf, days_back=90):
    """
    Closed Won vs Closed Lost in the last N days.
    Breakdowns: by competitor, by segment, by owner, overall rates.
    """
    cutoff = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00Z")

    # Overall win/loss
    overall_soql = f"""
        SELECT IsWon,
               COUNT(Id) DealCount,
               SUM(Amount) TotalAmount
        FROM Opportunity
        WHERE IsClosed = TRUE
          AND CloseDate >= {cutoff[:10]}
          AND Amount > 0
        GROUP BY IsWon
    """
    overall = sf.query_all(overall_soql)["records"]

    # Win/loss by stage (for loss reason analysis — which stage did they die?)
    stage_soql = f"""
        SELECT StageName, IsWon,
               COUNT(Id) DealCount,
               SUM(Amount) TotalAmount
        FROM Opportunity
        WHERE IsClosed = TRUE
          AND CloseDate >= {cutoff[:10]}
          AND Amount > 0
        GROUP BY StageName, IsWon
        ORDER BY SUM(Amount) DESC
    """
    by_stage = sf.query_all(stage_soql)["records"]

    # Win/loss by owner (top 10 reps)
    owner_soql = f"""
        SELECT Owner.Name, IsWon,
               COUNT(Id) DealCount,
               SUM(Amount) TotalAmount
        FROM Opportunity
        WHERE IsClosed = TRUE
          AND CloseDate >= {cutoff[:10]}
          AND Amount > 0
        GROUP BY Owner.Name, IsWon
        ORDER BY SUM(Amount) DESC
        LIMIT 30
    """
    by_owner = sf.query_all(owner_soql)["records"]

    return {"overall": overall, "by_stage": by_stage, "by_owner": by_owner,
            "period_days": days_back}


def query_forecast_vs_actual(sf):
    """
    Compare forecasted amounts to actual closed-won by quarter.
    Uses the ForecastingItem or Opportunity.ForecastCategory.

    Salesforce forecast data access depends on org config:
    - If Collaborative Forecasts enabled: query ForecastingItem or ForecastingQuota
    - Fallback: use Opportunity.ForecastCategory rollups
    """
    # Approach: Roll up Opportunity data by ForecastCategory and fiscal quarter
    # This gives us: Pipeline, Best Case, Commit, Closed amounts per quarter
    forecast_soql = """
        SELECT ForecastCategory,
               FISCAL_QUARTER(CloseDate) FiscalQtr,
               FISCAL_YEAR(CloseDate) FiscalYr,
               SUM(Amount) TotalAmount,
               COUNT(Id) DealCount
        FROM Opportunity
        WHERE CloseDate >= LAST_N_QUARTERS:4
          AND Amount > 0
        GROUP BY ForecastCategory, FISCAL_QUARTER(CloseDate), FISCAL_YEAR(CloseDate)
        ORDER BY FISCAL_YEAR(CloseDate) DESC, FISCAL_QUARTER(CloseDate) DESC
    """
    results = sf.query_all(forecast_soql)["records"]

    # Also get the actual closed-won per quarter for comparison
    actual_soql = """
        SELECT FISCAL_QUARTER(CloseDate) FiscalQtr,
               FISCAL_YEAR(CloseDate) FiscalYr,
               SUM(Amount) ClosedWon
        FROM Opportunity
        WHERE IsWon = TRUE
          AND CloseDate >= LAST_N_QUARTERS:4
          AND Amount > 0
        GROUP BY FISCAL_QUARTER(CloseDate), FISCAL_YEAR(CloseDate)
        ORDER BY FISCAL_YEAR(CloseDate) DESC, FISCAL_QUARTER(CloseDate) DESC
    """
    actuals = sf.query_all(actual_soql)["records"]

    return {"by_category": results, "actuals": actuals}


def discover_schema(sf):
    """
    Utility: Describe the Opportunity object to find custom fields.
    Run this once to identify competitor fields, forecast fields, etc.
    Output saved to memory/sfdc-schema-discovery.json
    """
    desc = sf.Opportunity.describe()
    fields = [{"name": f["name"], "label": f["label"], "type": f["type"],
               "custom": f["custom"], "picklistValues": [v["value"] for v in f.get("picklistValues", [])]}
              for f in desc["fields"]]

    output = {
        "object": "Opportunity",
        "field_count": len(fields),
        "custom_fields": [f for f in fields if f["custom"]],
        "all_fields": fields,
        "discovered_at": datetime.utcnow().isoformat(),
    }

    out_path = MEMORY_DIR / "sfdc-schema-discovery.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"Schema discovery saved to {out_path}")
    print(f"Total fields: {len(fields)}, Custom: {len(output['custom_fields'])}")

    # Highlight fields likely relevant to CFO analytics
    relevant_keywords = ["competitor", "forecast", "arr", "acv", "tcv", "renewal",
                         "churn", "segment", "territory", "partner", "channel",
                         "discount", "product", "region"]
    highlights = [f for f in fields
                  if any(kw in f["name"].lower() or kw in f["label"].lower()
                         for kw in relevant_keywords)]
    print(f"\nRelevant fields for CFO analytics ({len(highlights)}):")
    for f in highlights:
        print(f"  {f['name']} ({f['label']}) — {f['type']}")

    return output


# ---------------------------------------------------------------------------
# Formatting (Markdown for email/briefing)
# ---------------------------------------------------------------------------

def fmt_currency(amount):
    """Format as $1.2M or $450K."""
    if amount is None:
        return "$0"
    if amount >= 1_000_000:
        return f"${amount/1_000_000:.1f}M"
    if amount >= 1_000:
        return f"${amount/1_000:.0f}K"
    return f"${amount:,.0f}"


def format_pipeline_markdown(data):
    """Markdown table of open pipeline by stage."""
    lines = ["## Pipeline Summary (Open Opportunities)\n"]

    # Stage summary table
    rows = []
    total_amount = 0
    total_count = 0
    for rec in data["summary"]:
        stage = rec.get("StageName", "Unknown")
        count = rec.get("OppCount", 0)
        amount = rec.get("TotalAmount", 0) or 0
        avg = rec.get("AvgAmount", 0) or 0
        rows.append([stage, count, fmt_currency(amount), fmt_currency(avg)])
        total_amount += amount
        total_count += count

    rows.append(["**TOTAL**", f"**{total_count}**", f"**{fmt_currency(total_amount)}**", ""])
    lines.append(tabulate(rows, headers=["Stage", "Deals", "Total", "Avg Deal"],
                          tablefmt="pipe"))

    # Top deals
    lines.append("\n### Top 10 Open Deals\n")
    deal_rows = []
    for d in data["top_deals"][:10]:
        acct = d.get("Account", {}).get("Name", "—") if d.get("Account") else "—"
        deal_rows.append([
            d.get("Name", "")[:40],
            acct[:25],
            d.get("StageName", ""),
            fmt_currency(d.get("Amount")),
            d.get("CloseDate", "")[:10],
            d.get("Owner", {}).get("Name", "—") if d.get("Owner") else "—",
        ])
    lines.append(tabulate(deal_rows,
                          headers=["Opportunity", "Account", "Stage", "Amount", "Close Date", "Owner"],
                          tablefmt="pipe"))

    return "\n".join(lines)


def format_competitive_markdown(data):
    """Markdown summary of competitive deals."""
    lines = ["## Competitive Deal Analysis\n"]

    if data.get("error"):
        lines.append(f"**Schema issue:** {data['error']}")
        lines.append("Run `python3 sfdc_analytics.py --mode discover` to find the correct field.\n")
        return "\n".join(lines)

    records = data["records"]
    if not records:
        lines.append("No competitive deals found in the current dataset.\n")
        return "\n".join(lines)

    # Aggregate by competitor
    comp_stats = {}
    source_field = data["source"]
    for rec in records:
        # Determine competitor name based on data source
        if source_field == "OpportunityCompetitor":
            comp_name = rec.get("CompetitorName", "Unknown")
            opp = rec.get("Opportunity", {})
            amount = opp.get("Amount", 0) or 0
            is_won = opp.get("IsWon", False)
            is_closed = opp.get("IsClosed", False)
        else:
            comp_name = rec.get(source_field, "Unknown")
            amount = rec.get("Amount", 0) or 0
            is_won = rec.get("IsWon", False)
            is_closed = rec.get("IsClosed", False)

        if comp_name not in comp_stats:
            comp_stats[comp_name] = {"total": 0, "won": 0, "lost": 0, "open": 0,
                                     "won_amount": 0, "lost_amount": 0, "open_amount": 0}
        comp_stats[comp_name]["total"] += 1
        if not is_closed:
            comp_stats[comp_name]["open"] += 1
            comp_stats[comp_name]["open_amount"] += amount
        elif is_won:
            comp_stats[comp_name]["won"] += 1
            comp_stats[comp_name]["won_amount"] += amount
        else:
            comp_stats[comp_name]["lost"] += 1
            comp_stats[comp_name]["lost_amount"] += amount

    # Table: competitor | open deals | open $ | won | won $ | lost | lost $ | win rate
    rows = []
    for comp in COMPETITORS:
        s = comp_stats.get(comp, {"total": 0, "won": 0, "lost": 0, "open": 0,
                                   "won_amount": 0, "lost_amount": 0, "open_amount": 0})
        decided = s["won"] + s["lost"]
        win_rate = f"{s['won']/decided*100:.0f}%" if decided > 0 else "—"
        rows.append([comp, s["open"], fmt_currency(s["open_amount"]),
                     s["won"], fmt_currency(s["won_amount"]),
                     s["lost"], fmt_currency(s["lost_amount"]),
                     win_rate])

    lines.append(tabulate(rows,
                          headers=["Competitor", "Open", "Open $", "Won", "Won $",
                                   "Lost", "Lost $", "Win Rate"],
                          tablefmt="pipe"))

    return "\n".join(lines)


def format_winloss_markdown(data):
    """Markdown win/loss summary."""
    lines = [f"## Win/Loss Trends (Last {data['period_days']} Days)\n"]

    # Overall
    won_count = lost_count = won_amount = lost_amount = 0
    for rec in data["overall"]:
        if rec.get("IsWon"):
            won_count = rec.get("DealCount", 0)
            won_amount = rec.get("TotalAmount", 0) or 0
        else:
            lost_count = rec.get("DealCount", 0)
            lost_amount = rec.get("TotalAmount", 0) or 0

    total_decided = won_count + lost_count
    win_rate = f"{won_count/total_decided*100:.0f}%" if total_decided > 0 else "—"
    win_rate_amount = (f"{won_amount/(won_amount+lost_amount)*100:.0f}%"
                       if (won_amount + lost_amount) > 0 else "—")

    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Deals Won | {won_count} ({fmt_currency(won_amount)}) |")
    lines.append(f"| Deals Lost | {lost_count} ({fmt_currency(lost_amount)}) |")
    lines.append(f"| Win Rate (count) | {win_rate} |")
    lines.append(f"| Win Rate (amount) | {win_rate_amount} |")

    # By owner (top reps)
    lines.append("\n### Win Rate by Rep (Top 10)\n")
    owner_stats = {}
    for rec in data["by_owner"]:
        owner = rec.get("Owner", {}).get("Name", "Unknown") if isinstance(rec.get("Owner"), dict) else "Unknown"
        if owner not in owner_stats:
            owner_stats[owner] = {"won": 0, "lost": 0, "won_amt": 0, "lost_amt": 0}
        if rec.get("IsWon"):
            owner_stats[owner]["won"] = rec.get("DealCount", 0)
            owner_stats[owner]["won_amt"] = rec.get("TotalAmount", 0) or 0
        else:
            owner_stats[owner]["lost"] = rec.get("DealCount", 0)
            owner_stats[owner]["lost_amt"] = rec.get("TotalAmount", 0) or 0

    owner_rows = []
    for name, s in sorted(owner_stats.items(), key=lambda x: x[1]["won_amt"], reverse=True)[:10]:
        decided = s["won"] + s["lost"]
        wr = f"{s['won']/decided*100:.0f}%" if decided > 0 else "—"
        owner_rows.append([name, s["won"], s["lost"], wr,
                           fmt_currency(s["won_amt"]), fmt_currency(s["lost_amt"])])

    lines.append(tabulate(owner_rows,
                          headers=["Rep", "Won", "Lost", "Win %", "Won $", "Lost $"],
                          tablefmt="pipe"))

    return "\n".join(lines)


def format_forecast_markdown(data):
    """Markdown forecast accuracy table."""
    lines = ["## Forecast vs Actual (Last 4 Quarters)\n"]

    # Build a lookup: (FY, Q) -> {Commit: $, BestCase: $, Pipeline: $, ClosedWon: $}
    quarters = {}
    for rec in data["by_category"]:
        key = (rec.get("FiscalYr"), rec.get("FiscalQtr"))
        if key not in quarters:
            quarters[key] = {}
        cat = rec.get("ForecastCategory", "Omitted")
        quarters[key][cat] = rec.get("TotalAmount", 0) or 0

    for rec in data["actuals"]:
        key = (rec.get("FiscalYr"), rec.get("FiscalQtr"))
        if key not in quarters:
            quarters[key] = {}
        quarters[key]["Actual"] = rec.get("ClosedWon", 0) or 0

    rows = []
    for (fy, fq) in sorted(quarters.keys(), reverse=True):
        q = quarters[(fy, fq)]
        commit = q.get("Commit", 0)
        best = q.get("BestCase", 0)
        pipeline = q.get("Pipeline", 0)
        actual = q.get("Actual", 0)
        accuracy = f"{actual/commit*100:.0f}%" if commit > 0 else "—"
        rows.append([f"FY{fy} Q{fq}", fmt_currency(pipeline), fmt_currency(best),
                     fmt_currency(commit), fmt_currency(actual), accuracy])

    lines.append(tabulate(rows,
                          headers=["Quarter", "Pipeline", "Best Case", "Commit",
                                   "Actual Closed", "Commit Accuracy"],
                          tablefmt="pipe"))

    # Forecast accuracy trend note
    lines.append("\n*Commit Accuracy = Actual Closed Won / Commit Forecast at quarter close.*")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Daily Snapshot (for state tracking / trend detection)
# ---------------------------------------------------------------------------

def save_snapshot(sf):
    """Save today's pipeline state to memory/ for trend tracking."""
    pipeline = query_open_pipeline(sf)

    snapshot = {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "total_pipeline": sum((r.get("TotalAmount", 0) or 0) for r in pipeline["summary"]),
        "deal_count": sum((r.get("OppCount", 0) or 0) for r in pipeline["summary"]),
        "by_stage": {r.get("StageName", "?"): {
            "count": r.get("OppCount", 0),
            "amount": r.get("TotalAmount", 0) or 0
        } for r in pipeline["summary"]},
    }

    # Load existing history, append, keep last 365 days
    history = []
    if SNAPSHOT_FILE.exists():
        try:
            history = json.loads(SNAPSHOT_FILE.read_text())
        except json.JSONDecodeError:
            history = []

    # Remove entries older than 365 days
    cutoff = (datetime.utcnow() - timedelta(days=365)).strftime("%Y-%m-%d")
    history = [h for h in history if h.get("date", "") >= cutoff]
    history.append(snapshot)

    SNAPSHOT_FILE.write_text(json.dumps(history, indent=2))
    print(f"Snapshot saved: {fmt_currency(snapshot['total_pipeline'])} across {snapshot['deal_count']} deals")

    return snapshot


# ---------------------------------------------------------------------------
# Briefing Integration
# ---------------------------------------------------------------------------

def generate_briefing_section(sf):
    """
    Generate the SFDC section for the 6 AM daily briefing email.
    Returns a markdown string to be inserted into the briefing template.
    """
    sections = []
    sections.append("# Salesforce Pipeline Update\n")

    try:
        pipeline = query_open_pipeline(sf)
        sections.append(format_pipeline_markdown(pipeline))
    except Exception as e:
        sections.append(f"**Pipeline query failed:** {e}\n")

    try:
        competitive = query_competitive_deals(sf)
        sections.append(format_competitive_markdown(competitive))
    except Exception as e:
        sections.append(f"**Competitive query failed:** {e}\n")

    try:
        winloss = query_win_loss(sf, days_back=30)
        sections.append(format_winloss_markdown(winloss))
    except Exception as e:
        sections.append(f"**Win/loss query failed:** {e}\n")

    try:
        forecast = query_forecast_vs_actual(sf)
        sections.append(format_forecast_markdown(forecast))
    except Exception as e:
        sections.append(f"**Forecast query failed:** {e}\n")

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Cohesity Salesforce Analytics")
    parser.add_argument("--mode", choices=["pipeline", "competitive", "winloss",
                                           "forecast", "briefing", "snapshot", "discover"],
                        default="briefing", help="Analysis mode")
    parser.add_argument("--days", type=int, default=90, help="Lookback days for win/loss")
    parser.add_argument("--jwt", action="store_true", help="Use JWT bearer auth instead of refresh token")
    args = parser.parse_args()

    sf = connect_sfdc_jwt() if args.jwt else connect_sfdc()

    if args.mode == "discover":
        discover_schema(sf)
    elif args.mode == "pipeline":
        data = query_open_pipeline(sf)
        print(format_pipeline_markdown(data))
    elif args.mode == "competitive":
        data = query_competitive_deals(sf)
        print(format_competitive_markdown(data))
    elif args.mode == "winloss":
        data = query_win_loss(sf, days_back=args.days)
        print(format_winloss_markdown(data))
    elif args.mode == "forecast":
        data = query_forecast_vs_actual(sf)
        print(format_forecast_markdown(data))
    elif args.mode == "snapshot":
        save_snapshot(sf)
    elif args.mode == "briefing":
        print(generate_briefing_section(sf))


if __name__ == "__main__":
    main()
```

---

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
