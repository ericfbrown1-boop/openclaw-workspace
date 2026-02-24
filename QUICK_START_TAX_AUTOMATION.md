# Quick Start: Tax Automation in 2 Hours

**Goal:** Get your first statement processed automatically in under 2 hours

---

## Step 1: Install Claude Desktop (15 minutes)

### Mac:
```bash
brew install --cask claude
```

### Windows:
- Download from https://claude.ai/download
- Run installer

**Subscribe to Claude Pro:** $20/month at https://claude.ai/

---

## Step 2: Install MCP Servers (10 minutes)

```bash
# Install Node.js first (if needed)
# Mac:
brew install node@22

# Windows: Download from https://nodejs.org/

# Install MCP servers
npm install -g @modelcontextprotocol/server-playwright
npm install -g @modelcontextprotocol/server-filesystem
npx playwright install
```

---

## Step 3: Configure Claude Desktop (10 minutes)

**Mac:** Edit `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** Edit `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-playwright"]
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/YOURNAME/Dropbox/2025 Taxes"
      ]
    }
  }
}
```

**Replace `/Users/YOURNAME/Dropbox/2025 Taxes` with YOUR actual path!**

**Restart Claude Desktop**

---

## Step 4: Test Download (30 minutes)

Open Claude Desktop and paste:

```
I need to download my January 2025 bank statement from Chase.

Please:
1. Open chase.com in a browser
2. Wait for me to log in (I'll handle credentials and 2FA)
3. Navigate to Statements & Documents
4. Download the January 2025 statement
5. Save it as: ~/Dropbox/2025 Taxes/Incoming/Chase_Checking_2025-01.pdf

Pause at the login page so I can authenticate.
```

**Claude will:**
- Launch browser
- Navigate to Chase
- Wait for you to log in
- Find the statements section
- Download the file
- Save with proper naming

**Result:** You just automated your first statement download! 🎉

---

## Step 5: Process Statement with Claude (20 minutes)

In Claude Desktop:

```
I have a bank statement at:
~/Dropbox/2025 Taxes/Incoming/Chase_Checking_2025-01.pdf

Please extract the following data and return as JSON:
- Institution name
- Account number (last 4 digits only)
- Statement period (start and end dates)
- Beginning balance
- Ending balance
- Interest earned
- Total deposits
- Total withdrawals

Use the filesystem MCP to read the file.
```

**Claude will:**
- Read the PDF
- Extract all the data
- Return structured JSON

**Copy the JSON response - you'll use it in Step 6**

---

## Step 6: Update Excel Manually (This Time) (15 minutes)

1. Open your "Index for 2025 Taxes.xlsx"
2. Find the row for Chase Checking
3. Paste the extracted values into the correct columns
4. Apply light blue fill to mark the row complete

**Next time:** We'll automate this step with Python!

---

## Step 7: Set Up Zapier (20 minutes)

1. Sign up at https://zapier.com/ (Starter plan: $29.99/month)
2. Create a new Zap:

**Trigger:**
- App: Dropbox
- Event: New File in Folder
- Folder: `/2025 Taxes/Incoming`

**Action:**
- App: Dropbox
- Action: Move File
- From: `/2025 Taxes/Incoming`
- To: `/2025 Taxes/Processed/Chase/Checking/`

3. Test the Zap
4. Turn it on

**Result:** Files automatically organize themselves! 🎉

---

## What You've Accomplished

In 2 hours, you've:
- ✅ Automated statement downloads
- ✅ Automated data extraction
- ✅ Automated file organization
- ✅ Processed your first statement

**Estimated time saved: ~15 minutes per statement**

---

## Next Steps (When Ready)

### Week 2: Add More Banks
- Repeat Step 4 for each bank
- Save Claude conversations as "skills" for next year

### Week 3: Python Automation
- Follow the full guide to install Python
- Set up the Excel automation scripts
- Eliminate manual copying/pasting

### Week 4: Full Pipeline
- Run the complete automation end-to-end
- Generate summary reports
- Prepare package for accountant

---

## Quick Commands for Claude Desktop

**Download all statements:**
```
Download all 2025 statements from:
- Chase Checking (***1234)
- Chase Savings (***5678)  
- Fidelity Investment (***9012)

Save to ~/Dropbox/2025 Taxes/Incoming/ with format:
{Bank}_{AccountType}_2025-{MM}.pdf
```

**Process all incoming files:**
```
For each PDF in ~/Dropbox/2025 Taxes/Incoming/:
1. Extract financial data (interest, balance, dates)
2. Save extraction as JSON in the same folder
3. Move PDF to appropriate Processed subfolder
```

**Generate summary:**
```
Analyze all PDFs in ~/Dropbox/2025 Taxes/Processed/ and create a summary:
- Total interest income
- Total dividends
- Which accounts are complete
- Which months are missing
- Any unusual transactions
```

---

## Troubleshooting

**Claude can't see my Dropbox folder?**
- Check the path in `claude_desktop_config.json` is correct
- Use absolute path (not ~)
- Restart Claude Desktop

**Bank website won't let Claude log in?**
- This is normal - you have to log in manually
- Tell Claude: "I'm logging in now, wait for me"
- Claude will continue after you authenticate

**PDF extraction returns gibberish?**
- PDF might be scanned (image-based)
- Tell Claude: "Use OCR to extract text from this image-based PDF"
- Or install Nutrient DWS MCP for better OCR

**Playwright not working?**
```bash
# Reinstall Playwright browsers
npx playwright install --force
```

---

## Success Checklist

Day 1:
- [ ] Claude Desktop installed and configured
- [ ] Downloaded 1 statement via Claude + Playwright
- [ ] Extracted data from 1 statement
- [ ] Set up Zapier file organization

Week 1:
- [ ] Downloaded statements from all banks
- [ ] Processed 5+ statements
- [ ] Files auto-organizing in Dropbox

Week 2:
- [ ] Python environment set up
- [ ] Automated Excel updates working
- [ ] Light blue completion tracking working

Week 4:
- [ ] Full pipeline running
- [ ] Summary report generated
- [ ] System documented for next year

---

## Cost Summary (Monthly)

- Claude Pro: $20
- Zapier Starter: $29.99
- Dropbox Pro: $11.99 (if needed)
- **Total: ~$62/month** (only during tax season)

**Time saved: 12-17 hours** (worth $600-2,550 at $50-150/hour)

**ROI: Break even in first year!**

---

## Get Help

- **Claude Desktop Docs:** https://docs.anthropic.com/claude/docs/claude-desktop
- **MCP Documentation:** https://modelcontextprotocol.io/
- **Anthropic Discord:** https://discord.gg/anthropic
- **Full Guide:** See `2025_Tax_Automation_Comprehensive_Guide.md`

---

**Remember:** You don't need to automate everything at once. Start with downloading and extracting - that alone saves huge time!

**Good luck! 🚀**
