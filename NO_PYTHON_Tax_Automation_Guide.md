# No-Code Tax Automation Guide
## Using Claude Desktop + MCP Servers (Zero Python Required)

**Last Updated:** February 8, 2026  
**Version:** 2.0  
**Estimated Setup Time:** 14 hours  

---

## 📋 Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Prerequisites & Setup](#2-prerequisites--setup)
3. [Playwright MCP - Detailed Setup](#3-playwright-mcp---detailed-setup)
4. [Nutrient DWS MCP - Detailed Setup](#4-nutrient-dws-mcp---detailed-setup)
5. [Zapier MCP - Detailed Setup](#5-zapier-mcp---detailed-setup)
6. [Claude Desktop Workflow](#6-claude-desktop-workflow)
7. [End-to-End Workflow Example](#7-end-to-end-workflow-example)
8. [Security & Credential Management](#8-security--credential-management)
9. [Implementation Roadmap](#9-implementation-roadmap)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Architecture Overview

### 1.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOU (Natural Language)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       CLAUDE DESKTOP                             │
│                    (Control Center)                              │
│                                                                   │
│  MCP Servers Connected:                                          │
│  • Playwright MCP (Browser automation)                           │
│  • Nutrient DWS MCP (PDF processing)                            │
│  • Zapier MCP (8,000+ app integrations)                         │
└─────────┬──────────────┬──────────────┬─────────────────────────┘
          │              │              │
          ▼              ▼              ▼
┌─────────────────┐ ┌──────────────┐ ┌──────────────────────┐
│ PLAYWRIGHT MCP  │ │ NUTRIENT MCP │ │    ZAPIER MCP        │
│                 │ │              │ │                      │
│ • Login to banks│ │ • OCR PDFs   │ │ • Dropbox file ops   │
│ • Navigate sites│ │ • Extract data│ │ • Google Sheets      │
│ • Download PDFs │ │ • Convert docs│ │ • Email notifications│
│ • Handle 2FA    │ │ • Redact info │ │ • 8,000+ apps        │
└────────┬────────┘ └──────┬───────┘ └──────┬───────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────────┐ ┌──────────────┐ ┌──────────────────────┐
│  BANK WEBSITES  │ │  PDF FILES   │ │  DROPBOX             │
│                 │ │              │ │  ↓                   │
│ • Chase         │ │ In Dropbox:  │ │  GOOGLE SHEETS       │
│ • Bank of America│ │ /2025 Taxes/ │ │  ↓                   │
│ • Wells Fargo   │ │  Statements/ │ │  EMAIL/NOTIFICATIONS │
└─────────────────┘ └──────────────┘ └──────────────────────┘
```

### 1.2 Data Flow Explanation

**Monthly Tax Automation Flow:**

1. **You speak to Claude:** "Download January statements from all my banks"
2. **Claude uses Playwright MCP** to:
   - Navigate to Chase.com
   - Securely retrieve credentials (from .env or keychain)
   - Login with 2FA handling
   - Navigate to Statements → Download PDF
   - Save to local `/Downloads/` folder
   - Repeat for Bank of America, Wells Fargo, etc.
3. **Zapier MCP detects new files** in Dropbox folder via Zap trigger
4. **Zapier organizes files** by bank name into subfolders
5. **You tell Claude:** "Extract income data from all January statements"
6. **Claude uses Nutrient DWS MCP** to:
   - OCR any scanned statements
   - Extract text with structure preserved
7. **Claude analyzes extracted text** using its AI capabilities
8. **Zapier MCP updates Google Sheets** with extracted data
9. **Audit trail logged** to `/2025 Taxes/audit.log`

### 1.3 Component Responsibilities

| Component | Responsibility | No Python? |
|-----------|---------------|-----------|
| **Claude Desktop** | Natural language interface, decision-making | ✅ Zero code |
| **Playwright MCP** | Browser automation, bank logins, downloads | ✅ JSON config only |
| **Nutrient DWS MCP** | PDF processing, OCR, data extraction | ✅ API calls only |
| **Zapier MCP** | App integrations, file organization, sheets updates | ✅ Visual workflow builder |
| **Dropbox** | File storage, trigger point for automation | ✅ GUI only |
| **Google Sheets** | Structured data storage (Excel alternative) | ✅ GUI only |

---

## 2. Prerequisites & Setup

### 2.1 Required Software

#### Claude Desktop
- **Download:** https://claude.ai/download
- **Cost:** Free (with Claude account)
- **Installation:**
  ```bash
  # macOS (Apple Silicon)
  # Download Claude-darwin-arm64.dmg
  # Drag to Applications folder
  
  # macOS (Intel)
  # Download Claude-darwin-x64.dmg
  # Drag to Applications folder
  
  # Windows
  # Download Claude-win-x64.exe
  # Run installer
  ```

#### Node.js (Required for MCP servers)
- **Version:** 18+ required
- **Download:** https://nodejs.org/
- **Verify installation:**
  ```bash
  node --version  # Should show v18.0.0 or higher
  npm --version   # Should show 9.0.0 or higher
  ```

### 2.2 Required Accounts

| Service | Purpose | Cost | Sign Up Link |
|---------|---------|------|--------------|
| **Claude** | AI assistant interface | Free tier available | https://claude.ai/signup |
| **Zapier** | Automation workflows | Free: 100 tasks/month, Starter: $20/month (750 tasks) | https://zapier.com/sign-up |
| **Nutrient DWS** | PDF processing API | Free: 1,000 documents/month | https://dashboard.nutrient.io/sign_up/ |
| **Dropbox** | File storage | Free: 2GB, Plus: $11.99/month (2TB) | https://www.dropbox.com/register |
| **Google Account** | Google Sheets access | Free | https://accounts.google.com/signup |

**Total Monthly Cost (Minimum):** $0 (using all free tiers)  
**Total Monthly Cost (Recommended):** $32/month (Zapier Starter + Dropbox Plus)

### 2.3 Configuration File Locations

**macOS:**
```
Claude Desktop Config:
~/Library/Application Support/Claude/claude_desktop_config.json

Secrets File (Playwright):
~/.openclaw/workspace/.env
# OR
~/tax-automation/.env
```

**Windows:**
```
Claude Desktop Config:
%APPDATA%\Claude\claude_desktop_config.json

Secrets File (Playwright):
C:\Users\YourUsername\tax-automation\.env
```

### 2.4 Initial Folder Structure

Create this folder structure in Dropbox:

```
/2025 Taxes/
├── Statements/
│   ├── Raw/              # Playwright saves here
│   ├── Chase/            # Zapier organizes here
│   ├── BankOfAmerica/
│   ├── WellsFargo/
│   └── Processed/        # After data extraction
├── Income/
│   └── income_2025.xlsx  # Google Sheets export
├── Expenses/
└── audit.log             # Activity log
```

---

## 3. Playwright MCP - Detailed Setup

### 3.1 What is Playwright MCP?

Playwright MCP gives Claude the ability to **control a real web browser** through natural language. Instead of writing Python scripts with Selenium or Playwright code, you just tell Claude "login to Chase and download my statement" and it does it.

**Key capabilities:**
- Navigate to any website
- Fill out forms
- Click buttons
- Handle authentication (including 2FA)
- Take screenshots
- Download files
- Execute within a real browser (Chrome, Firefox, or WebKit)

### 3.2 Installation

**Option 1: Quick Install (Recommended)**
```bash
# This installs globally
npm install -g @executeautomation/playwright-mcp-server

# Verify installation
npx @executeautomation/playwright-mcp-server --version
```

**Option 2: Use npx (No Installation)**
```bash
# npx downloads and runs on-the-fly
# No global installation needed
npx -y @executeautomation/playwright-mcp-server
```

**Install Browser Binaries:**
```bash
# Playwright needs browser binaries
# These install to ~/.cache/ms-playwright (macOS/Linux)
# or %USERPROFILE%\AppData\Local\ms-playwright (Windows)

npx playwright install chromium  # Recommended for bank sites
npx playwright install firefox   # Alternative
npx playwright install webkit    # Safari engine
```

### 3.3 Claude Desktop Configuration

Edit your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

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
        "--user-data-dir", "/Users/yourusername/.playwright-profile",
        "--secrets", "/Users/yourusername/.openclaw/workspace/.env"
      ],
      "env": {
        "SANDBOX_PATH": "/Users/yourusername/Dropbox/2025 Taxes/Statements/Raw"
      }
    }
  }
}
```

**Configuration Explained:**
- `--browser chromium`: Use Chrome (best compatibility with banks)
- `--headless false`: Show the browser window (helpful for debugging 2FA)
- `--user-data-dir`: Persistent browser profile (stays logged in)
- `--secrets`: Path to your credential file (see 3.4)
- `SANDBOX_PATH`: Where downloads are saved

### 3.4 Credential Management - The Right Way

**❌ NEVER DO THIS:**
```json
{
  "username": "myemail@gmail.com",
  "password": "MyPassword123"
}
```

**✅ DO THIS INSTEAD:**

#### Option A: Environment Variables + .env File (Recommended)

Create `.env` file in your workspace:

**Location:** `~/tax-automation/.env` or `~/.openclaw/workspace/.env`

```bash
# Bank Credentials (NEVER commit this file to Git!)
CHASE_USERNAME=myemail@gmail.com
CHASE_PASSWORD=
CHASE_2FA_METHOD=sms

BOFA_USERNAME=myemail@gmail.com
BOFA_PASSWORD=
BOFA_2FA_METHOD=app

WELLS_USERNAME=myemail@gmail.com
WELLS_PASSWORD=
WELLS_2FA_METHOD=sms

# Nutrient API
NUTRIENT_DWS_API_KEY=your_api_key_here

# Zapier MCP
ZAPIER_MCP_URL=https://api.zapier.com/v1/mcp/your-endpoint-id
```

**CRITICAL:** Add `.env` to your `.gitignore`:
```bash
echo ".env" >> .gitignore
```

#### Option B: macOS Keychain (Most Secure)

```bash
# Store credentials in macOS Keychain
security add-generic-password \
  -a "chase_login" \
  -s "tax_automation" \
  -w "myemail@gmail.com"

security add-generic-password \
  -a "chase_password" \
  -s "tax_automation" \
  -w "MySecurePassword123"

# Retrieve in scripts (Playwright will handle this via secrets file)
security find-generic-password \
  -a "chase_login" \
  -s "tax_automation" \
  -w
```

#### Option C: 1Password CLI (Recommended for Teams)

```bash
# Install 1Password CLI
brew install --cask 1password-cli

# Sign in
op signin

# Create credentials
op item create \
  --category=login \
  --title="Chase Bank - Tax Automation" \
  --username="myemail@gmail.com" \
  --password="MySecurePassword"

# Reference in .env file:
# CHASE_USERNAME=op://tax-automation/chase-bank/username
# CHASE_PASSWORD=op://tax-automation/chase-bank/password
```

**Then configure Playwright to use 1Password:**
```json
{
  "command": "op",
  "args": ["run", "--no-masking", "--", "npx", "@executeautomation/playwright-mcp-server"]
}
```

### 3.5 Bank-Specific Automation Examples

#### Example 1: Chase Bank Statement Download

**Natural language prompt to Claude:**
```
Using Playwright, go to chase.com, login using my Chase credentials from the secrets file, 
navigate to the Documents section, filter for January 2025, and download the checking 
account statement to the sandbox directory. Name it Chase_Checking_Jan2025.pdf
```

**What Claude + Playwright MCP does:**
1. Opens chromium browser
2. Navigates to https://www.chase.com
3. Clicks "Sign In"
4. Retrieves `CHASE_USERNAME` from .env
5. Fills username field
6. Clicks "Next"
7. Retrieves `CHASE_PASSWORD` from .env
8. Fills password field
9. Clicks "Sign In"
10. **Handles 2FA:**
    - If SMS: Waits for user to enter code (headless=false shows browser)
    - If app: Waits for push notification approval
11. Navigates to Documents/Statements
12. Filters by date: January 2025
13. Clicks download link
14. Saves to `SANDBOX_PATH/Chase_Checking_Jan2025.pdf`

#### Example 2: Bank of America with 2FA

**Prompt:**
```
Download my Bank of America checking statement for January 2025. 
I use the BofA mobile app for 2FA, so wait for me to approve the login.
```

**Playwright MCP Configuration for 2FA waiting:**
```json
{
  "args": [
    "--timeout-action", "60000",
    "--timeout-navigation", "120000"
  ]
}
```

#### Example 3: Wells Fargo - Multiple Accounts

**Prompt:**
```
Login to Wells Fargo and download January 2025 statements for:
1. Checking account ending in 1234
2. Savings account ending in 5678
3. Credit card ending in 9012

Save them as:
- WellsFargo_Checking_Jan2025.pdf
- WellsFargo_Savings_Jan2025.pdf
- WellsFargo_CC_Jan2025.pdf
```

**Claude will:**
- Login once
- Navigate to each account
- Download each statement
- Rename files appropriately

### 3.6 Which Banks Work Best?

| Bank | Compatibility | 2FA Support | Notes |
|------|---------------|-------------|-------|
| **Chase** | ✅ Excellent | SMS, App | Very automation-friendly |
| **Bank of America** | ✅ Excellent | SMS, App, Security Questions | May require first-time manual login |
| **Wells Fargo** | ⚠️ Good | SMS, App | Occasionally requires CAPTCHA |
| **Capital One** | ✅ Excellent | SMS, App | Great API-like structure |
| **Discover** | ✅ Excellent | SMS | Simple, clean interface |
| **American Express** | ⚠️ Good | SMS, App | Aggressive bot detection |
| **Citi** | ⚠️ Moderate | SMS, App | Complex navigation |
| **US Bank** | ⚠️ Moderate | SMS | Frequent layout changes |

**Tips for Success:**
- Use `--headless false` for first-time logins
- Save the browser profile (`--user-data-dir`) to stay logged in
- For banks with aggressive bot detection, slow down interactions:
  ```json
  {"args": ["--slow-mo", "1000"]}  // Wait 1 second between actions
  ```

### 3.7 Handling 2FA/MFA Authentication

#### Strategy 1: Manual 2FA (Headless = False)

```json
{
  "args": ["--headless", "false"]
}
```

**How it works:**
1. Playwright opens visible browser window
2. Automates up to 2FA step
3. **Pauses** and waits for YOU to complete 2FA
4. You enter SMS code or approve push notification
5. Playwright detects success and continues

**Claude prompt:**
```
Login to Chase. When you reach the 2FA screen, pause and wait for me to 
enter the code. Once I'm logged in, download the January statement.
```

#### Strategy 2: SMS 2FA with OTP Capture (Advanced)

Some MCP servers can capture SMS codes if you have:
- An Android phone with SMS forwarding
- A service like Twilio that receives SMS
- IFTTT or Zapier webhook that forwards SMS

**Not recommended** for bank accounts due to security concerns.

#### Strategy 3: Persistent Browser Profile (Best)

```json
{
  "args": [
    "--user-data-dir", "/Users/you/.playwright-profile",
    "--storage-state", "/Users/you/bank-session.json"
  ]
}
```

**How it works:**
1. First time: Login manually with 2FA
2. Playwright saves cookies and local storage
3. Future runs: Already authenticated, no 2FA needed
4. Sessions typically last 30-90 days

**Re-authentication:**
When session expires, Claude will say:
```
"I've reached a login screen. The session appears to have expired. 
Would you like me to pause so you can re-authenticate?"
```

### 3.8 Error Handling & Retry Logic

Playwright MCP has built-in retry logic. You can configure it:

```json
{
  "args": [
    "--retries", "3",
    "--timeout-action", "30000"
  ]
}
```

**Common errors and solutions:**

| Error | Cause | Solution |
|-------|-------|----------|
| `TimeoutError: waiting for selector` | Element not found | Increase timeout or check selector |
| `Navigation timeout` | Page took too long to load | Increase `--timeout-navigation` |
| `Session expired` | Cookies cleared | Re-authenticate |
| `CAPTCHA detected` | Bot detection | Use `--slow-mo`, add human-like delays |
| `Download failed` | File not found | Check download path permissions |

**Claude handles errors naturally:**
```
You: "Download my Chase statement"
Claude: "I encountered a timeout error. The Chase website is loading slowly. 
Should I retry with a longer timeout?"
```

### 3.9 Scheduling Monthly Downloads

**Option 1: Manual Monthly Trigger**
```
You to Claude (first week of each month):
"Download all my January bank statements"
```

**Option 2: Claude Desktop + Cron (macOS/Linux)**

While Claude itself can't schedule tasks, you can create a simple reminder:

```bash
# Add to your crontab (crontab -e)
0 9 1 * * osascript -e 'display notification "Download monthly bank statements" with title "Tax Automation"'
```

**Option 3: Zapier Schedule (Recommended)**

Create a Zap:
- **Trigger:** Schedule (First of every month, 9 AM)
- **Action:** Send email to you: "Time to download bank statements"
- **Action 2:** Slack/Discord notification

Then you open Claude and say:
```
"Download all bank statements for [current month]"
```

---

## 4. Nutrient DWS MCP - Detailed Setup

### 4.1 What is Nutrient DWS MCP?

Nutrient Document Web Services (formerly PSPDFKit) provides **cloud-based PDF processing** without any local software installation. The MCP server lets Claude:

- **OCR scanned PDFs** (extract text from images)
- **Convert formats:** PDF ↔ DOCX, XLSX, images, HTML, Markdown
- **Extract structured data:** Tables, key-value pairs, text
- **Redact sensitive information:** SSNs, credit cards, emails
- **Merge/split PDFs**
- **Add watermarks**
- **Digitally sign documents**

**Why it's better than Python libraries:**
- No local dependencies (no Poppler, Tesseract, ghostscript)
- Cloud-based = always up-to-date
- Production-grade OCR (99%+ accuracy)
- Handles complex PDFs (multi-column, tables, forms)

### 4.2 Getting Your API Key

1. **Sign up:** https://dashboard.nutrient.io/sign_up/
2. **Email verification:** Check your inbox
3. **Create API key:**
   - Dashboard → API Keys → Create New Key
   - Name: "Tax Automation"
   - Copy the key (looks like: `pdf_live_abc123...`)

**Free tier limits:**
- 1,000 document operations per month
- 100 MB max file size
- All features included

**Paid tier ($99/month):**
- 10,000 operations/month
- 500 MB files
- Priority support

### 4.3 Installation & Configuration

**Install the MCP server:**
```bash
npm install -g @nutrient-sdk/dws-mcp-server

# Verify
npx @nutrient-sdk/dws-mcp-server --version
```

**Configure Claude Desktop:**

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@executeautomation/playwright-mcp-server"]
    },
    "nutrient-dws": {
      "command": "npx",
      "args": ["-y", "@nutrient-sdk/dws-mcp-server"],
      "env": {
        "NUTRIENT_DWS_API_KEY": "pdf_live_your_api_key_here",
        "SANDBOX_PATH": "/Users/yourusername/Dropbox/2025 Taxes/Statements"
      }
    }
  }
}
```

**Security Note:** Don't put API key in config file directly. Use environment variable:

```bash
# Add to ~/.zshrc or ~/.bash_profile
export NUTRIENT_DWS_API_KEY="pdf_live_your_key"
```

Then in config:
```json
{
  "env": {
    "NUTRIENT_DWS_API_KEY": "${NUTRIENT_DWS_API_KEY}",
    "SANDBOX_PATH": "/Users/you/Dropbox/2025 Taxes/Statements"
  }
}
```

**Restart Claude Desktop** after config changes.

### 4.4 PDF Processing Workflows

#### Workflow 1: OCR a Scanned Bank Statement

**Scenario:** Your credit union emails PDFs that are scanned images (no selectable text).

**Prompt to Claude:**
```
I have a file called "CreditUnion_Jan2025.pdf" in my Statements folder. 
It's a scanned document. Please OCR it and extract all the text. 
Then save the searchable PDF as "CreditUnion_Jan2025_OCR.pdf"
```

**What happens:**
1. Claude uses `nutrient-dws` MCP server
2. Uploads PDF to Nutrient API
3. Performs OCR (optical character recognition)
4. Returns searchable PDF
5. Saves to your sandbox directory

**Claude's response:**
```
I've OCR'd the credit union statement. The document contained 2 pages 
and I successfully extracted 1,247 words. Here's a summary:

Account: Checking ***1234
Statement Period: January 1-31, 2025
Beginning Balance: $3,456.78
Ending Balance: $4,123.45
Total Deposits: $5,000.00
Total Withdrawals: $4,333.33

The searchable PDF has been saved as CreditUnion_Jan2025_OCR.pdf
```

#### Workflow 2: Extract Structured Data for Tax Records

**Prompt:**
```
From Chase_Checking_Jan2025.pdf, extract:
1. All deposit amounts and dates
2. All withdrawal amounts and dates
3. Total interest earned
4. Account fees

Return as JSON so I can add it to my spreadsheet.
```

**Claude uses Nutrient to:**
1. Extract text from PDF
2. Identify table structures
3. Parse transaction data
4. Format as JSON

**Response:**
```json
{
  "account": "Chase Checking ***1234",
  "period": "2025-01-01 to 2025-01-31",
  "deposits": [
    {"date": "2025-01-05", "description": "Payroll Deposit", "amount": 3500.00},
    {"date": "2025-01-20", "description": "Payroll Deposit", "amount": 3500.00}
  ],
  "withdrawals": [
    {"date": "2025-01-10", "description": "Rent Payment", "amount": 1800.00},
    {"date": "2025-01-15", "description": "Utilities", "amount": 150.00}
  ],
  "interest": 2.34,
  "fees": 0.00,
  "ending_balance": 5052.34
}
```

#### Workflow 3: Convert PDF to Markdown for Claude Analysis

**Prompt:**
```
Convert BofA_Statement_Jan2025.pdf to markdown so you can analyze it more easily.
```

**Why this is useful:**
- Markdown is Claude's native format
- Better understanding of document structure
- Can reason about the content more effectively

**Claude extracts:**
```markdown
# Bank of America Checking Account Statement
## Account: ***5678

### Statement Period
January 1, 2025 - January 31, 2025

### Account Summary
| Metric | Amount |
|--------|--------|
| Beginning Balance | $2,345.67 |
| Deposits | $7,000.00 |
| Withdrawals | $6,123.45 |
| Ending Balance | $3,222.22 |

### Transactions
...
```

#### Workflow 4: Merge Multiple Bank Statements

**Prompt:**
```
Merge these files into one PDF called "AllBanks_Jan2025.pdf":
- Chase_Checking_Jan2025.pdf
- Chase_Savings_Jan2025.pdf
- BofA_Checking_Jan2025.pdf
- WellsFargo_CC_Jan2025.pdf

Add a cover page that says "2025 Tax Year - January Statements"
```

**Nutrient MCP does:**
1. Merges all PDFs in order
2. Generates a cover page
3. Combines into single document
4. Saves result

### 4.5 Available Tools & Capabilities

**Nutrient DWS MCP provides these tools:**

| Tool Name | Description | Use Case |
|-----------|-------------|----------|
| `document_processor` | All-in-one PDF processing | OCR, merge, convert, extract |
| `document_signer` | Digital signatures | Sign tax forms electronically |
| `sandbox_file_tree` | Browse files | See what PDFs are available |

**Document Processor Actions:**

```
OCR (Optical Character Recognition):
- Multi-language support (English, Spanish, German, etc.)
- High accuracy (99%+)
- Preserves layout

Format Conversion:
- PDF → DOCX (editable Word docs)
- PDF → Markdown (for AI analysis)
- PDF → PNG/JPEG (images)
- DOCX/XLSX/PPTX → PDF

Data Extraction:
- Extract all text
- Extract tables as JSON/CSV
- Extract key-value pairs (form fields)
- Extract images

Security:
- Redact SSNs, credit cards, emails
- Add password protection
- Remove metadata

Editing:
- Merge multiple PDFs
- Split PDF into pages
- Rotate pages
- Add watermarks
- Flatten annotations
```

### 4.6 Integration with Dropbox via Zapier

**Setup:**

1. Files downloaded by Playwright → Save to Dropbox `/Raw/` folder
2. Zapier watches for new files
3. Triggers Claude (via webhook) to process
4. Nutrient MCP processes PDF
5. Result saved to `/Processed/` folder

**Zap configuration:**
- **Trigger:** New File in Dropbox (`/2025 Taxes/Statements/Raw/`)
- **Filter:** Only PDF files
- **Action:** Webhook to Claude API (or email you)
- **Action 2:** Move file to appropriate bank folder

---

## 5. Zapier MCP - Detailed Setup

### 5.1 What is Zapier MCP?

Zapier MCP connects Claude to **8,000+ apps** without writing any code. Instead of building integrations yourself, you use Zapier's pre-built connectors.

**Key capabilities:**
- Trigger workflows from Claude
- Update Google Sheets/Excel Online
- Send emails, Slack messages, SMS
- Create calendar events
- Upload/organize files in Dropbox
- Query databases (PostgreSQL, MySQL, Airtable)
- Call any webhook

**How it works:**
1. You create "Zaps" (workflows) in Zapier's visual builder
2. Each Zap becomes a "tool" that Claude can call
3. You tell Claude what to do in natural language
4. Claude calls the appropriate Zap
5. Zapier executes the workflow

### 5.2 Installation & Authentication

**No installation required** - Zapier MCP is cloud-hosted.

**Setup steps:**

1. **Sign up for Zapier:** https://zapier.com/sign-up
   - Free plan: 100 tasks/month (may be tight)
   - Starter plan: $19.99/month, 750 tasks (recommended)

2. **Navigate to Zapier MCP:** https://mcp.zapier.com

3. **Create MCP Server:**
   - Click "+ New MCP Server"
   - Choose: **Claude** as the MCP client
   - Name it: "Tax Automation"
   - Click "Create MCP Server"

4. **Copy the MCP endpoint URL:**
   - It looks like: `https://api.zapier.com/v1/mcp/YOUR_UNIQUE_ID`

5. **Add to Claude Desktop config:**

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@executeautomation/playwright-mcp-server"]
    },
    "nutrient-dws": {
      "command": "npx",
      "args": ["-y", "@nutrient-sdk/dws-mcp-server"],
      "env": {
        "NUTRIENT_DWS_API_KEY": "your_api_key"
      }
    },
    "zapier": {
      "url": "https://api.zapier.com/v1/mcp/YOUR_UNIQUE_ID",
      "type": "http"
    }
  }
}
```

**Restart Claude Desktop.**

### 5.3 Creating Zaps for Tax Workflow

#### Zap 1: Organize Bank Statements by Name

**Goal:** Automatically move downloaded PDFs to bank-specific folders.

**Zap Configuration:**

```
Trigger: New File in Folder
  App: Dropbox
  Folder: /2025 Taxes/Statements/Raw
  File Type: PDF only

Filter: Only continue if...
  Filename contains "Chase" OR "BofA" OR "WellsFargo"

Action 1: Move File
  App: Dropbox
  If filename contains "Chase" → Move to /2025 Taxes/Statements/Chase/
  If filename contains "BofA" → Move to /2025 Taxes/Statements/BankOfAmerica/
  If filename contains "Wells" → Move to /2025 Taxes/Statements/WellsFargo/

Action 2: Send Notification
  App: Email or Slack
  Message: "New [Bank Name] statement organized"
```

**Add this Zap as a tool in Zapier MCP:**
- Name the tool: `organize_bank_statements`
- Claude can call it: "Organize all statements in the Raw folder"

#### Zap 2: Update Google Sheets with Extracted Data

**Goal:** Take JSON data from Claude and add it to a spreadsheet.

**Zap Configuration:**

```
Trigger: Webhook (Catch Hook)
  URL: https://hooks.zapier.com/hooks/catch/YOUR_ID/
  
  Expected data:
  {
    "bank": "Chase",
    "account": "Checking",
    "month": "January",
    "year": 2025,
    "deposits": 7000.00,
    "withdrawals": 5000.00,
    "ending_balance": 3000.00,
    "interest": 2.34,
    "fees": 0.00
  }

Action: Create Spreadsheet Row
  App: Google Sheets
  Spreadsheet: "2025 Tax Records"
  Worksheet: "Income Summary"
  
  Fields:
  - Bank: {{trigger.bank}}
  - Account: {{trigger.account}}
  - Month: {{trigger.month}}
  - Year: {{trigger.year}}
  - Total Deposits: {{trigger.deposits}}
  - Total Withdrawals: {{trigger.withdrawals}}
  - Ending Balance: {{trigger.ending_balance}}
  - Interest Earned: {{trigger.interest}}
  - Fees Paid: {{trigger.fees}}
  - Date Processed: {{current_date}}
```

**Add as MCP tool:**
- Tool name: `update_income_spreadsheet`
- Claude prompt: 
  ```
  After extracting data from Chase_Jan2025.pdf, update my income spreadsheet 
  with the totals.
  ```

#### Zap 3: Email Monthly Summary

**Goal:** Send a summary email at the end of each month.

```
Trigger: Webhook (from Claude)
  Data includes: summary text, attachments

Action 1: Send Email
  App: Gmail
  To: youremail@gmail.com
  Subject: "2025 Tax Summary - {{month}}"
  Body: {{summary_text}}
  Attachments: {{pdf_links}}

Action 2: Log to Spreadsheet
  App: Google Sheets
  Sheet: "Audit Log"
  Add row with timestamp, action, status
```

#### Zap 4: Slack Notification When Complete

```
Trigger: Webhook

Action: Send Channel Message
  App: Slack
  Channel: #tax-automation
  Message: "✅ [Bank] statements processed for [Month]. Data added to spreadsheet."
```

### 5.4 How Claude Triggers Zaps

**Example conversation:**

```
You: "Download my Chase statement for January and add the totals to my spreadsheet"

Claude: 
"I'll break this down:
1. First, I'll use Playwright to download the statement
2. Then Nutrient to extract the data
3. Finally, Zapier to update your Google Sheet

Starting now..."

[Playwright downloads PDF]

"Statement downloaded. Now extracting data..."

[Nutrient OCRs and extracts]

"I found:
- Total deposits: $7,000.00
- Total withdrawals: $5,123.45
- Interest earned: $2.34
- Fees: $0.00

Now updating your spreadsheet..."

[Calls Zapier MCP → triggers webhook → updates Google Sheets]

"Done! Your spreadsheet has been updated with January's Chase data."
```

**Behind the scenes:**
1. Claude calls Zapier MCP tool: `update_income_spreadsheet`
2. Sends JSON payload to Zap webhook
3. Zapier receives data
4. Inserts row in Google Sheets
5. Returns success to Claude
6. Claude confirms to you

### 5.5 Zapier Task Usage

**Important:** Each Zap execution counts against your monthly task limit.

**Estimated task usage for tax automation:**

| Action | Tasks per Month | Monthly Total |
|--------|----------------|---------------|
| Organize 4 bank statements × 12 months | 48 | 48 |
| Update spreadsheet (4 banks × 12 months) | 48 | 48 |
| Email notifications (monthly) | 12 | 12 |
| Slack notifications | 48 | 48 |
| **Total** | | **156 tasks** |

**Recommendation:** Zapier Starter plan (750 tasks/month) provides plenty of buffer.

### 5.6 No-Code Workflow Builder Tips

**Best practices:**

1. **Name your Zaps clearly:**
   - ✅ "Tax Auto - Organize Bank Statements"
   - ❌ "Zap 1"

2. **Add filters to prevent unnecessary runs:**
   ```
   Filter: Only continue if...
   - File extension is "pdf"
   - Filename doesn't contain "receipt"
   - File size > 10 KB
   ```

3. **Use Formatter to clean data:**
   ```
   Formatter: Text → Replace
   Replace "BankOfAmerica" with "Bank of America"
   ```

4. **Add error handling:**
   ```
   If Action 1 fails:
   - Send error email
   - Log to error spreadsheet
   - Retry once after 5 minutes
   ```

5. **Test with sample data:**
   - Zapier lets you test each step
   - Use a test file: `Test_Chase_Jan2025.pdf`
   - Verify it moves to correct folder
   - Check spreadsheet was updated correctly

---

## 6. Claude Desktop Workflow

### 6.1 Using Claude as the Control Center

Think of Claude as your **conversational automation conductor**. Instead of:
- Writing Python scripts
- Running cron jobs
- Clicking through UIs

You just **talk** to Claude:

```
You: "It's February 1st. Time to download all my January bank statements."

Claude: "I'll download statements from Chase, Bank of America, and Wells Fargo. 
This will take about 3-4 minutes due to login and 2FA steps. Should I proceed?"

You: "Yes, go ahead."

Claude: [executes everything]
```

### 6.2 Example Commands

#### Command 1: Monthly Statement Download

```
Download January 2025 statements from:
- Chase checking (account ending in 1234)
- Chase savings (account ending in 5678)
- Bank of America checking (account ending in 9012)
- Wells Fargo credit card (ending in 3456)

Save them to the Raw folder in Dropbox with filenames:
- Chase_Checking_Jan2025.pdf
- Chase_Savings_Jan2025.pdf
- BofA_Checking_Jan2025.pdf
- WellsFargo_CC_Jan2025.pdf
```

**Claude executes:**
1. Playwright logs into Chase → downloads 2 statements
2. Playwright logs into BofA → downloads 1 statement
3. Playwright logs into Wells Fargo → downloads 1 statement
4. Saves all 4 PDFs to Dropbox with correct names

#### Command 2: Batch PDF Processing

```
Process all PDFs in the Raw folder:
1. OCR any scanned documents
2. Extract transaction data from each
3. Save the results to Processed folder
4. Give me a summary of total deposits and withdrawals per bank
```

**Claude executes:**
1. Lists files in Raw folder (4 PDFs found)
2. For each PDF:
   - Nutrient OCRs it
   - Extracts text
   - Parses transactions
   - Moves to Processed folder
3. Aggregates data:
   ```
   Summary for January 2025:
   
   Chase Checking:
   - Deposits: $7,000.00
   - Withdrawals: $5,123.45
   - Net: +$1,876.55
   
   Chase Savings:
   - Deposits: $500.00
   - Withdrawals: $0.00
   - Net: +$500.00
   
   [etc.]
   
   Total across all accounts:
   - Deposits: $15,234.00
   - Withdrawals: $12,456.78
   - Net: +$2,777.22
   ```

#### Command 3: Update Spreadsheet

```
Take the transaction data we just extracted and update my Google Sheet 
"2025 Tax Records" with the January totals for each bank.
```

**Claude executes:**
1. Formats data as JSON
2. Calls Zapier MCP tool: `update_income_spreadsheet`
3. Zapier webhook triggered
4. Google Sheets updated
5. Confirms: "Spreadsheet updated with 4 new rows"

#### Command 4: Audit & Verification

```
Check which banks are missing February statements. We're on March 1st now, 
so I should have all of them.
```

**Claude executes:**
1. Lists files in `/2025 Taxes/Statements/Chase/`
2. Checks for `_Feb2025.pdf`
3. Repeats for BofA, Wells Fargo, etc.
4. Reports:
   ```
   February statements found:
   ✅ Chase Checking
   ✅ Chase Savings  
   ❌ Bank of America (missing)
   ✅ Wells Fargo CC
   
   You're missing Bank of America's February statement. Would you like me to 
   download it now?
   ```

### 6.3 Prompt Engineering for Tax Automation

**Best practices:**

1. **Be specific about file names:**
   ```
   ✅ "Save as Chase_Checking_Jan2025.pdf"
   ❌ "Save with a good filename"
   ```

2. **Break complex tasks into steps:**
   ```
   ✅ "First download statements, then extract data, then update spreadsheet"
   ❌ "Do my taxes"
   ```

3. **Specify error handling:**
   ```
   "If 2FA is required, pause and wait for me to approve. If a download fails, 
   skip it and continue with the others. Give me a summary at the end of any failures."
   ```

4. **Use conditional logic:**
   ```
   "If the PDF is a scanned image (no selectable text), OCR it first. Otherwise, 
   extract directly."
   ```

5. **Request confirmation for destructive actions:**
   ```
   "Before moving files out of the Raw folder, show me the list and ask for confirmation."
   ```

### 6.4 Data Extraction Templates

#### Template 1: Income Summary

```
From [filename], extract:
1. Statement period (start and end dates)
2. Account type (checking, savings, credit card)
3. Beginning balance
4. Ending balance
5. Total deposits (sum of all deposit transactions)
6. Total withdrawals (sum of all withdrawal transactions)
7. Interest earned (if any)
8. Fees charged (if any)
9. Largest single deposit (amount and description)
10. Largest single withdrawal (amount and description)

Return as JSON.
```

#### Template 2: Tax-Relevant Transactions

```
From [filename], identify and extract:
1. Any business-related transactions (descriptions containing: "business", 
   company name, contractor payments)
2. Any charitable donations (descriptions containing: "donation", "charity", 
   "foundation", "nonprofit")
3. Any medical expenses (descriptions containing: "hospital", "pharmacy", 
   "doctor", "medical")
4. Any investment-related transactions (descriptions containing: "dividend", 
   "interest", "capital gain")

For each transaction, include:
- Date
- Description
- Amount
- Category (business/charity/medical/investment)

Return as JSON array.
```

#### Template 3: Cross-Account Transfers

```
Identify any transfers between my own accounts to avoid double-counting income.

Look for transactions like:
- "Transfer to Savings"
- "Transfer from Checking"
- Matching amounts on the same day

Return as JSON with:
- From account
- To account
- Amount
- Date
```

---

## 7. End-to-End Workflow Example

### 7.1 Complete Monthly Workflow

**Date:** February 1, 2025  
**Goal:** Process all January 2025 statements

**Step 1: Open Claude Desktop**

You say:
```
Good morning! It's February 1st. Time to process my January bank statements. 
Let's download them from Chase, Bank of America, and Wells Fargo.
```

**Step 2: Claude Downloads Statements (Playwright MCP)**

Claude responds:
```
I'll download January statements from all three banks. This will require:
1. Chase (checking + savings): ~2 minutes
2. Bank of America (checking): ~1 minute  
3. Wells Fargo (credit card): ~1 minute

I'll need you to approve 2FA for Bank of America (mobile app push notification). 
Should I proceed?
```

You: `Yes`

Claude:
```
Starting downloads...

✅ Chase checking statement downloaded → Chase_Checking_Jan2025.pdf
✅ Chase savings statement downloaded → Chase_Savings_Jan2025.pdf
⏸️ Bank of America requires 2FA. I've entered your credentials and the login page 
is waiting for you to approve the push notification on your phone.

[You approve on BofA mobile app]

✅ Bank of America checking statement downloaded → BofA_Checking_Jan2025.pdf
✅ Wells Fargo credit card statement downloaded → WellsFargo_CC_Jan2025.pdf

All 4 statements downloaded to:
/Users/you/Dropbox/2025 Taxes/Statements/Raw/

Would you like me to process them now?
```

**Step 3: Zapier Auto-Organizes Files**

(This happens automatically via Zap #1)

```
Zapier detected new files in Raw folder:
✅ Moved Chase_Checking_Jan2025.pdf → /Chase/
✅ Moved Chase_Savings_Jan2025.pdf → /Chase/
✅ Moved BofA_Checking_Jan2025.pdf → /BankOfAmerica/
✅ Moved WellsFargo_CC_Jan2025.pdf → /WellsFargo/

Slack notification sent: "4 new statements organized"
```

**Step 4: Claude Processes PDFs (Nutrient DWS MCP)**

You say:
```
Yes, please process all 4 statements. Extract the income data and give me a summary.
```

Claude:
```
Processing 4 statements...

1/4: Chase_Checking_Jan2025.pdf
- Document type: Text-based PDF (no OCR needed)
- Extracted 2,341 words
- Found 47 transactions
- Analysis complete

2/4: Chase_Savings_Jan2025.pdf  
- Document type: Text-based PDF
- Extracted 312 words
- Found 3 transactions
- Analysis complete

3/4: BofA_Checking_Jan2025.pdf
- Document type: Text-based PDF
- Extracted 1,876 words
- Found 34 transactions
- Analysis complete

4/4: WellsFargo_CC_Jan2025.pdf
- Document type: Scanned PDF (OCR required)
- Performing OCR...
- OCR complete: 98.7% confidence
- Extracted 1,523 words
- Found 28 transactions
- Analysis complete

Here's your January 2025 summary:

┌────────────────────┬────────────┬──────────────┬─────────────┬──────────────┐
│ Account            │ Deposits   │ Withdrawals  │ Interest    │ Fees         │
├────────────────────┼────────────┼──────────────┼─────────────┼──────────────┤
│ Chase Checking     │ $7,000.00  │ $5,234.56    │ $0.45       │ $0.00        │
│ Chase Savings      │ $500.00    │ $0.00        │ $12.34      │ $0.00        │
│ BofA Checking      │ $3,200.00  │ $2,876.43    │ $1.23       │ $0.00        │
│ Wells Fargo CC     │ $0.00      │ $1,543.22    │ $0.00       │ $39.00       │
├────────────────────┼────────────┼──────────────┼─────────────┼──────────────┤
│ TOTALS             │ $10,700.00 │ $9,654.21    │ $14.02      │ $39.00       │
└────────────────────┴────────────┴──────────────┴─────────────┴──────────────┘

Net change: +$1,020.81

Would you like me to update your Google Sheet with this data?
```

**Step 5: Update Spreadsheet (Zapier MCP)**

You: `Yes please`

Claude:
```
Calling Zapier to update your income spreadsheet...

Zapier MCP response:
✅ Added 4 rows to "2025 Tax Records" > "Income Summary"
✅ Row highlighting applied (light blue for completed months)
✅ Formula cells auto-calculated totals
✅ Email notification sent to youremail@gmail.com

Your spreadsheet is updated! You can view it here:
https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID
```

**Step 6: Audit Trail**

Claude:
```
I've logged this session to your audit trail:

/2025 Taxes/audit.log

Entry added:
---
Date: 2025-02-01 09:23:15
Action: Monthly statement processing
Month: January 2025
Statements processed: 4
Banks: Chase (2), Bank of America (1), Wells Fargo (1)
Data extracted: Income, expenses, interest, fees
Spreadsheet updated: Yes
Errors: None
Duration: 4 minutes 32 seconds
---

Is there anything else you need help with?
```

You: `Nope, we're all set! Thanks!`

### 7.2 Time Comparison

**Manual Process (without automation):**
1. Visit Chase.com, login, navigate, download (5 min)
2. Visit BofA.com, login, 2FA, navigate, download (6 min)
3. Visit WellsFargo.com, login, navigate, download (5 min)
4. Open each PDF in Acrobat (2 min)
5. Copy/paste data into Excel (15 min)
6. Calculate totals, check for errors (10 min)
7. Organize files into folders (3 min)

**Total: 46 minutes**

**With Claude + MCP Automation:**
1. Tell Claude to do it (30 seconds)
2. Approve 2FA when prompted (30 seconds)
3. Review summary (1 minute)

**Total: 2 minutes (plus 4 minutes of automated background processing)**

**Time Saved: 44 minutes per month × 12 months = 8.8 hours per year**

---

## 8. Security & Credential Management

### 8.1 Best Practices for Bank Credentials

#### ✅ DO:

1. **Use environment variables**
   ```bash
   # .env file (NEVER commit to git)
   CHASE_USERNAME=myemail@gmail.com
   CHASE_PASSWORD=MySecureP@ssw0rd
   ```

2. **Store .env outside your codebase**
   ```bash
   # Good locations:
   ~/.config/tax-automation/.env  # Home directory
   /Users/you/.openclaw/workspace/.env  # OpenClaw workspace
   ```

3. **Use 1Password or macOS Keychain for master credentials**
   ```bash
   # Store .env file encryption key in Keychain
   # Decrypt .env at runtime
   ```

4. **Enable 2FA on all bank accounts**
   - Preferably app-based (Google Authenticator, Authy)
   - SMS as fallback

5. **Use read-only access when possible**
   - Some banks offer "view-only" credentials
   - Request from your bank

6. **Rotate credentials every 90 days**
   ```bash
   # Set calendar reminder
   # Change passwords quarterly
   ```

7. **Use persistent browser profiles**
   ```json
   {"args": ["--user-data-dir", "/secure/location/.playwright-profile"]}
   ```
   - Avoids storing passwords in plain text
   - Relies on browser's encrypted cookie storage

#### ❌ DON'T:

1. **Never hardcode credentials**
   ```json
   // NEVER DO THIS
   {
     "env": {
       "USERNAME": "myemail@gmail.com",
       "PASSWORD": "MyPassword123"
     }
   }
   ```

2. **Never commit .env files to Git**
   ```bash
   # Always add to .gitignore
   echo ".env" >> .gitignore
   echo "*.env" >> .gitignore
   ```

3. **Never email credentials**
   - Use secure sharing tools (1Password shared vaults)

4. **Never use the same password across banks**
   - Use a password manager to generate unique passwords

5. **Never disable 2FA for convenience**
   - 2FA is your safety net

### 8.2 Playwright Secure Credential Retrieval

**Method 1: Secrets File (Recommended)**

Playwright MCP supports a `--secrets` flag:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "-y",
        "@executeautomation/playwright-mcp-server",
        "--secrets", "/Users/you/.config/tax-automation/.env"
      ]
    }
  }
}
```

**The .env file:**
```bash
# /Users/you/.config/tax-automation/.env

