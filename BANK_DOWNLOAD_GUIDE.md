# Bank Document Download Guide
## Using Your Existing Logged-In Chrome Session

## 🚀 Quick Start

### Step 1: Launch Chrome with Remote Debugging

Open Terminal and run:
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="$HOME/chrome-automation"
```

This will:
- Open a new Chrome window
- Enable remote control on port 9222
- Use a separate profile (keeps your main Chrome separate)

### Step 2: Login to Your Bank

In the Chrome window that just opened:
1. Go to your bank's website
2. Login normally (handle 2FA yourself)
3. Navigate to the Statements/Documents/Tax Forms page
4. Leave the window open on that page

### Step 3: Tell Me You're Ready

Message me: "Ready to download documents from [Bank Name]"

I'll connect to your Chrome window and:
- Search for all document links (statements, 1099s, PDFs, reports)
- Download everything I find
- Save to: `~/Downloads/Tax-Documents/[Bank Name]/`

### Step 4: Repeat for Each Bank

Keep the Chrome window open and just login to the next bank. Tell me when ready for each one.

---

## 📋 What Gets Downloaded

The script searches for any links containing:
- "statement" / "statements"
- "tax document" / "tax documents"  
- "1099", "1099-INT", "1099-DIV", "1099-B"
- "report" / "reports"
- Any PDF files
- "download" / "export" buttons

## 📁 Download Locations

All files go to: `~/Downloads/Tax-Documents/[Bank Name]/`

Examples:
- `~/Downloads/Tax-Documents/Chase/`
- `~/Downloads/Tax-Documents/Bank-of-America/`
- `~/Downloads/Tax-Documents/Wells-Fargo/`

## 🔒 Security Benefits

✅ **You handle login** - No storing bank passwords  
✅ **You handle 2FA** - No SMS/authenticator automation needed  
✅ **Session stays secure** - Uses your authenticated session  
✅ **Separate profile** - Doesn't touch your main Chrome data  
✅ **Local only** - Everything runs on your Mac  

## 💡 Tips

1. **Stay on the documents page** - Make sure you're viewing the list of available documents
2. **Expand date ranges** - Set to "All dates" or "2025" before starting
3. **One bank at a time** - Don't switch banks mid-download
4. **Close popups** - Dismiss any "download our app!" messages first

## 🛠️ Manual Mode (If You Prefer)

You can also run the script directly:

```bash
cd ~/.openclaw/workspace
node bank-document-downloader.js "Chase" "https://secure.chase.com/statements"
```

## 🚨 Troubleshooting

**Chrome won't connect?**
- Make sure Chrome was launched with `--remote-debugging-port=9222`
- Close and relaunch if you opened it normally first

**No documents found?**
- Make sure you're on the statements/documents page
- Try navigating to "View All Documents" or similar
- Check that document links are visible on the page

**Download failed?**
- Some documents require clicking through confirmation dialogs
- The script will skip those and continue with others
- You can download those manually after

## 📞 Get Help

Just message me:
- "Help with bank downloads"
- "Something's not working"
- "How do I [specific question]"

I'll guide you through it! 🤖
