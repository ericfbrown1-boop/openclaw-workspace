# Tax Automation Workflow Diagrams

Visual representations of the automation workflows

---

## Overall System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     TAX AUTOMATION SYSTEM                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ├─────────────────────────────┐
                              │                             │
                    ┌─────────▼────────┐         ┌─────────▼────────┐
                    │   CLOUD LAYER    │         │   LOCAL LAYER    │
                    └─────────┬────────┘         └─────────┬────────┘
                              │                             │
         ┌────────────────────┼────────────┐               │
         │                    │            │               │
    ┌────▼─────┐      ┌──────▼──────┐  ┌──▼───────┐  ┌────▼─────┐
    │ Dropbox  │      │   Claude    │  │  Zapier  │  │  Python  │
    │  Files   │      │  API/Desktop│  │  Zaps    │  │  Scripts │
    └────┬─────┘      └──────┬──────┘  └──┬───────┘  └────┬─────┘
         │                   │            │               │
         └───────────────────┴────────────┴───────────────┘
                              │
                    ┌─────────▼────────┐
                    │  YOUR TAX DATA   │
                    │   (Excel File)   │
                    └──────────────────┘
```

---

## Workflow 1: Statement Download Automation

```
START
  │
  ├─ User: "Download my Jan 2025 statements"
  │
  ▼
┌─────────────────────┐
│  Claude Desktop     │
│  + Playwright MCP   │
└──────────┬──────────┘
           │
           ├─ Opens Browser
           │
           ▼
    ┌─────────────┐
    │  Bank Site  │
    └──────┬──────┘
           │
           ├─ PAUSE: User logs in + 2FA
           │
           ▼
    ┌─────────────┐
    │ Navigate to │
    │ Statements  │
    └──────┬──────┘
           │
           ├─ For each month:
           │
           ▼
    ┌────────────────┐
    │ Download PDF   │
    │ Rename File    │
    │ Save to Dropbox│
    └──────┬─────────┘
           │
           ▼
┌──────────────────────┐
│ ~/Dropbox/2025 Taxes/│
│      Incoming/       │
│                      │
│ ✓ Chase_Checking_    │
│   2025-01.pdf        │
│ ✓ Chase_Checking_    │
│   2025-02.pdf        │
└──────────────────────┘
           │
           ▼
         DONE
```

---

## Workflow 2: Zapier File Organization

```
┌──────────────────────────────────────────────────────┐
│           DROPBOX FOLDER STRUCTURE                   │
└──────────────────────────────────────────────────────┘

BEFORE:
/2025 Taxes/
└── Incoming/
    ├── Chase_Checking_2025-01.pdf ← File arrives here
    ├── Fidelity_Investment_2025-Q1.pdf
    └── AmEx_Credit_2025-01.pdf

                    │
                    │ Zapier watches for new files
                    │ Trigger: New file in Incoming
                    ▼

          ┌─────────────────┐
          │  Zapier Action  │
          │                 │
          │ 1. Parse filename│
          │ 2. Extract bank  │
          │ 3. Extract type  │
          │ 4. Move to folder│
          └────────┬────────┘
                   │
                   ▼

AFTER:
/2025 Taxes/
├── Incoming/ (empty)
│
└── Processed/
    ├── Chase/
    │   ├── Checking/
    │   │   └── Chase_Checking_2025-01.pdf ← Moved here
    │   └── Savings/
    ├── Fidelity/
    │   └── Investment/
    │       └── Fidelity_Investment_2025-Q1.pdf ← Moved here
    └── AmEx/
        └── Credit/
            └── AmEx_Credit_2025-01.pdf ← Moved here
