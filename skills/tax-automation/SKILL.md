---
name: tax-automation
description: >
  Multi-property tax tracking for Eric's real estate portfolio.
  Form F (agricultural), rental depreciation, estimated tax calculations.
---

# Tax & Accounting Automation

## When to Use
- Quarterly estimated tax (ES) payment reminders and calculations
- Rental income/expense tracking across properties
- Farm Form F agricultural deduction prep (vineyard, orchard)
- Depreciation schedule updates for rental properties
- Tax email scanning and categorization from Gmail
- Year-end tax document assembly for CPA

## Properties Tracked

| Property | Type | State | Notes |
|----------|------|-------|-------|
| 162 James Ave, Atherton CA | Primary Residence | CA | Property tax, mortgage interest |
| 3553 Old Mission Rd, Traverse City MI | Farm/Vineyard | MI | Form F agricultural deductions |
| 3469 Old Mission Rd, Traverse City MI | Rental | MI | Managed by Soper Services |
| 100 Main St, Los Altos CA | Rental | CA | Rental income/depreciation |

## Farm Vendors (Form F — 3553 Old Mission Rd)
- **Agrivine** — vineyard labor, pruning, harvest
- **Manigold Orchards** — cherry and pear tree maintenance, spraying
- **Ginops** — farm equipment rental and maintenance

## Data Sources
- **Gmail** (`gog` CLI) — scan for tax-related emails (1099s, K-1s, property tax bills, vendor invoices)
- **Google Sheets** — Income Tax Tracking Items sheet (`1Ua45Dw38A32RMo2L6IBc6NoC-hyQXGs4rZb_7uymLzg`)
- **Existing tax guides** — `2025_Tax_Automation_Comprehensive_Guide.md` in workspace
- **Legacy scripts** — `scripts/legacy/` (see integration section below)

## Quarterly ES Tax Reminders

Due dates for federal and CA/MI estimated tax payments:
- **Q1**: April 15
- **Q2**: June 15
- **Q3**: September 15
- **Q4**: January 15 (following year)

### Reminder Workflow
1. Check `memory/cron-state.json` for last ES reminder sent.
2. If within 14 days of a due date, generate a reminder with:
   - Federal ES voucher amount (from prior year safe harbor or CPA estimate)
   - CA FTB 540-ES amount
   - MI MI-1040ES amount (if applicable based on MI rental/farm income)
3. Post reminder via email or Slack (see `slack-teams-hub` skill).
4. Update cron state after delivery.

## Rental Income Tracking

### Gmail Scan for Rental Deposits
```python
import subprocess, json, re
from datetime import datetime, timedelta

def scan_rental_emails(days_back=30):
    """Scan Gmail for rental income notifications using gog CLI."""
    since = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")
    queries = [
        f"from:soper subject:rent after:{since}",           # Soper Services (3469 Old Mission)
        f"subject:rental payment subject:los altos after:{since}",  # 100 Main St
    ]
    results = []
    for q in queries:
        # Use gog CLI for Gmail search
        out = subprocess.run(
            ["gog", "gmail", "search", "--query", q, "--format", "json"],
            capture_output=True, text=True
        )
        if out.returncode == 0:
            messages = json.loads(out.stdout)
            for msg in messages:
                results.append({
                    "date": msg.get("date"),
                    "subject": msg.get("subject"),
                    "from": msg.get("from"),
                    "snippet": msg.get("snippet", ""),
                })
    return results
```

### Update Google Sheet
```python
def append_rental_to_sheet(property_name, amount, date, category="Rental Income"):
    """Append a rental income/expense row to the tax tracking sheet."""
    sheet_id = "1Ua45Dw38A32RMo2L6IBc6NoC-hyQXGs4rZb_7uymLzg"
    row_data = f"{date},{property_name},{category},{amount}"
    subprocess.run([
        "gog", "sheets", "append", "--spreadsheet-id", sheet_id,
        "--range", "Transactions!A:D", "--values", row_data
    ], check=True)
```

## Form F Agricultural Deductions (3553 Old Mission Rd)

Track expenses by vendor for Michigan Form F (Schedule of Farm Income/Loss):
- **Labor**: Agrivine invoices for vineyard work
- **Supplies & maintenance**: Manigold Orchards for orchard care
- **Equipment**: Ginops invoices for equipment rental
- **Property taxes**: Traverse City property tax on agricultural parcels
- **Insurance**: Farm liability and crop insurance

### Vendor Invoice Scan
```python
FARM_VENDORS = ["agrivine", "manigold", "ginops"]

def scan_farm_invoices(year=2026):
    """Scan Gmail for farm vendor invoices."""
    results = []
    for vendor in FARM_VENDORS:
        out = subprocess.run(
            ["gog", "gmail", "search", "--query",
             f"from:{vendor} OR subject:{vendor} after:{year}/01/01 before:{year}/12/31",
             "--format", "json"],
            capture_output=True, text=True
        )
        if out.returncode == 0:
            messages = json.loads(out.stdout)
            for msg in messages:
                results.append({"vendor": vendor, "date": msg.get("date"), "subject": msg.get("subject")})
    return results
```

## Depreciation Schedules

Rental properties use straight-line depreciation over 27.5 years (residential):
- **3469 Old Mission Rd** — basis, placed-in-service date, annual deduction
- **100 Main St, Los Altos** — basis, placed-in-service date, annual deduction

Track in the Google Sheet under a "Depreciation" tab. Update annually or when capital improvements are made.

## Workflow
1. **Daily/weekly scan**: Run Gmail scan for new tax-related emails (rental payments, vendor invoices, 1099s).
2. **Categorize**: Match emails to property and expense category.
3. **Record**: Append to Google Sheet tax tracking spreadsheet.
4. **Quarterly**: 14 days before ES due date, generate payment reminder with amounts.
5. **Year-end**: Compile Form F totals, rental P&L by property, depreciation schedules for CPA.

## Error Handling
- **Gmail auth failure**: Re-authenticate with `gog auth login` — see `skills/google-oauth-reauth/SKILL.md`.
- **Sheet write failure**: Check sheet permissions; Eric must share with the service account.
- **Missing vendor emails**: Some vendors mail paper invoices — flag for manual entry.
- **Multi-state complexity**: CA and MI have different rules; flag anything unusual for CPA review.

## Integration Points
- **Legacy scripts** (`scripts/legacy/`):
  - `subscription_tracker.py` — subscription cost tracking (overlaps with expense categorization)
  - `tax_email_scan.py`, `check-tax-emails.py`, `scan-tax-emails.py` — prior Gmail scanning implementations; reference for query patterns but use the workflow above for new runs
  - `add-tax-emails-to-sheet.py` — prior sheet integration; patterns reusable
  - `create_farm_tax_doc.py` — Form F document generation
- **Google Sheets** (`subscription_tracker.py` writes to the same subscription sheet)
- **Daily briefing**: Tax reminders can be included in the daily CFO briefing when ES dates approach.
- **Incident logging**: All failures logged to `memory/incidents.jsonl`.