# Bank credentials
CHASE_USER=myemail@gmail.com
CHASE_PASS=MySecureP@ssw0rd
BOFA_USER=myemail@gmail.com
BOFA_PASS=DifferentP@ssw0rd
WELLS_USER=myemail@gmail.com
WELLS_PASS=AnotherP@ssw0rd

# MCP API keys
NUTRIENT_API_KEY=pdf_live_abc123
ZAPIER_MCP_URL=https://api.zapier.com/v1/mcp/xyz789
```

**Secure the file:**
```bash
# Only you can read/write
chmod 600 /Users/you/.config/tax-automation/.env

# Verify permissions
ls -la /Users/you/.config/tax-automation/.env
# Should show: -rw------- (600)
```

**Method 2: macOS Keychain Integration**

```bash
# Store credentials in Keychain
security add-generic-password \
  -a "$USER" \
  -s "tax_automation_chase" \
  -w "MySecureP@ssw0rd" \
  -U

# Retrieve in runtime (Playwright can do this with a wrapper script)
security find-generic-password \
  -a "$USER" \
  -s "tax_automation_chase" \
  -w
```

**Method 3: 1Password CLI**

```bash
# Install 1Password CLI
brew install --cask 1password-cli

# Sign in
eval $(op signin)

# Store credentials
op item create \
  --category=login \
  --title="Chase Bank - Tax Automation" \
  --username="myemail@gmail.com" \
  --password="MySecureP@ssw0rd" \
  --vault="Personal"