```

---

## Workflow 3: Statement Processing Pipeline

```
START: Run master_automation.py
│
├─ Scan Dropbox/Incoming/ folder
│
▼
┌────────────────────┐
│ Find all PDFs      │
│ ✓ Found 3 files    │
└─────────┬──────────┘
          │
          ├─ For each PDF:
          │
          ▼
   ┌──────────────────┐
   │  Step 1:         │
   │  Extract Text    │
   │  (pdfplumber)    │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │  Step 2:         │
   │  Send to Claude  │
   │  for Analysis    │
   └────────┬─────────┘
            │
            ├─ Claude extracts:
            │  • Institution name
            │  • Account number
            │  • Interest earned
            │  • Balances
            │  • Dates
            │
            ▼
   ┌──────────────────────────┐
   │  Step 3:                 │
   │  Save Extracted Data     │
   │  as JSON                 │
   │                          │
   │  {                       │
   │   "institution": "Chase",│
   │   "interest": 125.50,    │
   │   ...                    │
   │  }                       │
   └────────┬─────────────────┘
            │
            ▼
   ┌──────────────────┐
   │  Step 4:         │
   │  Open Excel      │
   │  (openpyxl)      │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │  Step 5:         │
   │  Find Account Row│
   │  in Spreadsheet  │
   └────────┬─────────┘
            │
            ├─ Search column A for "Chase Checking"
            ├─ Found at row 5
            │
            ▼
   ┌──────────────────┐
   │  Step 6:         │
   │  Cross-reference │
   │  with Claude     │
   └────────┬─────────┘
            │
            ├─ Compare extracted data with existing row
            ├─ Check for discrepancies
            ├─ Confidence: 98%
            │
            ▼
   ┌──────────────────┐
   │  Step 7:         │
   │  Update Excel Row│
   └────────┬─────────┘
            │
            ├─ Write to columns E, F, G, H, I
            ├─ Apply light blue fill to row
            ├─ Save with backup
            │
            ▼
   ┌──────────────────┐
   │  Step 8:         │
   │  Move PDF to     │
   │  Processed Folder│
   └────────┬─────────┘
            │
            ▼
     Next PDF or DONE

┌────────────────────────────────┐
│  FINAL RESULT:                 │
│                                │
│  Excel Updated:                │
│  Row 5: ■ Light Blue (complete)│
│                                │
│  Files Organized:              │
│  ✓ All PDFs in Processed/     │
│                                │
│  Logs Created:                 │
│  ✓ automation_20250208.log    │
│                                │
│  Backups Created:              │
│  ✓ Index_backup_20250208.xlsx │
└────────────────────────────────┘
```

---

## Workflow 4: Excel Update Detail

```
┌─────────────────────────────────────────────────────────┐
│              EXCEL SPREADSHEET STRUCTURE                │
│                                                         │
│  Row │  A        │ B      │ C    │ D      │ E    │ F   │
│  ────┼───────────┼────────┼──────┼────────┼──────┼─────┤
│   1  │ Account   │ Bank   │ Acct#│ Type   │ Int. │ Div.│
│  ────┼───────────┼────────┼──────┼────────┼──────┼─────┤
│   2  │ Checking  │ Chase  │ 1234 │ Check  │      │     │
│   3  │ Savings   │ Chase  │ 5678 │ Save   │      │     │
│   4  │ Investment│ Fidelity│ 9012│ Invest │      │     │
│   5  │ Credit    │ AmEx   │ 3456 │ Credit │      │     │
└─────────────────────────────────────────────────────────┘

BEFORE UPDATE (Row 2):
┌───────────┬────────┬──────┬────────┬──────┬─────┐
│ Checking  │ Chase  │ 1234 │ Check  │      │     │ ← Empty
└───────────┴────────┴──────┴────────┴──────┴─────┘

                      │
                      │ Python script:
                      │ 1. Finds row (row 2)
                      │ 2. Writes extracted data
                      │ 3. Applies light blue fill
                      ▼

AFTER UPDATE (Row 2):
┌───────────┬────────┬──────┬────────┬────────┬─────┐
│ Checking  │ Chase  │ 1234 │ Check  │ 125.50 │ 0.00│ ■ Light Blue
└───────────┴────────┴──────┴────────┴────────┴─────┘
                                        ▲        ▲
                                        │        │
                              Interest  │   Dividend
                              from      │   income
                              statement │
