---
name: snowflake-sql
description: >
  Execute SQL queries against Cohesity's Snowflake data warehouse.
  Pull ARR, churn, NRR, customer metrics on demand.
---

# Snowflake SQL Connector

## When to Use
- Eric asks for revenue, ARR, or customer count data
- ARR breakdown by segment (Enterprise, Mid-Market, SMB)
- Net Revenue Retention (NRR) trending over quarters
- Churn analysis by cohort or time period
- Revenue by product line (DataProtect, DataHawk, FortKnox, Turing)
- Board prep data pulls or QBR metric refreshes
- Ad-hoc SQL queries against the analytics warehouse

## Prerequisites
1. **Snowflake account credentials** stored in 1Password (Jarvis vault):
   - `SNOWFLAKE_ACCOUNT` — Cohesity account identifier (e.g., `cohesity.us-west-2`)
   - `SNOWFLAKE_USER` — service account username
   - `SNOWFLAKE_PASSWORD` — service account password
   - `SNOWFLAKE_WAREHOUSE` — analytics warehouse (e.g., `ANALYTICS_WH`)
   - `SNOWFLAKE_DATABASE` — target database (e.g., `COHESITY_ANALYTICS`)
   - `SNOWFLAKE_SCHEMA` — schema (e.g., `FINANCE` or `REVENUE`)
2. **Read-only analytics role** — Requires Cohesity IT to provision a `JARVIS_READONLY` role with SELECT on finance/revenue tables. Contact IT ServiceNow or Eric's IT liaison.
3. **Python library**: `pip install snowflake-connector-python`
4. **Network access**: VPN or allowlisted IP for Snowflake endpoint.

## Credential Retrieval
```bash
# Pull credentials from 1Password CLI
SNOWFLAKE_ACCOUNT=$(op read "op://Jarvis/Snowflake/account")
SNOWFLAKE_USER=$(op read "op://Jarvis/Snowflake/username")
SNOWFLAKE_PASSWORD=$(op read "op://Jarvis/Snowflake/password")
```

## Connection Setup
```python
import snowflake.connector
import os
import json

def get_snowflake_connection():
    """Establish read-only Snowflake connection."""
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "ANALYTICS_WH"),
        database=os.environ.get("SNOWFLAKE_DATABASE", "COHESITY_ANALYTICS"),
        schema=os.environ.get("SNOWFLAKE_SCHEMA", "FINANCE"),
        role="JARVIS_READONLY",
    )
    return conn

def run_query(sql, params=None):
    """Execute a read-only query and return rows as list of dicts."""
    conn = get_snowflake_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or [])
        columns = [col[0] for col in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        conn.close()
```

## Pre-Built Queries

### ARR by Customer Segment
```python
ARR_BY_SEGMENT = """
SELECT customer_segment, SUM(arr_amount) AS total_arr,
       COUNT(DISTINCT account_id) AS customer_count
FROM revenue.arr_snapshot
WHERE snapshot_date = CURRENT_DATE()
GROUP BY customer_segment
ORDER BY total_arr DESC
"""
```

### NRR Trending (Quarterly)
```python
NRR_TRENDING = """
SELECT fiscal_quarter,
       ROUND(ending_arr / beginning_arr * 100, 1) AS nrr_pct
FROM revenue.nrr_summary
WHERE fiscal_quarter >= DATEADD(quarter, -8, CURRENT_DATE())
ORDER BY fiscal_quarter
"""
```

### Churn by Cohort
```python
CHURN_BY_COHORT = """
SELECT cohort_quarter,
       COUNT(CASE WHEN churned = TRUE THEN 1 END) AS churned_count,
       COUNT(*) AS total_count,
       ROUND(churned_count / total_count * 100, 1) AS churn_rate_pct
FROM revenue.customer_cohorts
GROUP BY cohort_quarter
ORDER BY cohort_quarter
"""
```

### Customer Count
```python
CUSTOMER_COUNT = """
SELECT customer_segment, COUNT(DISTINCT account_id) AS active_customers
FROM revenue.arr_snapshot
WHERE snapshot_date = CURRENT_DATE() AND arr_amount > 0
GROUP BY customer_segment
"""
```

### Revenue by Product Line
```python
REVENUE_BY_PRODUCT = """
SELECT product_line, SUM(arr_amount) AS arr,
       ROUND(arr / SUM(arr) OVER () * 100, 1) AS pct_of_total
FROM revenue.arr_by_product
WHERE snapshot_date = CURRENT_DATE()
GROUP BY product_line
ORDER BY arr DESC
"""
```

## Workflow
1. Parse Eric's request to identify which metric(s) are needed.
2. Retrieve credentials from 1Password (or env vars if already loaded).
3. Select the appropriate pre-built query, or construct a custom one.
4. Execute via `run_query()` — all queries must be SELECT-only.
5. Format results as a markdown table or summary paragraph.
6. If board prep, combine multiple queries into a single briefing section.

## Error Handling
- **Authentication failure**: Check 1Password credentials are current; Snowflake passwords may rotate quarterly.
- **Role not found**: IT has not provisioned `JARVIS_READONLY` — escalate via ServiceNow.
- **Warehouse suspended**: Auto-resume is enabled, but if timeout occurs, retry after 30s.
- **Table not found**: Schema names may differ; query `INFORMATION_SCHEMA.TABLES` to discover available tables.
- **Network timeout**: Ensure VPN is connected or IP is allowlisted.

## Integration Points
- **Daily Briefing**: Can be called by the daily briefing cron to include fresh ARR/NRR numbers.
- **Board Deck Prep**: Feeds into board prep workflow for quarterly metrics.
- **Google Sheets Export**: Results can be pushed to Eric's tracking sheets via `gog` CLI.

## Safety
- All connections use the `JARVIS_READONLY` role — no writes possible.
- Never expose credentials in logs or output; use env vars or 1Password references only.
- Queries should include `LIMIT 10000` for ad-hoc exploratory queries to avoid runaway scans.
