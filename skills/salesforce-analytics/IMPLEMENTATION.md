# Salesforce Analytics — Implementation Details

> **Quick reference:** See [SKILL.md](SKILL.md) for prerequisites, auth setup, SOQL reference, and error handling.

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