```

---

## Workflow 5: Data Flow Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    DATA FLOW DIAGRAM                       │
└────────────────────────────────────────────────────────────┘

[Bank Websites] ─────┐
                     │
                     ├─ Playwright MCP
                     │
                     ▼
              ┌─────────────┐
              │   PDFs      │
              │  (Raw Data) │
              └──────┬──────┘
                     │
                     │ Dropbox Sync
                     │
                     ▼
              ┌─────────────┐
              │  Dropbox    │
              │  /Incoming  │
              └──────┬──────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
    ┌──────────┐          ┌─────────┐
    │  Zapier  │          │ Python  │
    │  Move    │          │ Extract │
    │  Files   │          │  Text   │
    └────┬─────┘          └────┬────┘
         │                     │
         ▼                     │
    [Processed/               │
     Organized]                │
                               │
                               ▼
                        ┌─────────────┐
                        │   Claude    │
                        │   Analyze   │
                        └──────┬──────┘
                               │
                               ├─ Structured JSON
                               │
                               ▼
                        ┌─────────────┐
                        │   Python    │
                        │   Update    │
                        │   Excel     │
                        └──────┬──────┘
                               │
                               ▼
                        ┌─────────────┐
                        │ Excel File  │
                        │ (Updated +  │
                        │  Formatted) │
                        └──────┬──────┘
                               │
                               ├─ Backup to Archive
                               │
                               ▼
                        ┌─────────────┐
                        │  Summary    │
                        │  Report     │
                        │ (Markdown)  │
                        └─────────────┘
                               │
                               ▼
                        [Ready for
                         Accountant]
```

---

## Workflow 6: Error Handling Flow

```
START: Process statement
│
▼
┌──────────────────┐
│  Extract Text    │
└────────┬─────────┘
         │
         ├─ SUCCESS? ────┐
         │               │
         NO              YES
         │               │
         ▼               ▼
    ┌─────────┐    ┌─────────────┐
    │ Try OCR │    │ Send to     │
    └────┬────┘    │ Claude      │
         │         └──────┬──────┘
         ├─ SUCCESS? ────┐│
         │               ││
         NO              YES
         │               ││
         ▼               ▼▼
    ┌──────────────┐  ┌────────────────┐
    │ Flag for     │  │ Parse JSON     │
    │ Manual       │  └────────┬───────┘
    │ Review       │           │
    └──────────────┘           ├─ VALID? ───┐
                               │             │
                               NO            YES
                               │             │
                               ▼             ▼
                          ┌──────────┐  ┌──────────┐
                          │ Log Error│  │ Find Row │
                          │ Continue │  │ in Excel │
                          └──────────┘  └────┬─────┘
                                             │
                                             ├─ FOUND? ──┐
                                             │           │
                                             NO          YES
                                             │           │
                                             ▼           ▼
                                        ┌─────────┐  ┌────────┐
                                        │ Create  │  │ Update │
                                        │ New Row?│  │  Row   │
                                        └─────────┘  └───┬────┘
                                                         │
                                                         ├─ SUCCESS?
                                                         │
                                                         YES
                                                         │
                                                         ▼
                                                    ┌─────────┐
                                                    │ Mark    │
                                                    │Complete │
                                                    └────┬────┘
                                                         │
                                                         ▼
                                                       DONE

ALL ERRORS LOGGED TO:
- logs/automation_YYYYMMDD.log
- Excel column: "Validation Status"
- Email notification (optional)
```

---

## Workflow 7: Weekly Automation Schedule

