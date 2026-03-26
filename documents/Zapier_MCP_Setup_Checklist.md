# Zapier MCP Tax Automation Setup Checklist
## Quick Start Guide - Get Running in 14 Hours

---

## 📋 Pre-Setup Checklist

Before you begin, gather these:

- [ ] **Email addresses** for all accounts
- [ ] **Bank usernames and passwords** (you'll store these securely)
- [ ] **Credit card** for paid services (optional - can start free)
- [ ] **Mobile phone** (for 2FA)
- [ ] **4-6 hours of focused time** over 2 weeks

---

## Week 1: Foundation (4 hours)

### Day 1: Monday (1.5 hours)

#### Install Software

- [ ] Download Claude Desktop
  - Mac: https://claude.ai/download
  - Windows: https://claude.ai/download
  - [ ] Install and open Claude Desktop
  - [ ] Sign in with your Anthropic account (create if needed)

- [ ] Install Node.js
  ```bash
  # Download from https://nodejs.org/ (v18+)
  # Or use package manager:
  brew install node  # Mac
  # Or download installer for Windows
  ```
  - [ ] Verify installation:
    ```bash
    node --version  # Should show v18+
    npm --version   # Should show 9+
    ```

#### Create Folder Structure

- [ ] Open Dropbox (or create account at dropbox.com)
- [ ] Create folders:
  ```
  /2025 Taxes/
    /Statements/
      /Raw/
      /Chase/
      /BankOfAmerica/
      /WellsFargo/
      /Processed/
    /Income/
    /Expenses/
    /Backups/
    /Playbooks/
  ```

#### Create Secrets File

- [ ] Choose location for secrets:
  ```bash
  # Recommended:
  mkdir -p ~/.config/tax-automation
  cd ~/.config/tax-automation
  ```

- [ ] Create `.env` file:
  ```bash
  touch .env
  chmod 600 .env  # Secure permissions (Mac/Linux)
  ```

- [ ] Open in text editor:
  ```bash
  nano .env
  # Or use VS Code, TextEdit, Notepad, etc.
  ```

- [ ] Add template (don't fill in yet):
  ```bash
  # Bank Credentials
  CHASE_USERNAME=
  CHASE_PASSWORD=
  
  BOFA_USERNAME=
  BOFA_PASSWORD=
  
  WELLS_USERNAME=
  WELLS_PASSWORD=
  
  # API Keys (fill in later)
  NUTRIENT_DWS_API_KEY=
  ZAPIER_MCP_URL=
  ```

- [ ] Save and close

- [ ] Verify security:
  ```bash
  ls -la ~/.config/tax-automation/.env
  # Should show: -rw------- (only you can read)
  ```

---

### Day 2: Tuesday (1 hour)

#### Install Playwright MCP

- [ ] Install globally:
  ```bash
  npm install -g @executeautomation/playwright-mcp-server
  ```

- [ ] Install browsers:
  ```bash
  npx playwright install chromium
  # Wait for download (500-700 MB)
  ```

- [ ] Verify installation:
  ```bash
  npx @executeautomation/playwright-mcp-server --version
  ```

#### Configure Claude Desktop for Playwright

- [ ] Find config file location:
  ```bash
  # macOS:
  open ~/Library/Application\ Support/Claude/
  # Windows:
  # Navigate to %APPDATA%\Claude\
  ```

- [ ] Create or edit `claude_desktop_config.json`:
  ```json
  {
    "mcpServers": {
      "playwright": {
        "command": "npx",
        "args": [
          "-y",
          "@executeautomation/playwright-mcp-server",
          "--browser", "chromium",
          "--headless", "false",
          "--secrets", "/Users/YOURUSERNAME/.config/tax-automation/.env"
        ],
        "env": {
          "SANDBOX_PATH": "/Users/YOURUSERNAME/Dropbox/2025 Taxes/Statements/Raw"
        }
      }
    }
  }
  ```
  
  **IMPORTANT:** Replace `YOURUSERNAME` with your actual username!

- [ ] Save the file

- [ ] Completely quit Claude Desktop (Cmd+Q on Mac, Alt+F4 on Windows)

- [ ] Reopen Claude Desktop

#### Test Playwright MCP

- [ ] In Claude, type:
  ```
  Can you navigate to google.com and take a screenshot?
  ```

- [ ] Expected result: Browser opens, navigates to Google, screenshot appears

- [ ] ✅ If successful, Playwright MCP is working!
- [ ] ❌ If errors, see Troubleshooting section below

---

### Day 3: Wednesday (1 hour)

#### Sign Up for Nutrient DWS

- [ ] Go to: https://dashboard.nutrient.io/sign_up/
- [ ] Fill out form:
  - [ ] Email
  - [ ] Password
  - [ ] Company name (can use your name)
- [ ] Verify email (check inbox)
- [ ] Log into dashboard

#### Get API Key

- [ ] In Nutrient dashboard, click "API Keys"
- [ ] Click "Create New Key"
- [ ] Name it: "Tax Automation"
- [ ] Copy the API key (starts with `pdf_live_...`)
- [ ] **IMPORTANT:** Save this key - you can't view it again!

#### Add to Secrets File

- [ ] Open `.env` file:
  ```bash
  nano ~/.config/tax-automation/.env
  ```

- [ ] Add API key:
  ```bash
  NUTRIENT_DWS_API_KEY=pdf_live_YOUR_KEY_HERE
  ```

- [ ] Save and close

#### Install Nutrient MCP

- [ ] Install server:
  ```bash
  npm install -g @nutrient-sdk/dws-mcp-server
  ```

- [ ] Verify:
  ```bash
  npx @nutrient-sdk/dws-mcp-server --version
  ```

#### Update Claude Config

- [ ] Edit `claude_desktop_config.json` again
- [ ] Add Nutrient MCP (keep Playwright):
  ```json
  {
    "mcpServers": {
      "playwright": {
        "command": "npx",
        "args": [
          "-y",
          "@executeautomation/playwright-mcp-server",
          "--browser", "chromium",
          "--headless", "false",
          "--secrets", "/Users/YOURUSERNAME/.config/tax-automation/.env"
        ],
        "env": {
          "SANDBOX_PATH": "/Users/YOURUSERNAME/Dropbox/2025 Taxes/Statements/Raw"
        }
      },
      "nutrient-dws": {
        "command": "npx",
        "args": ["-y", "@nutrient-sdk/dws-mcp-server"],
        "env": {
          "NUTRIENT_DWS_API_KEY": "${NUTRIENT_DWS_API_KEY}",
          "SANDBOX_PATH": "/Users/YOURUSERNAME/Dropbox/2025 Taxes/Statements"
        }
      }
    }
  }
  ```

- [ ] Save, quit Claude Desktop, reopen

#### Test Nutrient MCP

- [ ] Create a test PDF (or use any PDF you have)
- [ ] Save it to: `~/Dropbox/2025 Taxes/Statements/test.pdf`
- [ ] In Claude, type:
  ```
  Use Nutrient to extract text from test.pdf and show me the first paragraph
  ```

- [ ] ✅ Success: Claude extracts and shows text
- [ ] ❌ Error: Check API key in .env file

---

### Day 4: Thursday (30 minutes)

#### Sign Up for Zapier

- [ ] Go to: https://zapier.com/sign-up
- [ ] Create account (free tier to start)
- [ ] Verify email

#### Create Zapier MCP Server

- [ ] Go to: https://mcp.zapier.com
- [ ] Click "+ New MCP Server"
- [ ] Choose client: **Claude**
- [ ] Name: "Tax Automation"
- [ ] Click "Create MCP Server"
- [ ] Copy the endpoint URL (looks like: `https://api.zapier.com/v1/mcp/abc123...`)

#### Add to Claude Config

- [ ] Edit `claude_desktop_config.json` one more time
- [ ] Add Zapier (keep previous MCPs):
  ```json
  {
    "mcpServers": {
      "playwright": { /* ... */ },
      "nutrient-dws": { /* ... */ },
      "zapier": {
        "url": "https://api.zapier.com/v1/mcp/YOUR_ENDPOINT_ID",
        "type": "http"
      }
    }
  }
  ```

- [ ] Save, restart Claude Desktop

#### Verify All MCPs Connected

- [ ] In Claude, type:
  ```
  Which MCP servers are you connected to?
  ```

- [ ] Expected response:
  ```
  I'm connected to:
  1. Playwright MCP (browser automation)
  2. Nutrient DWS MCP (PDF processing)
  3. Zapier MCP (app integrations)
  ```

- [ ] ✅ All three connected? Week 1 complete!

---

## Week 2: Configure First Bank (3 hours)

### Day 1: Monday (1.5 hours)

#### Choose Your First Bank

- [ ] Pick the simplest bank (recommended: Chase or Capital One)
- [ ] Make sure you know:
  - [ ] Username
  - [ ] Password
  - [ ] 2FA method (SMS, app, etc.)

#### Add Credentials to .env

- [ ] Open `.env` file
- [ ] Add bank credentials:
  ```bash
  # Example for Chase:
  CHASE_USERNAME=myemail@gmail.com
  CHASE_PASSWORD=MySecureP@ssw0rd
  CHASE_2FA_METHOD=app
  ```

- [ ] Save and close

#### Test Manual Login

- [ ] Open a browser manually
- [ ] Go to your bank's website
- [ ] Login with your credentials
- [ ] Complete 2FA
- [ ] Navigate to Statements section
- [ ] Note the exact steps (write them down)

#### Test with Claude

- [ ] In Claude:
  ```
  Using Playwright, navigate to chase.com and login using my credentials 
  from the secrets file. Use headless=false so I can watch. Pause after login 
  so I can approve 2FA.
  ```

- [ ] Watch the browser window open
- [ ] Verify it enters username and password
- [ ] When 2FA prompt appears, approve on your phone
- [ ] Once logged in, ask Claude:
  ```
  Take a screenshot of the homepage
  ```

- [ ] ✅ If you see your account homepage, login works!

---

### Day 2: Tuesday (1 hour)

#### Navigate to Statements

- [ ] In Claude:
  ```
  Navigate to the Statements or Documents section
  ```

- [ ] Watch it navigate
- [ ] If it gets stuck:
  ```
  The statements link is labeled "Documents". Try clicking that.
  ```

#### Download a Statement

- [ ] Find a recent statement (doesn't have to be current month yet)
- [ ] In Claude:
  ```
  Download the December 2024 checking account statement. 
  Save it as Chase_Checking_Dec2024.pdf in the Dropbox Raw folder.
  ```

- [ ] Wait for download
- [ ] Check Dropbox folder - file should appear

- [ ] ✅ If PDF downloaded correctly, you're done!

---

### Day 3: Wednesday (30 minutes)

#### Create Playbook

- [ ] Create file: `/2025 Taxes/Playbooks/chase-download.md`
- [ ] Write step-by-step instructions:
  ```markdown
  # Chase Bank Statement Download
  
  ## Steps:
  1. Navigate to chase.com
  2. Click "Sign In"
  3. Enter username from CHASE_USERNAME
  4. Click "Next"
  5. Enter password from CHASE_PASSWORD
  6. Click "Sign In"
  7. Wait for 2FA (I'll approve on phone)
  8. Once logged in, click "Documents & Statements" in menu
  9. Filter by account: Checking ending in 1234
  10. Filter by date: [SPECIFY MONTH/YEAR]
  11. Click the download icon for the statement
  12. Save to: ~/Dropbox/2025 Taxes/Statements/Raw/
  13. Filename format: Chase_Checking_[Month][Year].pdf
  
  ## Example:
  "Download January 2025 checking statement"
  Should save as: Chase_Checking_Jan2025.pdf
  ```

#### Test the Playbook

- [ ] In Claude:
  ```
  Follow the Chase download playbook in /2025 Taxes/Playbooks/ 
  to download January 2025 statement
  ```

- [ ] Verify it follows your steps
- [ ] Adjust playbook if needed

- [ ] ✅ When Claude can successfully download using the playbook, you're ready for Week 3!

---

## Week 3: Setup Zapier Workflows (3 hours)

### Day 1: Monday (1 hour)

#### Create Zap #1: Auto-Organize Files

**In Zapier:**

- [ ] Click "Create Zap"

**Step 1: Trigger**
- [ ] Choose app: **Dropbox**
- [ ] Choose trigger: **New File in Folder**
- [ ] Connect your Dropbox account
- [ ] Choose folder: `/2025 Taxes/Statements/Raw`
- [ ] File extension: `pdf`
- [ ] Click "Test trigger"
- [ ] Upload a test PDF to Raw folder
- [ ] Verify Zapier found it

**Step 2: Filter (Optional but Recommended)**
- [ ] Add step: **Filter**
- [ ] Condition: `(Filename contains "Chase") OR (Filename contains "BofA") OR (Filename contains "Wells")`

**Step 3: Action - Move File**
- [ ] Choose app: **Dropbox**
- [ ] Choose action: **Move File**
- [ ] Set up conditions:
  ```
  If filename contains "Chase":
    Move to: /2025 Taxes/Statements/Chase/
  
  If filename contains "BofA":
    Move to: /2025 Taxes/Statements/BankOfAmerica/
  
  If filename contains "Wells":
    Move to: /2025 Taxes/Statements/WellsFargo/
  ```
  
  **Note:** You may need to create multiple Zaps (one per bank) since Zapier doesn't support complex conditionals in free tier. Or use Zapier's "Paths" feature (available on paid plans).

**Step 4: Test**
- [ ] Upload `Chase_Test_Jan2025.pdf` to Raw folder
- [ ] Wait 1-2 minutes
- [ ] Check Chase folder - file should appear there
- [ ] ✅ If file moved correctly, turn on Zap

---

### Day 2: Tuesday (1 hour)

#### Create Google Sheet

- [ ] Go to: https://sheets.google.com
- [ ] Create new sheet: "2025 Tax Records"
- [ ] Create worksheet: "Income Summary"
- [ ] Add headers (Row 1):
  ```
  A: Date Processed
  B: Bank
  C: Account
  D: Month
  E: Year
  F: Deposits
  G: Withdrawals
  H: Interest
  I: Fees
  J: Net Change
  ```

- [ ] Format columns:
  - [ ] A: Date format
  - [ ] F-J: Currency format ($)

#### Create Zap #2: Update Spreadsheet

**In Zapier:**

- [ ] Click "Create Zap"

**Step 1: Trigger**
- [ ] Choose app: **Webhooks by Zapier**
- [ ] Choose trigger: **Catch Hook**
- [ ] Copy the webhook URL (you'll need this later)

**Step 2: Action**
- [ ] Choose app: **Google Sheets**
- [ ] Choose action: **Create Spreadsheet Row**
- [ ] Connect Google account
- [ ] Select spreadsheet: "2025 Tax Records"
- [ ] Select worksheet: "Income Summary"
- [ ] Map fields:
  ```
  Date Processed: {{zap_meta_human_now}}
  Bank: {{bank}}
  Account: {{account}}
  Month: {{month}}
  Year: {{year}}
  Deposits: {{deposits}}
  Withdrawals: {{withdrawals}}
  Interest: {{interest}}
  Fees: {{fees}}
  Net Change: (Leave blank - use formula in sheet)
  ```

**Step 3: Test with CURL**

- [ ] Open terminal
- [ ] Run:
  ```bash
  curl -X POST "YOUR_WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d '{
      "bank": "Chase",
      "account": "Checking",
      "month": "January",
      "year": 2025,
      "deposits": 7000.00,
      "withdrawals": 5123.45,
      "interest": 2.34,
      "fees": 0.00
    }'
  ```

- [ ] Check Google Sheets
- [ ] ✅ If row appeared, turn on Zap

---

### Day 3: Wednesday (1 hour)

#### Add Zap as Zapier MCP Tool

- [ ] Go to: https://mcp.zapier.com
- [ ] Click your "Tax Automation" server
- [ ] Click "+ Add Tool"
- [ ] Configure:
  - **App:** Webhooks by Zapier
  - **Action:** POST (the webhook Zap you created)
  - **Tool Name:** `update_income_spreadsheet`
  - **Description:** "Updates Google Sheets with bank statement data"
  - **Parameters:**
    ```json
    {
      "bank": {"type": "string", "required": true},
      "account": {"type": "string", "required": true},
      "month": {"type": "string", "required": true},
      "year": {"type": "number", "required": true},
      "deposits": {"type": "number", "required": true},
      "withdrawals": {"type": "number", "required": true},
      "interest": {"type": "number", "required": false},
      "fees": {"type": "number", "required": false}
    }
    ```

- [ ] Save tool

#### Test from Claude

- [ ] In Claude:
  ```
  Use the update_income_spreadsheet tool to add this data:
  Bank: Chase
  Account: Checking
  Month: January
  Year: 2025
  Deposits: 7000
  Withdrawals: 5000
  Interest: 2.34
  Fees: 0
  ```

- [ ] Check Google Sheets
- [ ] ✅ If new row appeared, Zapier MCP is working!

---

## Week 4: Add More Banks + Test (4 hours)

### Day 1: Monday (2 hours)

#### Add Bank of America

- [ ] Add credentials to `.env`:
  ```bash
  BOFA_USERNAME=myemail@gmail.com
  BOFA_PASSWORD=MySecureP@ssw0rd
  ```

- [ ] Create playbook: `/Playbooks/bofa-download.md`
- [ ] Test login manually
- [ ] Test with Claude
- [ ] Download one statement

#### Add Wells Fargo

- [ ] Add credentials to `.env`:
  ```bash
  WELLS_USERNAME=myemail@gmail.com
  WELLS_PASSWORD=MySecureP@ssw0rd
  ```

- [ ] Create playbook: `/Playbooks/wells-download.md`
- [ ] Test login manually
- [ ] Test with Claude
- [ ] Download one statement

#### Update Zapier Zap

- [ ] Edit Zap #1 (file organizer)
- [ ] Add conditions for new banks:
  - If filename contains "BofA" → move to BankOfAmerica folder
  - If filename contains "Wells" → move to WellsFargo folder

---

### Day 2: Tuesday (1 hour)

#### End-to-End Test

- [ ] Tell Claude:
  ```
  Download December 2024 statements from Chase, Bank of America, and Wells Fargo.
  Then process all PDFs, extract the data, and update my Google Sheet.
  ```

- [ ] Watch the process:
  1. [ ] Downloads 3 PDFs
  2. [ ] Zapier moves them to correct folders
  3. [ ] Claude processes PDFs with Nutrient
  4. [ ] Claude extracts data
  5. [ ] Zapier updates Google Sheets
  6. [ ] 3 new rows appear in sheet

- [ ] ✅ If everything works end-to-end, you're almost done!

#### Test Error Scenarios

- [ ] What if 2FA times out?
  ```
  Tell Claude: "If 2FA times out, pause and let me know"
  ```

- [ ] What if statement isn't available?
  ```
  Tell Claude: "If a statement isn't available, skip it and tell me which ones are missing"
  ```

- [ ] What if file already exists?
  ```
  Tell Claude: "Before downloading, check if the file already exists. If so, skip it."
  ```

---

### Day 3: Wednesday (1 hour)

#### Create Master Workflow Document

- [ ] Create: `/2025 Taxes/Playbooks/monthly-workflow.md`
- [ ] Write complete process:
  ```markdown
  # Monthly Tax Automation Workflow
  
  Run on 1st of each month for previous month's statements.
  
  ## Prompt to Claude:
  
  "Download [MONTH] [YEAR] statements from Chase, Bank of America, and Wells Fargo.
  Then process all PDFs, extract income data, and update my Google Sheet."
  
  ## What Claude will do:
  1. Login to each bank (you'll approve 2FA)
  2. Download PDFs to Raw folder
  3. Zapier auto-organizes files
  4. Claude processes PDFs with Nutrient
  5. Claude extracts totals
  6. Zapier updates Google Sheets
  7. Claude gives you summary
  
  ## Verify:
  - [ ] Check Google Sheets for 3 new rows
  - [ ] Check bank folders for new PDFs
  - [ ] Review totals for accuracy
  
  ## Backup:
  - [ ] Download copy of Google Sheets
  - [ ] Save to /2025 Taxes/Backups/
  ```

#### Final Test

- [ ] Run the complete workflow
- [ ] Time yourself (should be ~10 minutes including 2FA)
- [ ] Document any issues

#### Create Troubleshooting Notes

- [ ] Create: `/2025 Taxes/troubleshooting.md`
- [ ] Document any problems you encountered and solutions
- [ ] Keep this updated as you use the system

---

### Day 4: Thursday (15 minutes)

#### Final Checklist

- [ ] All 3 banks can download statements automatically
- [ ] PDFs auto-organize into correct folders
- [ ] Google Sheets updates correctly
- [ ] No errors in test run
- [ ] Playbooks documented
- [ ] Credentials secured (`.env` file permissions = 600)
- [ ] Backup strategy in place

#### Plan First Real Use

- [ ] Set calendar reminder for February 1st
- [ ] When reminder fires, run monthly workflow
- [ ] Process January 2025 statements

---

## 🎉 You're Done!

You now have a working no-code tax automation system!

### Next Steps:

1. **Use it monthly:** First of each month, download previous month's statements
2. **Refine as needed:** Update playbooks if banks change their websites
3. **Expand if desired:** Add more banks, more data fields, more automation

### Monthly Time Commitment:

- **Manual:** 45 minutes per month
- **With automation:** 5-10 minutes per month (mostly 2FA approvals)
- **Time saved:** ~35-40 minutes per month = 7-8 hours per year

---

## 🆘 Quick Troubleshooting

### Playwright MCP not working?

1. Check Node.js version: `node --version` (must be 18+)
2. Reinstall: `npm install -g @executeautomation/playwright-mcp-server`
3. Restart Claude Desktop completely
4. Check config file for typos

### Nutrient API not working?

1. Check API key: https://dashboard.nutrient.io
2. Verify key in `.env` file (no extra spaces)
3. Test: `echo $NUTRIENT_DWS_API_KEY`
4. Regenerate key if needed

### Zapier not updating sheet?

1. Check Zap is turned ON
2. Test webhook with curl command
3. Verify Google Sheets permissions
4. Check column mappings in Zap

### Files not organizing?

1. Check filename contains bank name ("Chase", "BofA", "Wells")
2. Verify Dropbox folders exist
3. Check Zap filter conditions
4. Test manually: upload file, watch Zap run

### Still stuck?

- Check main guide: `NO_PYTHON_Tax_Automation_Guide.md`
- Zapier support: https://zapier.com/help
- Playwright MCP: https://github.com/executeautomation/mcp-playwright
- Nutrient support: https://www.nutrient.io/support/

---

## 📊 Progress Tracker

Use this to track your setup:

```
Week 1: Foundation
□□□□ Day 1 □□□□ Day 2 □□□□ Day 3 □□□□ Day 4

Week 2: First Bank
□□□□ Day 1 □□□□ Day 2 □□□□ Day 3

Week 3: Zapier
□□□□ Day 1 □□□□ Day 2 □□□□ Day 3

Week 4: Complete
□□□□ Day 1 □□□□ Day 2 □□□□ Day 3 □□□□ Day 4

🎉 DONE!
```

---

**Good luck! You've got this! 🚀**
