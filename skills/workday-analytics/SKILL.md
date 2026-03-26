---
name: workday-analytics
description: >
  Cohesity Workday HR analytics. Headcount, budget vs actual,
  org structure, payroll cost trending.
---

# Workday HR Analytics

## When to Use
- Eric needs headcount data by department or location for board prep
- Budget vs actual analysis by cost center
- Open requisition counts and time-to-fill metrics
- Payroll cost trending for quarterly reviews
- Org structure lookups (who reports to whom, department sizes)
- Workforce planning and scenario modeling inputs

## Prerequisites
1. **Workday Integration System User (ISU)** — provisioned by Cohesity IT with read-only access to:
   - Headcount reports
   - Budget/compensation reports
   - Recruiting reports
   - Org hierarchy data
2. **RaaS (Report-as-a-Service) endpoints** — Cohesity IT must publish custom reports as REST endpoints. Each report gets a unique URL.
3. **Credentials** stored in 1Password (Jarvis vault):
   - `WORKDAY_RAAS_BASE_URL` — base tenant URL (e.g., `https://services1.myworkday.com/ccx/service/cohesity`)
   - `WORKDAY_ISU_USER` — integration system username (e.g., `ISU_Jarvis`)
   - `WORKDAY_ISU_PASSWORD` — integration system password
4. **Python library**: `pip install requests` (standard HTTP; no Workday-specific SDK needed)
5. **Network**: VPN or allowlisted IP; Workday blocks unapproved origins.

## Credential Retrieval
```bash
WORKDAY_RAAS_BASE_URL=$(op read "op://Jarvis/Workday/raas_base_url")
WORKDAY_ISU_USER=$(op read "op://Jarvis/Workday/username")
WORKDAY_ISU_PASSWORD=$(op read "op://Jarvis/Workday/password")
```

## Connection Setup
```python
import os
import requests
from requests.auth import HTTPBasicAuth

class WorkdayClient:
    """Client for Workday Report-as-a-Service (RaaS) REST API."""

    def __init__(self):
        self.base_url = os.environ["WORKDAY_RAAS_BASE_URL"]
        self.auth = HTTPBasicAuth(
            os.environ["WORKDAY_ISU_USER"],
            os.environ["WORKDAY_ISU_PASSWORD"],
        )
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({"Accept": "application/json"})

    def get_report(self, report_name, params=None):
        """Fetch a published RaaS report by name. Returns parsed JSON."""
        url = f"{self.base_url}/{report_name}"
        resp = self.session.get(url, params=params or {}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("Report_Entry", data)

    def get_report_csv(self, report_name, params=None):
        """Fetch report as CSV for large datasets."""
        url = f"{self.base_url}/{report_name}"
        headers = {"Accept": "text/csv"}
        resp = self.session.get(url, params=params or {}, headers=headers, timeout=60)
        resp.raise_for_status()
        return resp.text
```

## Pre-Built Report Queries

### Headcount by Department and Location
```python
def get_headcount(client):
    """Headcount breakdown by department and work location."""
    rows = client.get_report("Jarvis_Headcount_By_Dept_Location")
    # Expected fields: Department, Location, Headcount, FTE_Count
    summary = {}
    for row in rows:
        dept = row.get("Department", "Unknown")
        loc = row.get("Location", "Unknown")
        count = int(row.get("Headcount", 0))
        summary.setdefault(dept, {"total": 0, "locations": {}})
        summary[dept]["total"] += count
        summary[dept]["locations"][loc] = summary[dept]["locations"].get(loc, 0) + count
    return summary
```