```
MONDAY
├─ 6:00 AM
│  └─ Zapier: Check for new statements
│
TUESDAY
├─ 6:00 AM
│  └─ Zapier: Auto-organize any new files
│
WEDNESDAY
├─ 6:00 AM
│  └─ Python: Run extraction on any unprocessed PDFs
│
THURSDAY
├─ 6:00 AM
│  └─ Python: Validate all Excel data
│     └─ Send validation report email
│
FRIDAY
├─ 6:00 AM
│  └─ Python: Generate weekly summary
│
SATURDAY
├─ 10:00 AM
│  └─ Manual: Review flagged items
│     └─ Download any missing statements
│
SUNDAY
├─ Rest day
└─ System backup runs automatically
```

---

## Workflow 8: Security & Backup Flow

```
┌─────────────────────────────────────────────────┐
│           SECURITY & BACKUP STRATEGY            │
└─────────────────────────────────────────────────┘

REAL-TIME:
│
├─ Every File Operation
│  └─ Logged to: logs/operations.log
│
DAILY:
│
├─ 11:00 PM
│  └─ Automated Backup
│     ├─ Copy Excel to /Archive/
│     ├─ Timestamp: Index_YYYYMMDD.xlsx
│     └─ Keep last 30 days
│
WEEKLY:
│
├─ Sunday 2:00 AM
│  └─ Full System Backup
│     ├─ Dropbox → External Drive
│     ├─ Scripts → GitHub (private repo)
│     └─ Config → Encrypted archive
│
MONTHLY:
│
├─ 1st of Month
│  └─ Off-site Backup
│     └─ Archive → Cloud storage (encrypted)

ENCRYPTION:
│
├─ API Keys: .env file (not in git)
├─ Credentials: OS Keychain
└─ Sensitive PDFs: Optional GPG encryption

ACCESS CONTROL:
│
├─ Dropbox: 2FA enabled
├─ Claude API: Usage limits set
├─ Zapier: API key rotated quarterly
└─ System: Full disk encryption
```

---

## Workflow 9: Monthly Tax Prep Cycle

```
MONTH VIEW (e.g., February 2025)

Week 1:
│
├─ Days 1-7
│  └─ Statements become available from banks
│     └─ Usually 1-5 days after month end
│
Week 2:
│
├─ Days 8-14
│  ├─ Download all available statements
│  │  └─ Claude + Playwright automation
│  │
│  ├─ Auto-process through pipeline
│  │  └─ Extract → Validate → Excel
│  │
│  └─ Review flagged items
│     └─ Fix any automation errors
│
Week 3:
│
├─ Days 15-21
│  ├─ Download any late statements
│  │
│  ├─ Run validation checks
│  │  └─ Compare with previous months
│  │
│  └─ Generate monthly summary
│
Week 4:
│
├─ Days 22-28
│  ├─ Final review and cleanup
│  │
│  ├─ Update year-to-date totals
│  │
│  └─ Backup everything
│
END OF MONTH:
└─ All data for month complete ✓

YEAR VIEW:

Jan │ ████████████ │ Statements processed
Feb │ ████████████ │
Mar │ ████████████ │
Apr │ ████████████ │
May │ ████████████ │
Jun │ ████████████ │
Jul │ ████████████ │
Aug │ ████████████ │
Sep │ ████████████ │
Oct │ ████████████ │
Nov │ ████████████ │
Dec │ ████████████ │
    │
    └─ January 2026: Generate annual summary
       └─ Send to accountant
       └─ File taxes by April 15
```

---

## Workflow 10: Human-in-the-Loop Decision Points

