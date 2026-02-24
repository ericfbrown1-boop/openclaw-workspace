# 2025 Tax Tracking Sheet - Setup Report
**Generated:** February 9, 2026  
**For:** Eric Brown (ericfbrown1@gmail.com)

---

## ✅ COMPLETED TASKS

### 1. Gmail Email Search
- **Date Range:** January 1, 2025 - February 9, 2026
- **Emails Searched:** All Mail folder
- **Keywords Used:** 17 tax-related keyword groups
- **Total Items Found:** 120 tax-related emails

### 2. Files Generated
- ✓ `tax_emails_2025.json` - Complete raw data (120 items)
- ✓ `Income_Tax_Tracking_Items.csv` - Ready for Google Sheets import
- ✓ `TAX_SHEET_SETUP_REPORT.md` - This comprehensive report

---

## 📊 FINDINGS SUMMARY

### Items Found by Category

| Category | Count | Status |
|----------|-------|--------|
| Other Tax Item | 99 | ⚠️ Needs manual review |
| Farm Expense | 7 | ✓ Good |
| Charitable Donation | 4 | ✓ Good |
| 1099-DIV Dividend Income | 3 | ✓ Good |
| Professional Fees | 2 | ✓ Good |
| Business Travel | 2 | ✓ Good |
| W-2 Wage Income | 1 | ⚠️ Expected 2+ (Cohesity, Informatica) |
| 1099-B Broker Statement | 1 | ⚠️ Expected more |
| Property Tax | 1 | ⚠️ Should have 3 properties |

---

## 🎯 KEY TAX ITEMS IDENTIFIED

### ✅ FOUND - Income Items
- **W-2:** Cohesity (2024 W-2 forwarded 2/8/2026)
- **1099-INT:** E*Trade (3 forms available 1/31/2026)
- **1099-B:** E*Trade (2024 Form ready 3/3/2025)
- **Rental Income:** (Search may have missed some)
- **Farm Income:** (No explicit items found - check manually)

### ✅ FOUND - Expense Items
- **Farm Expenses:**
  - Agrivine: Invoice 6434 (1/31/25), Invoice 6497 (5/17/25), + others
  - Total Agrivine invoices: 7
- **Charitable Donations:** 4 items including Series A Operating Agreement (DocuSign)
- **Business Travel:** 2 American Airlines trips to Traverse City (June 2025)
- **Professional Fees:** 2 GLG consultation requests (Informatica)

### ⚠️ POTENTIALLY MISSING - Need Manual Check

#### Income Items
- [ ] **W-2 - Informatica** (not found in search)
- [ ] **1099 forms from:**
  - [ ] Morgan Stanley (only found 3 general emails)
  - [ ] Bernstein (found 68 emails but none clearly tax forms)
  - [ ] Banks (interest income)
- [ ] **Rental Income statements:**
  - [ ] 3469 Old Mission Road
  - [ ] 100 Main Street Los Altos
- [ ] **Farm Income/Sales:**
  - [ ] 3553 Old Mission Road (cherries, pears, grapes)
  - [ ] No crop sale records found
- [ ] **Pension/Retirement:** Pillsbury distributions

#### Expense Items
- [ ] **More Farm Expenses:**
  - [ ] Manigold Orchards (found 2 mentions, need invoices)
  - [ ] Ginops (found 1 mention)
  - [ ] Equipment purchases
  - [ ] Farm supplies
- [ ] **Rental Property Expenses:**
  - [ ] Soper Services (not found)
  - [ ] Repairs/maintenance for 3469 Old Mission
  - [ ] Repairs/maintenance for 100 Main Street
- [ ] **Property Tax bills:**
  - [ ] 3469 Old Mission Road
  - [ ] 3553 Old Mission Road
  - [ ] 100 Main Street Los Altos
  - Only found 1 Nevada property tax mention
- [ ] **Mortgage Interest:**
  - [ ] Wells Fargo statements
  - [ ] Morgan Stanley statements
- [ ] **Insurance:**
  - [ ] Farm insurance
  - [ ] Rental property insurance

---

## 🚀 NEXT STEPS - CREATE GOOGLE SHEET

### Option 1: Manual Import (Simplest - 5 minutes)

1. **Create Google Sheet:**
   - Go to: https://sheets.google.com
   - Click "+ Blank spreadsheet"
   - Name it: "Income Tax Tracking Items"

2. **Import CSV:**
   - File > Import
   - Upload tab
   - Select: `Income_Tax_Tracking_Items.csv`
   - Import location: "Replace current sheet"
   - Separator type: "Comma"
   - Click "Import data"

3. **Format (optional but recommended):**
   - Row 1: Make header row bold, background color
   - Column A: Format as Date
   - Freeze Row 1: View > Freeze > 1 row
   - Auto-resize columns: Double-click column borders

4. **Share:**
   - Click "Share" button
   - Add: ericfbrown1@gmail.com
   - Permission: "Editor"
   - Click "Send"