# Use in .env with secret references
# .env file:
CHASE_USER=op://Personal/Chase Bank - Tax Automation/username
CHASE_PASS=op://Personal/Chase Bank - Tax Automation/password

# Run Playwright with 1Password injection
op run --env-file=/path/to/.env -- npx @executeautomation/playwright-mcp-server
```

**Method 4: Persistent Browser Sessions (Most Secure)**

```json
{
  "args": [
    "--user-data-dir", "/Users/you/.playwright-sessions/banks",
    "--storage-state", "/Users/you/.playwright-sessions/storage.json"
  ]
}
```

**How it works:**
1. First run: Login manually (Claude waits for you)
2. Playwright saves cookies and local storage
3. Future runs: Already authenticated
4. **No credentials stored anywhere**

**Re-authentication:**
- Sessions expire after 30-90 days
- Claude will prompt: "Session expired. Please login again."

### 8.3 2FA Handling Strategies

#### Strategy 1: Manual Approval (Headless = False)

**Best for:** App-based 2FA (BofA, Chase mobile apps)

```json
{
  "args": ["--headless", "false"]
}
```

**Workflow:**
1. Playwright opens browser window (visible)
2. Navigates to bank, enters credentials
3. Reaches 2FA screen
4. **Pauses**
5. Claude says: "Waiting for 2FA approval on your mobile device"
6. You approve on your phone
7. Browser continues automatically
8. Claude: "Login successful, proceeding with download"

#### Strategy 2: SMS Code Entry

**For:** SMS-based 2FA

**Workflow:**
1. Playwright enters credentials
2. Clicks "Send SMS code"
3. Claude: "Please check your phone for the SMS code and enter it in the browser window"
4. You enter code manually
5. Browser continues

**Alternative (advanced):** Use Twilio or similar service to receive SMS and forward to webhook, but this is complex and not recommended for bank accounts.

#### Strategy 3: TOTP (Time-based One-Time Password)

**For:** Google Authenticator, Authy

Some banks support TOTP. If so, you can:

```bash
# Install oathtool
brew install oath-toolkit