### Budget vs Actual by Cost Center
```python
def get_budget_vs_actual(client, fiscal_year="FY2026"):
    """Compare budget to actual spend by cost center."""
    params = {"Fiscal_Year": fiscal_year}
    rows = client.get_report("Jarvis_Budget_vs_Actual", params)
    # Expected fields: Cost_Center, Budget_Amount, Actual_Amount, Variance
    results = []
    for row in rows:
        results.append({
            "cost_center": row.get("Cost_Center"),
            "budget": float(row.get("Budget_Amount", 0)),
            "actual": float(row.get("Actual_Amount", 0)),
            "variance": float(row.get("Variance", 0)),
            "variance_pct": round(float(row.get("Variance", 0)) / max(float(row.get("Budget_Amount", 1)), 1) * 100, 1),
        })
    return sorted(results, key=lambda x: abs(x["variance"]), reverse=True)
```

### Open Requisitions and Time-to-Fill
```python
def get_open_reqs(client):
    """Get open requisitions with time-to-fill metrics."""
    rows = client.get_report("Jarvis_Open_Reqs_TTF")
    # Expected fields: Req_ID, Job_Title, Department, Days_Open, Hiring_Manager
    return [{
        "req_id": row.get("Req_ID"),
        "title": row.get("Job_Title"),
        "department": row.get("Department"),
        "days_open": int(row.get("Days_Open", 0)),
        "hiring_manager": row.get("Hiring_Manager"),
    } for row in rows]

def get_ttf_summary(client):
    """Average time-to-fill by department."""
    reqs = get_open_reqs(client)
    dept_days = {}
    for r in reqs:
        dept_days.setdefault(r["department"], []).append(r["days_open"])
    return {dept: round(sum(days) / len(days), 1) for dept, days in dept_days.items()}
```

### Payroll Cost Trending
```python
def get_payroll_trending(client, periods=8):
    """Monthly payroll cost for the last N periods."""
    params = {"Periods": str(periods)}
    rows = client.get_report("Jarvis_Payroll_Trending", params)
    # Expected fields: Period, Total_Payroll, Headcount, Cost_Per_Employee
    return [{
        "period": row.get("Period"),
        "total_payroll": float(row.get("Total_Payroll", 0)),
        "headcount": int(row.get("Headcount", 0)),
        "cost_per_employee": float(row.get("Cost_Per_Employee", 0)),
    } for row in rows]
```

## Workflow
1. Parse Eric's request to identify which HR metric is needed.
2. Retrieve ISU credentials from 1Password or env vars.
3. Instantiate `WorkdayClient()`.
4. Call the appropriate report function.
5. Format results as markdown table or executive summary.
6. For board prep, combine headcount + budget + payroll into a single workforce section.

## RaaS Report Setup (One-Time, IT Task)
Cohesity IT must create and publish these custom reports in Workday:
- `Jarvis_Headcount_By_Dept_Location` — worker count grouped by supervisory org and location
- `Jarvis_Budget_vs_Actual` — plan vs spend by cost center, parameterized by fiscal year
- `Jarvis_Open_Reqs_TTF` — open job requisitions with days-open calculation
- `Jarvis_Payroll_Trending` — monthly payroll aggregates with headcount

Each report must be enabled as a web service (RaaS) and the ISU must be granted access via a security group.

## Error Handling
- **401 Unauthorized**: ISU credentials expired or incorrect — update in 1Password. Workday ISU passwords may be rotated by IT policy.
- **403 Forbidden**: ISU lacks the required security group membership — escalate to Cohesity IT/Workday admin.
- **404 Not Found**: Report name is wrong or report has not been published as RaaS — verify with IT.
- **Timeout**: Large reports may take >30s; use CSV format (`get_report_csv`) for datasets over 10K rows.
- **Empty results**: Check that report parameters (fiscal year, date range) are valid.
- **Schema changes**: If Workday field names change after a tenant update, the parsing will break — check field names against actual response keys.

## Integration Points
- **Board Prep**: Headcount and budget data feed into quarterly board deck generation.
- **Daily Briefing**: Can include headcount delta or open req count in the daily CFO briefing.
- **Snowflake**: For cross-referencing revenue-per-employee, combine Workday headcount with Snowflake ARR data.
- **Google Sheets**: Export formatted results to Eric's planning spreadsheets via `gog` CLI.
- **Incident Logging**: All API failures logged to `memory/incidents.jsonl` per workspace rules.