5. **Done!** ✓

### Option 2: Automated via Google Sheets API (Requires Setup)

If you want to automate this:

1. Install Python libraries:
   ```bash
   pip3 install google-api-python-client google-auth-oauthlib
   ```

2. Set up OAuth credentials:
   - Go to: https://console.cloud.google.com/apis/credentials
   - Create OAuth 2.0 Client ID (Desktop app)
   - Download as `credentials.json`

3. Run the script:
   ```bash
   python3 create_google_sheet.py
   ```

This will:
- Authenticate with Google
- Create the spreadsheet
- Populate with all 120 items
- Format headers
- Share with your email

---

## 📝 RECOMMENDED FOLLOW-UP ACTIONS

### 1. Manual Email Checks (High Priority)

Search Gmail manually for these specific items:

**Missing Tax Forms:**
```
subject:(W-2 OR "Form W-2") from:informatica after:2024/12/31
subject:(1099) from:"morgan stanley" after:2024/12/31
subject:(1099) from:bernstein after:2024/12/31
subject:("property tax" OR "tax bill") after:2025/01/01
subject:("mortgage interest" OR "form 1098") after:2024/12/31
```

**Rental Property:**
```
subject:("3469 Old Mission" OR "100 Main Street") after:2025/01/01
from:tenant OR from:property OR from:rent after:2025/01/01
```

**Farm Income/Expenses:**
```
subject:("3553 Old Mission" OR farm OR cherry OR pear OR grape) after:2025/01/01
from:manigold OR from:ginops after:2025/01/01
subject:(equipment OR supply) farm after:2025/01/01
```

### 2. Check Physical Mail / Other Sources

Some tax documents may arrive by mail or be available on institution websites:

- [ ] **Morgan Stanley** - Log in to portal, download 1099 forms
- [ ] **Bernstein** - Check client portal for tax forms
- [ ] **Informatica** - Check ADP or payroll portal for W-2
- [ ] **County Tax Assessor** - Property tax bills (may be mailed)
- [ ] **Farm Sales** - Check bank deposits or sales records
- [ ] **Rental Income** - Check bank deposits from tenants

### 3. Review the "Other Tax Item" Category

The search found 99 items categorized as "Other Tax Item" because they mentioned relevant keywords but weren't clearly tax forms. Review these manually:

- Many Cohesity mentions (job postings, news) - NOT tax related
- Many Bernstein emails (likely client correspondence) - may contain tax info
- Morgan Stanley emails - need manual review
- Check `tax_emails_2025.json` for full list

---

## 📂 FILE LOCATIONS

All files saved to: `/Users/ericbrown/.openclaw/workspace/`

- **tax_emails_2025.json** - Raw data (all 120 items with full details)
- **Income_Tax_Tracking_Items.csv** - Clean CSV for import
- **search_tax_emails_2025.py** - Search script (reusable)
- **create_tax_sheet_csv.py** - CSV generator script
- **create_google_sheet.py** - Automated Sheet creator script

---

## 🔍 SEARCH METHODOLOGY

### Keywords Used:
- **Employers:** W-2, W2, Cohesity, Informatica
- **Financial Institutions:** 1099, Morgan Stanley, Bernstein, E*Trade
- **Properties:** property tax, mortgage interest, 3469 Old Mission, 100 Main Street, 3553 Old Mission
- **Farm:** Agrivine, Manigold, Ginops, Soper
- **Other:** charitable, donation, Traverse City

### Limitations:
1. **Subject line only** - IMAP search limitations mean body text searches were less reliable
2. **Exact keyword matching** - Variations or misspellings may have been missed
3. **Date filtering** - Some emails from late 2024 may be relevant but not captured
4. **Attachments** - Search doesn't analyze attachment contents
5. **Classification** - Automated categorization may have errors

---

## 💡 TIPS FOR COMPLETING THE SHEET

### Review Each Item:
1. Click the Gmail link to open the original email
2. Verify the tax relevance
3. Update the "Type" if incorrectly classified
4. Add comments/questions in the last column
5. Delete items that aren't actually tax-related

### Add Missing Items:
1. As you find missing items manually, add new rows
2. Keep the same column structure
3. Use the Gmail search URL format: `https://mail.google.com/mail/u/0/#search/[term]`

### Prepare for Tax Filing:
1. Download actual tax forms (PDFs) from each institution
2. Save PDFs to organized folders (Income, Expenses, Deductions)
3. Use the spreadsheet as a checklist
4. Share with your tax preparer/accountant

---

## 📞 QUESTIONS?

If you need help with:
- Creating the Google Sheet
- Running the automated scripts
- Understanding any findings
- Additional search refinements

Just ask! 

---

**Report Generated:** Monday, February 9, 2026 at 9:30 AM PST  
**Search Duration:** ~2 minutes  
**Total Items Processed:** 120 emails from 2025 tax year

---