# Generate code
oathtool --totp --base32 YOUR_SECRET_KEY

# Playwright can call this automatically
```

**Security note:** Storing TOTP secrets diminishes security. Only do this if the convenience is worth the trade-off.

#### Strategy 4: Trusted Device

**For:** Banks that remember devices

1. First run: Complete 2FA and check "Trust this device for 30 days"
2. Playwright saves the device token
3. Future runs: No 2FA required for 30 days

**Enable in Playwright:**
```json
{
  "args": [
    "--user-data-dir", "/secure/path/.playwright-sessions/chase"
  ]
}
```

### 8.4 Audit Trail Logging

**Why it matters:**
- Track what was downloaded and when
- Verify no unauthorized access
- Provide evidence for tax audits

**Create an audit log:**

```bash
# /2025 Taxes/audit.log
# This file is automatically updated by Claude

2025-02-01 09:23:15 | INFO  | Session started
2025-02-01 09:23:18 | INFO  | Playwright MCP initialized
2025-02-01 09:23:45 | INFO  | Logged into Chase.com
2025-02-01 09:24:12 | INFO  | Downloaded Chase_Checking_Jan2025.pdf (234 KB)
2025-02-01 09:24:45 | INFO  | Downloaded Chase_Savings_Jan2025.pdf (89 KB)
2025-02-01 09:25:03 | INFO  | Logged into BankOfAmerica.com
2025-02-01 09:25:15 | WARN  | 2FA required - waiting for user approval
2025-02-01 09:25:47 | INFO  | 2FA approved, login successful
2025-02-01 09:26:02 | INFO  | Downloaded BofA_Checking_Jan2025.pdf (187 KB)
2025-02-01 09:26:34 | INFO  | Logged into WellsFargo.com
2025-02-01 09:27:01 | INFO  | Downloaded WellsFargo_CC_Jan2025.pdf (145 KB)
2025-02-01 09:27:15 | INFO  | All downloads complete
2025-02-01 09:27:20 | INFO  | Nutrient MCP processing started
2025-02-01 09:28:42 | INFO  | All PDFs processed
2025-02-01 09:28:50 | INFO  | Zapier webhook called: update_income_spreadsheet
2025-02-01 09:28:53 | INFO  | Google Sheets updated
2025-02-01 09:28:55 | INFO  | Session ended
2025-02-01 09:28:55 | INFO  | Total duration: 5 minutes 40 seconds
```

**Ask Claude to log automatically:**
```
After each action, append a log entry to /2025 Taxes/audit.log with:
- Timestamp
- Action performed
- Status (success/failure)
- Any errors
```

### 8.5 Backup Strategy

**Before automating:**

1. **Backup your Excel/Google Sheets**
   ```bash
   # Download a copy weekly
   # Keep in /2025 Taxes/Backups/
   ```

2. **Backup raw PDFs**
   ```bash
   # Keep originals in /2025 Taxes/Originals/
   # Never delete these
   ```

3. **Test on copies first**
   ```
   Claude prompt:
   "Create a test folder /2025 Taxes/Test/ and run the process on copies of 
   my Chase statements. Don't touch the originals."
   ```

4. **Version control your .env file**
   ```bash
   # Encrypt and back up to 1Password
   # Or use git-crypt to encrypt specific files in Git
   ```

---

## 9. Implementation Roadmap

### 9.1 Week 1: Setup Claude Desktop + MCP Servers (4 hours)

**Day 1: Monday (1.5 hours)**

- [ ] Install Claude Desktop
- [ ] Install Node.js (v18+)
- [ ] Create folder structure in Dropbox:
  ```
  /2025 Taxes/
    Statements/Raw/
    Statements/Chase/
    Statements/BankOfAmerica/
    Statements/WellsFargo/
    Income/
    Expenses/
  ```
- [ ] Create `.env` file template (see Section 8.2)
- [ ] Secure `.env` file permissions: `chmod 600 .env`

**Day 2: Tuesday (1 hour)**

- [ ] Install Playwright MCP server:
  ```bash
  npm install -g @executeautomation/playwright-mcp-server
  npx playwright install chromium
  ```
- [ ] Configure Claude Desktop config file
- [ ] Test Playwright MCP:
  ```
  Claude prompt: "Navigate to google.com and take a screenshot"
  ```

**Day 3: Wednesday (1 hour)**

- [ ] Sign up for Nutrient DWS (https://dashboard.nutrient.io/sign_up/)
- [ ] Get API key
- [ ] Install Nutrient MCP server:
  ```bash
  npm install -g @nutrient-sdk/dws-mcp-server
  ```
- [ ] Add to Claude Desktop config
- [ ] Test with sample PDF:
  ```
  Claude prompt: "Extract text from test.pdf and show me the first paragraph"
  ```

**Day 4: Thursday (30 minutes)**

- [ ] Sign up for Zapier account
- [ ] Create MCP server at https://mcp.zapier.com
- [ ] Add Zapier MCP endpoint to Claude config
- [ ] Restart Claude Desktop and verify all 3 MCP servers are connected

**Checkpoint:** Ask Claude:
```
"Which MCP servers are you connected to?"
```

Expected response:
```
I'm connected to:
1. Playwright MCP - for browser automation
2. Nutrient DWS MCP - for PDF processing
3. Zapier MCP - for app integrations