```
                    ┌────────────────┐
                    │  AUTOMATION    │
                    │  STARTS HERE   │
                    └───────┬────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Download      │
                    │ Statement?    │
                    └───────┬───────┘
                            │
                ┌───────────┼───────────┐
                │                       │
         [AUTOMATED]              [HUMAN INPUT]
         Browser opens            Login + 2FA
                │                       │
                └───────────┬───────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ PDF → Text    │
                    │ Extraction    │
                    └───────┬───────┘
                            │
                     [AUTOMATED]
                            │
                            ▼
                    ┌───────────────┐
                    │ Claude        │
                    │ Analysis      │
                    └───────┬───────┘
                            │
                ┌───────────┴───────────┐
                │                       │
         Confidence > 95%         Confidence < 95%
                │                       │
         [AUTOMATED]              [HUMAN REVIEW]
                │                  "Does this look right?"
                │                       │
                └───────────┬───────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Excel Update  │
                    └───────┬───────┘
                            │
                ┌───────────┴───────────┐
                │                       │
         No Conflicts             Discrepancy Found
                │                       │
         [AUTOMATED]              [HUMAN DECISION]
         Mark complete            "Override or Skip?"
                │                       │
                └───────────┬───────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  COMPLETE     │
                    └───────────────┘

HUMAN INTERVENTION POINTS:
━━━━━━━━━━━━━━━━━━━━━━━━━
1. Bank Login + 2FA        (Required, ~2 min each)
2. Low Confidence Extract  (Optional, review recommended)
3. Data Discrepancy        (Required, must resolve)
4. Missing Statement       (Required, manual download)
5. Final Report Review     (Required, before sending to accountant)

AUTOMATION LEVEL: 80-90%
HUMAN TIME: 3-5 hours (vs 15-20 hours manual)
```

---

## Summary: Complete System Overview

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃        2025 TAX AUTOMATION SYSTEM OVERVIEW         ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

INPUT SOURCES:
├─ Multiple Banks
├─ Investment Accounts
└─ Credit Card Statements

          ↓ (Download via Playwright)

STAGE 1: ACQUISITION
├─ Tool: Claude Desktop + Playwright MCP
├─ Time: 15-30 min
└─ Output: PDFs in Dropbox/Incoming

          ↓ (Trigger: New file arrives)

STAGE 2: ORGANIZATION
├─ Tool: Zapier
├─ Time: Real-time (< 1 min)
└─ Output: PDFs in Processed/{Bank}/{Type}

          ↓ (Process: Extract text)

STAGE 3: EXTRACTION
├─ Tool: Python + pdfplumber
├─ Time: 5-10 min for batch
└─ Output: Raw text files

          ↓ (Analyze: Understand content)

STAGE 4: ANALYSIS
├─ Tool: Claude API
├─ Time: 2-3 min per statement
└─ Output: Structured JSON data

          ↓ (Validate: Check accuracy)

STAGE 5: VALIDATION
├─ Tool: Claude + Python
├─ Time: 1-2 min per statement
└─ Output: Confidence scores, error flags

          ↓ (Update: Write to Excel)

STAGE 6: INTEGRATION
├─ Tool: Python + openpyxl
├─ Time: < 1 min per row
└─ Output: Updated Excel with light blue fills

          ↓ (Backup: Preserve data)

STAGE 7: BACKUP
├─ Tool: Python + Dropbox
├─ Time: < 1 min
└─ Output: Timestamped backups

          ↓ (Summarize: Generate report)

STAGE 8: REPORTING
├─ Tool: Claude API
├─ Time: 2-3 min
└─ Output: Markdown summary for accountant

          ↓

FINAL OUTPUT:
├─ ✓ Complete Excel spreadsheet
├─ ✓ All statements organized
├─ ✓ Backups created
├─ ✓ Summary report ready
└─ ✓ Ready for accountant

TIME SAVED: 12-17 hours per tax season
ACCURACY: 95%+ with human oversight
COST: ~$62/month (only during tax prep)
ROI: Break-even in first year
```

---

## Legend

```
Symbols Used:
─────────────
│  = Sequential flow
├─ = Branch/option
└─ = End of branch
▼  = Direction indicator
┌─ = Box top
└─ = Box bottom
■  = Filled/completed
□  = Empty/incomplete
✓  = Success/complete
✗  = Error/failed
[AUTOMATED] = No human input needed
[HUMAN INPUT] = Requires human action
```

---

**These diagrams are conceptual. Your actual workflow may vary based on:**
- Number of accounts
- Bank websites (some are easier to automate)
- Your Excel spreadsheet structure
- Comfort level with automation

**Refer to the main guide for detailed implementation instructions.**