All servers are responding normally. What would you like me to help you with?
```

---

### 9.2 Week 2: Configure First Bank with Playwright (3 hours)

**Day 1: Monday (1.5 hours)**

**Goal:** Successfully download one statement from your easiest bank.

- [ ] Choose your simplest bank (recommend Chase or Capital One)
- [ ] Add credentials to `.env` file
- [ ] Test manual login first (visit bank website yourself to verify it works)
- [ ] Ask Claude:
  ```
  "Navigate to chase.com, login using my credentials from the secrets file, 
  and show me the homepage. Use headless=false so I can watch."
  ```
- [ ] **Handle 2FA:** Approve on your phone when prompted
- [ ] Once logged in successfully, ask Claude:
  ```
  "Take a screenshot so I can see the homepage"
  ```
- [ ] Verify login was successful

**Day 2: Tuesday (1 hour)**

- [ ] Navigate to statements section:
  ```
  "Navigate to the Statements or Documents section"
  ```
- [ ] Find the latest statement:
  ```
  "Show me what statements are available"
  ```
- [ ] Download a specific statement:
  ```
  "Download the January 2025 checking account statement and save it as 
  Chase_Checking_Jan2025.pdf in my Dropbox Raw folder"
  ```
- [ ] Verify the PDF was downloaded and saved correctly

**Day 3: Wednesday (30 minutes)**

- [ ] Create a reusable prompt template:
  ```markdown
  ## Chase Statement Download Template
  
  1. Navigate to chase.com
  2. Click "Sign In"
  3. Enter username from CHASE_USERNAME
  4. Click "Next"
  5. Enter password from CHASE_PASSWORD  
  6. Click "Sign In"
  7. Wait for 2FA approval (I'll handle this on my phone)
  8. Navigate to "Documents & Statements"
  9. Filter by account: Checking ending in 1234
  10. Filter by date: [MONTH] [YEAR]
  11. Click download link
  12. Save to Dropbox: Chase_Checking_[MONTH][YEAR].pdf
  ```
- [ ] Save this template to `/2025 Taxes/playbooks/chase-download.md`
- [ ] Test the template by asking Claude to follow it

**Checkpoint:** You should be able to say:
```
"Follow the Chase download playbook for February 2025"
```

And Claude successfully downloads the statement.

---

### 9.3 Week 3: Setup Zapier Workflows (3 hours)

**Day 1: Monday (1 hour)**

**Create Zap #1: Auto-organize statements**

- [ ] Login to Zapier.com
- [ ] Create new Zap
- [ ] **Trigger:** Dropbox - New File in Folder
  - Folder: `/2025 Taxes/Statements/Raw`
  - File Type: PDF
  - Test trigger with sample file
- [ ] **Filter:** Only continue if filename contains bank name
- [ ] **Action:** Dropbox - Move File
  - If filename contains "Chase" → move to `/Statements/Chase/`
  - If filename contains "BofA" → move to `/Statements/BankOfAmerica/`
  - If filename contains "Wells" → move to `/Statements/WellsFargo/`
- [ ] Test with real file
- [ ] Turn on Zap

**Day 2: Tuesday (1 hour)**

**Create Zap #2: Update Google Sheets**

- [ ] Create Google Sheet: "2025 Tax Records"
- [ ] Add worksheet: "Income Summary"
- [ ] Create columns:
  ```
  | Date Processed | Bank | Account | Month | Year | Deposits | Withdrawals | Interest | Fees | Net Change |
  ```
- [ ] In Zapier, create new Zap
- [ ] **Trigger:** Webhooks - Catch Hook
  - Copy webhook URL
- [ ] **Action:** Google Sheets - Create Spreadsheet Row
  - Spreadsheet: 2025 Tax Records
  - Worksheet: Income Summary
  - Map fields from webhook data
- [ ] Test with sample data:
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
- [ ] Verify row appeared in Google Sheets
- [ ] Turn on Zap

**Day 3: Wednesday (1 hour)**

**Connect Zapier MCP to Claude**

- [ ] In Zapier MCP dashboard (https://mcp.zapier.com)
- [ ] Click "+ Add Tool"
- [ ] Configure webhook-to-sheets Zap as a callable tool
  - Tool name: `update_income_spreadsheet`
  - Description: "Updates Google Sheets with bank statement data"
  - Parameters:
    - bank (required)
    - account (required)
    - month (required)
    - year (required)
    - deposits (required)
    - withdrawals (required)
    - interest (optional)
    - fees (optional)
- [ ] Test from Claude:
  ```
  "Use the update_income_spreadsheet tool to add a test entry:
  Bank: Chase, Account: Checking, Month: January, Year: 2025,
  Deposits: 7000, Withdrawals: 5000, Interest: 2.34, Fees: 0"
  ```
- [ ] Verify entry in Google Sheets

**Checkpoint:** You should be able to:
1. Drop a PDF in `/Raw/` → auto-organized into bank folder
2. Tell Claude to update spreadsheet → new row appears

---

### 9.4 Week 4: Add Remaining Banks + Testing (4 hours)

**Day 1: Monday (2 hours)**

**Add Bank of America:**

- [ ] Add BofA credentials to `.env`
- [ ] Create playbook: `/2025 Taxes/playbooks/bofa-download.md`
- [ ] Test login with Claude
- [ ] Test statement download
- [ ] Update Zapier Zap to handle "BofA" in filename

**Add Wells Fargo:**

- [ ] Add Wells credentials to `.env`
- [ ] Create playbook: `/2025 Taxes/playbooks/wells-download.md`
- [ ] Test login with Claude
- [ ] Test statement download
- [ ] Update Zapier Zap to handle "Wells" in filename

**Day 2: Tuesday (1 hour)**

**Integration Testing:**

- [ ] Test full workflow end-to-end:
  ```
  1. Download statements from all banks
  2. Verify auto-organization works
  3. Process PDFs with Nutrient
  4. Extract data
  5. Update spreadsheet
  6. Verify all data is correct
  ```
- [ ] Test error scenarios:
  - What if 2FA times out?
  - What if a statement isn't available?
  - What if Zapier webhook fails?
- [ ] Document any issues in `/2025 Taxes/troubleshooting.md`

**Day 3: Wednesday (1 hour)**

**Create Master Workflow:**

- [ ] Create `/2025 Taxes/playbooks/monthly-workflow.md`:
  ```markdown
  # Monthly Tax Automation Workflow
  
  Run this on the 1st of each month:
  
  ## Step 1: Download Statements (5 minutes)
  "Download [previous month] statements from Chase, Bank of America, and 
  Wells Fargo. Save to Raw folder with standardized names."
  
  ## Step 2: Wait for Auto-Organization (30 seconds)
  Zapier will automatically move files to correct folders.
  
  ## Step 3: Process PDFs (2 minutes)
  "Process all PDFs in the Raw folder. OCR if needed. Extract transaction data."
  
  ## Step 4: Update Spreadsheet (1 minute)
  "Update Google Sheets with extracted data for [month]."
  
  ## Step 5: Verify (2 minutes)
  - Open Google Sheets
  - Check that all 3 banks have entries
  - Verify totals look correct
  - Check audit log for errors
  
  ## Step 6: Backup (1 minute)
  - Download a copy of the spreadsheet
  - Save to /2025 Taxes/Backups/
  ```
- [ ] Test the complete workflow
- [ ] Time yourself: should take ~10 minutes total

**Day 4: Thursday (15 minutes)**

**Documentation:**

- [ ] Create `/2025 Taxes/README.md` with:
  - Quick start guide
  - List of credentials and where they're stored
  - Troubleshooting common issues
  - Contact info for support (Zapier, Nutrient, etc.)

**Checkpoint:** Run the complete monthly workflow start-to-finish without errors.

---

### 9.5 Total Time Estimate

| Phase | Estimated Time | Actual Time (track yours) |
|-------|----------------|---------------------------|
| Week 1: Setup | 4 hours | ___ hours |
| Week 2: First bank | 3 hours | ___ hours |
| Week 3: Zapier | 3 hours | ___ hours |
| Week 4: Testing | 4 hours | ___ hours |
| **Total** | **14 hours** | **___ hours** |

**Compare to Python-based automation:**
- Learning Python: 20 hours
- Writing scripts: 15 hours
- Debugging: 8 hours
- Maintenance: 5 hours/year
- **Total: 43 hours first year**

**No-code approach saves you 29 hours in year 1.**

---

## 10. Troubleshooting

### 10.1 Common Playwright Errors

#### Error: "Browser not installed"

**Symptom:**
```
Error: Browser chromium not found
```

**Solution:**
```bash
npx playwright install chromium
```

#### Error: "Timeout waiting for selector"

**Symptom:**
```
TimeoutError: waiting for selector "button[name='login']" to be visible
```

**Solutions:**
1. Increase timeout:
   ```json
   {"args": ["--timeout-action", "60000"]}
   ```
2. Check if selector changed:
   ```
   Claude prompt: "Take a screenshot of the login page and show me the 
   current layout"
   ```
3. Use more robust selectors:
   ```
   Instead of: button[name='login']
   Try: text="Sign In"
   Or: role=button[name="Sign In"]
   ```

#### Error: "CAPTCHA detected"

**Symptom:**
Browser gets stuck on CAPTCHA screen

**Solutions:**
1. Use persistent session (stay logged in):
   ```json
   {"args": ["--user-data-dir", "/path/to/profile"]}
   ```
2. Slow down interactions:
   ```json
   {"args": ["--slow-mo", "2000"]}
   ```
3. Add human-like delays:
   ```
   Claude prompt: "Wait 3 seconds between each click"
   ```
4. Manual CAPTCHA solving:
   ```json
   {"args": ["--headless", "false"]}
   ```
   Then solve CAPTCHA yourself when prompted.

#### Error: "Session expired"

**Symptom:**
Playwright reaches login screen even though you logged in before

**Solutions:**
1. Check cookies were saved:
   ```bash
   ls -la ~/.playwright-sessions/
   ```
2. Re-authenticate:
   ```
   Claude prompt: "The session expired. Please pause at the login screen 
   so I can re-authenticate."
   ```
3. Increase session persistence:
   - Enable "Remember this device" during login
   - Check bank settings for session timeout options

### 10.2 MFA/2FA Handling Issues

#### Issue: 2FA code expires before I can enter it

**Solution 1:** Increase timeout
```json
{"args": ["--timeout-action", "120000"]}  // 2 minutes
```

**Solution 2:** Use app-based 2FA instead of SMS
- Faster approval
- No typing required
- Push notification-based

**Solution 3:** Pre-approve before starting
```
Claude prompt: "I'm ready with my phone. Start the login process now."
```

#### Issue: Bank doesn't remember my device

**Solution:**
- Some banks clear device memory frequently
- Check bank settings: "Manage trusted devices"
- May need to manually approve 2FA every time (unavoidable)

#### Issue: SMS codes not arriving

**Solutions:**
1. Check phone signal strength
2. Try alternative 2FA method (email, app)
3. Contact bank to verify phone number on file

### 10.3 Bank Website Changes

#### Problem: Selectors break after bank updates their website

**Symptom:**
```
Error: Cannot find element with selector "a#statements"
```

**Solution:**
1. Ask Claude to inspect current page:
   ```
   "Take a screenshot and show me the current layout of the Statements page"
   ```
2. Update playbook with new selectors
3. Use more resilient selectors:
   - ✅ `text="Statements"` (text-based)
   - ✅ `role=link[name="Statements"]` (accessibility-based)
   - ❌ `a#nav-item-47` (fragile ID-based)

**Preventive measures:**
- Use text-based selectors when possible
- Playwright MCP has auto-healing: it tries multiple strategies
- Keep playbooks updated after successful runs

#### When banks make major changes:

1. Visit bank website manually
2. Note the new navigation path
3. Update playbook
4. Test with Claude:
   ```
   "Follow my updated playbook for Chase"
   ```

### 10.4 Zapier Rate Limits

#### Issue: "Rate limit exceeded"

**Cause:**
- Free plan: 100 tasks/month
- Starter plan: 750 tasks/month
- Each Zap run = 1 task per action

**Solution:**
1. Upgrade to Starter plan ($19.99/month)
2. Optimize Zaps:
   - Combine multiple actions into one Zap
   - Use filters to prevent unnecessary runs
   - Reduce polling frequency (check every 15 min instead of 5 min)

#### Issue: "Task limit reached"

**Monitor usage:**
- Zapier Dashboard → Usage
- Track tasks consumed per Zap
- Estimate monthly usage (see Section 5.5)

**Reduce task consumption:**
- Disable Zaps you're not using
- Use Zapier's "Paused" state for seasonal Zaps
- Batch operations (process multiple files at once)

### 10.5 Claude Desktop Issues

#### Issue: MCP servers not showing up

**Symptom:**
Claude doesn't respond to commands like "Use Playwright to..."

**Solutions:**
1. **Verify config file location:**
   ```bash
   # macOS
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   
   # Windows
   type %APPDATA%\Claude\claude_desktop_config.json
   ```

2. **Check JSON syntax:**
   ```bash
   # Validate JSON
   cat claude_desktop_config.json | python -m json.tool
   ```

3. **Restart Claude Desktop completely:**
   - Quit Claude (Cmd+Q on Mac, Alt+F4 on Windows)
   - Check Activity Monitor/Task Manager for lingering processes
   - Kill any "Claude" processes
   - Restart

4. **Check MCP server logs:**
   ```bash
   # Playwright MCP logs
   tail -f ~/playwright-mcp-server.log
   
   # Nutrient MCP logs (if configured for file output)
   tail -f ~/nutrient-mcp-server.log
   ```

#### Issue: Claude says "I don't have access to that tool"

**Cause:** MCP server failed to start

**Debugging:**
1. Test MCP server manually:
   ```bash
   npx @executeautomation/playwright-mcp-server
   # Should start without errors
   ```

2. Check Node.js version:
   ```bash
   node --version
   # Must be v18.0.0 or higher
   ```

3. Check environment variables:
   ```bash
   echo $NUTRIENT_DWS_API_KEY
   # Should print your API key
   ```

4. Verify npx can access packages:
   ```bash
   npx @executeautomation/playwright-mcp-server --version
   ```

#### Issue: "API rate limit exceeded" (Claude)

**Cause:** Too many messages too quickly

**Solution:**
- Wait 1 minute between complex requests
- Break large workflows into smaller chunks
- Use Claude's thinking time wisely (it can process while "thinking")

### 10.6 PDF Processing Issues

#### Issue: Nutrient API returns "Invalid API key"

**Solutions:**
1. Check API key in dashboard: https://dashboard.nutrient.io
2. Regenerate key if needed
3. Verify environment variable:
   ```bash
   echo $NUTRIENT_DWS_API_KEY
   ```
4. Update Claude config and restart

#### Issue: "Monthly limit exceeded"

**Cause:** Free tier = 1,000 operations/month

**Calculate your usage:**
- 4 banks × 12 months × 3 operations each (OCR, extract, convert) = 144 operations
- Well under the limit

**If you exceed:**
- Upgrade to paid plan ($99/month for 10,000 operations)
- Reduce unnecessary OCR (only OCR scanned docs)
- Process PDFs locally with other tools

#### Issue: OCR accuracy is low

**Causes:**
- Poor quality scan
- Non-standard font
- Multiple columns
- Handwriting

**Solutions:**
1. Request better quality statements from bank
2. Adjust OCR settings:
   ```
   Claude prompt: "OCR this document with high accuracy mode and German 
   language detection"
   ```
3. Manual correction:
   ```
   "Extract the text, then I'll correct any errors"
   ```

### 10.7 Spreadsheet Update Issues

#### Issue: Wrong data goes to wrong cell

**Cause:** Column mapping in Zapier is incorrect

**Solution:**
1. Go to Zapier Zap
2. Click "Edit" on Google Sheets action
3. Verify field mappings:
   ```
   Bank → Column A
   Account → Column B
   Month → Column C
   Deposits → Column D
   (etc.)
   ```
4. Test with sample data

#### Issue: Formula cells get overwritten

**Solution:**
1. In Google Sheets, lock formula cells
2. Or place formulas in a different sheet/range
3. Zapier should only write to data columns, not formula columns

#### Issue: Duplicate entries

**Cause:** Zap ran twice for the same file

**Solutions:**
1. Add filter in Zapier:
   ```
   Only continue if...
   Row with same Bank + Month + Year doesn't exist
   ```
2. Use "Update or Create" action instead of "Create Row"
3. Manual cleanup:
   ```
   "Claude, check my spreadsheet for duplicate entries for January 2025 and 
   remove them"
   ```

---

## Appendix A: Quick Reference

### Essential Commands

```bash
# Install MCP servers
npm install -g @executeautomation/playwright-mcp-server
npm install -g @nutrient-sdk/dws-mcp-server

# Install browsers
npx playwright install chromium

# Test MCP server
npx @executeautomation/playwright-mcp-server --version

# Secure .env file
chmod 600 ~/.config/tax-automation/.env

# Restart Claude Desktop
killall Claude && open -a Claude
```

### File Locations

```
Claude Config (macOS):
~/Library/Application Support/Claude/claude_desktop_config.json

Claude Config (Windows):
%APPDATA%\Claude\claude_desktop_config.json

Secrets File:
~/.config/tax-automation/.env

Playwright Profile:
~/.playwright-sessions/banks/

Dropbox Folder:
~/Dropbox/2025 Taxes/
```

### Support Links

- **Claude Desktop:** https://claude.ai/download
- **Playwright MCP:** https://github.com/executeautomation/mcp-playwright
- **Nutrient DWS:** https://www.nutrient.io/api/
- **Zapier MCP:** https://mcp.zapier.com
- **Zapier Support:** https://zapier.com/help

---

## Appendix B: Cost Breakdown

| Service | Free Tier | Paid Tier | Recommended |
|---------|-----------|-----------|-------------|
| **Claude** | Free usage | $20/month Pro | Free is fine |
| **Zapier** | 100 tasks/month | $19.99/month (750 tasks) | Paid |
| **Nutrient DWS** | 1,000 docs/month | $99/month (10,000 docs) | Free is fine |
| **Dropbox** | 2 GB | $11.99/month (2 TB) | Depends on usage |
| **Google Sheets** | Free | N/A | Free |
| **Total (minimum)** | **$0/month** | | |
| **Total (recommended)** | **$32/month** | | Zapier + Dropbox |

**ROI Calculation:**
- Time saved: 44 minutes/month = 8.8 hours/year
- If your time is worth $50/hour: 8.8 × $50 = **$440/year saved**
- Cost: $32/month × 12 = $384/year
- **Net benefit: $56/year + significant stress reduction**

---

**End of Guide**

*For questions, issues, or improvements, please create a GitHub issue or contact the maintainer.*
