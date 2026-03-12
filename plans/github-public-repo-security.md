# GitHub Public Repository Security Report
**Prepared for:** Eric Brown, CFO/COO  
**Date:** March 8, 2026  
**Repos Reviewed:** `ericfbrown1-boop/ContractAnalyzer` · `ericfbrown1-boop/ProjectScraper`  
**Status:** 🔴 STOP — Critical issues found in both repos. Do NOT make public yet.

---

## 🚨 CRITICAL FINDINGS (Action Required Before Anything Else)

### Finding 1 — Hardcoded Gmail App Password in ContractAnalyzer (SEVERITY: CRITICAL)
**File:** `send_report_email.py` (committed to git history, Phase 1 commit, March 7, 2026)  
```
PASSWORD = "sxugqgnxpfgvxcik"
```
This is a Gmail app password, hardcoded in source code, committed to the repository's git history. If this repo becomes public, **this credential is immediately accessible to anyone** and could be used to send email as your Gmail account.

**Immediate action:** Revoke this Gmail app password NOW, even before any git cleanup, as the hash may already be indexed by GitHub's secret scanning. Go to: Google Account → Security → 2-Step Verification → App passwords → delete it.

### Finding 2 — Cohesity Confidential Documents in ProjectScraper (SEVERITY: CRITICAL)
The ProjectScraper git repository has committed highly sensitive Cohesity internal and competitive intelligence files including:
- `Cohesity/PricingCommittee_M365_Feb26.pptx` — Internal Cohesity pricing committee presentation
- `Cohesity/pricing_data.csv`, `cost_calculator.csv` — Internal pricing data  
- `Commvault/data/cohesity_pricing_intel.md` — Pricing intelligence
- `Cohesity/COHESITY_INTELLIGENCE_REPORT.md`, `EXECUTIVE_SUMMARY.md`
- Competitive data on Rubrik, Veeam, Commvault (tar.gz archives, full analysis sets)
- `Build_Your_Own_Jarvis_Complete_Guide.docx` (and backups) — Internal guide with API config details

**Making this repo public would expose Cohesity confidential business information to competitors, the public, and potentially violate NDAs or employment agreements.** This is not just a security issue — it's a legal and professional risk.

**Recommendation:** ProjectScraper should likely NOT be made public without significant restructuring (the actual crawler code separated from all intelligence output). See Section 5 for options.

### Finding 3 — Morgan Stanley Contract Data Referenced in ContractAnalyzer (SEVERITY: HIGH)
The `send_report_email.py` body text contains detailed Morgan Stanley contract terms (specific dollar values, discount structures, escalation caps, schedule dates). While actual PDFs are gitignored, **the email script itself reveals confidential client contract details in the git history**.

---

## 1. Risk Assessment

### ContractAnalyzer (`ericfbrown1-boop/ContractAnalyzer`)

| Risk | Severity | Status |
|------|----------|--------|
| Gmail app password hardcoded in `send_report_email.py` | 🔴 CRITICAL | In git history since commit `3727817` |
| Morgan Stanley contract terms in script body | 🟠 HIGH | In git history |
| MinIO default credentials (`minioadmin`/`minioadmin`) in `config.py` | 🟡 MEDIUM | Defaults only, but visible |
| Default PostgreSQL credentials in `config.py` | 🟡 MEDIUM | `contract_user:contract_pass` — clearly dev defaults |
| `DROPBOX_CLI` path hardcoded to `/Users/ericbrown/` | 🟡 MEDIUM | Reveals local filesystem paths |
| LLM config (`ANTHROPIC_API_KEY: str = ""`) | 🟢 LOW | Empty default is fine; good practice |
| `input_pdfs/` directory properly gitignored | ✅ Good | Contract files not committed |
| `.env` file properly gitignored | ✅ Good | Credentials not committed |

**Overall:** ContractAnalyzer has ONE critical issue (the Gmail password in history) and is otherwise reasonably well-secured. Can be made public after history cleanup + password rotation.

### ProjectScraper (`ericfbrown1-boop/ProjectScraper`)

| Risk | Severity | Status |
|------|----------|--------|
| Cohesity internal pricing deck (`PricingCommittee_M365_Feb26.pptx`) committed | 🔴 CRITICAL | In git history |
| Cohesity competitive intelligence reports committed | 🔴 CRITICAL | In git history |
| Rubrik/Commvault/Veeam competitive analyses committed | 🟠 HIGH | In git history |
| Internal `Build_Your_Own_Jarvis` guide committed | 🟠 HIGH | Contains API config details |
| Hardcoded path to `HOME` directory in crawler scripts | 🟡 MEDIUM | Reveals local path structure |
| `.gitignore` only excludes `venv/`, `__pycache__/`, `.DS_Store` | 🟠 HIGH | Too minimal — doesn't exclude output data |
| Playwright `node_modules` in tracked files (code/node_modules) | 🟡 MEDIUM | Bloats repo, not excluded |

**Overall:** ProjectScraper requires major surgery before it can be public. The data outputs (competitive intelligence) should never be in the same repo as the crawler code if this is to be public.

---

## 2. Pre-Publication Checklist

### ContractAnalyzer — Step-by-Step

**Phase 1: Immediate Credential Actions (Do NOW)**
- [ ] **1a.** Revoke the Gmail app password `sxugqgnxpfgvxcik` at accounts.google.com → Security → App passwords
- [ ] **1b.** Generate a new Gmail app password and store it in 1Password (your Jarvis vault)
- [ ] **1c.** Update `send_report_email.py` to load password from environment variable: `os.environ.get("GMAIL_APP_PASSWORD")`

**Phase 2: Pre-Cleanup Scan**
- [ ] **2a.** Install and run TruffleHog on the full repo history (see Section 3)
- [ ] **2b.** Install and run Gitleaks scan
- [ ] **2c.** Review all scan output before proceeding

**Phase 3: Git History Cleanup**
- [ ] **3a.** Use BFG Repo-Cleaner or `git filter-repo` to scrub `send_report_email.py` from history (or replace with sanitized version — see Section 5)
- [ ] **3b.** Force-push cleaned history to GitHub
- [ ] **3c.** Contact GitHub support to purge cached views (optional but good practice)

**Phase 4: Code Cleanup**
- [ ] **4a.** Confirm `send_report_email.py` now uses env vars (no hardcoded credentials)
- [ ] **4b.** Replace all absolute paths (`/Users/ericbrown/...`) with relative paths or env vars
- [ ] **4c.** Remove any Morgan Stanley-specific content from script bodies/comments (replace with `[CLIENT_NAME]` placeholders)
- [ ] **4d.** Review `scripts/*.py` for any hardcoded email addresses, paths, or client names
- [ ] **4e.** Update `.gitignore` (see Section 4)

**Phase 5: Final Checks**
- [ ] **5a.** Add `LICENSE` file (MIT recommended — see Section 7)
- [ ] **5b.** Add `SECURITY.md` (template in Section 6)
- [ ] **5c.** Update `README.md` — remove any client-specific references, add setup instructions for env vars
- [ ] **5d.** Enable GitHub Dependabot on the repo (see Section 6)
- [ ] **5e.** Run `pip audit` on `requirements.txt` for vulnerability check
- [ ] **5f.** Final review: `git log --all -p | grep -E "sk-ant|password|secret|token"` to confirm clean

### ProjectScraper — Step-by-Step

**Decision Point First: What should be public?**

The crawler code (files in `code/`) is the shareable portion. All the data output (Cohesity/, Rubrik/, Commvault/, Veeam/, BI_Tools/, *.docx, *.tar.gz) should NOT be public.

**Option A: Clean & Make Public (Complex — 2-3 hours)**
- [ ] **A1.** Create a new branch `public-clean`
- [ ] **A2.** Remove all intelligence output directories from git history using BFG
- [ ] **A3.** Keep only: `code/`, `.github/`, `README.md`, `LICENSE`, `SECURITY.md`, `.gitignore`
- [ ] **A4.** Rewrite `.gitignore` to exclude output directories going forward
- [ ] **A5.** Run TruffleHog + Gitleaks on cleaned history

**Option B: Create a Fresh Public Repo (Recommended — 30 minutes)**
- [ ] **B1.** Create a NEW repo `ProjectScraper-public` (or just `WebCrawler`)
- [ ] **B2.** Copy only the `code/` directory files to it
- [ ] **B3.** Write a clean README describing what it does (without mentioning Cohesity targets)
- [ ] **B4.** This avoids all git history risk entirely

**Option C: Keep Private**
- [ ] Simply don't make it public. The intelligence output has ongoing value for competitive work.

**My recommendation: Option B for ProjectScraper.** Fresh repo with just the code, no history baggage.

---

## 3. Recommended Tools

### Tools to Install Now

```bash
# TruffleHog — scans git history for 800+ secret types including Anthropic, OpenAI keys
brew install trufflehog

# Gitleaks — fast git history scanner, great for pre-commit hooks
brew install gitleaks

# BFG Repo-Cleaner — fastest way to purge files/strings from git history
brew install bfg

# git-filter-repo — modern alternative to git filter-branch (more reliable)
pip install git-filter-repo

# pip-audit — scan Python dependencies for known vulnerabilities
pip install pip-audit
```

### Run These Commands

```bash
# === ContractAnalyzer ===
cd ~/ContractAnalyzer

# 1. Scan full history for secrets (TruffleHog)
trufflehog git file://. --since-commit HEAD~20 --only-verified

# 2. Scan with Gitleaks
gitleaks detect --source . --log-opts="--all"

# 3. Check Python dependencies for vulnerabilities
pip-audit -r api/requirements.txt

# === ProjectScraper ===
cd ~/ProjectScraper

# 4. Scan full history
trufflehog git file://. --since-commit HEAD~5 --only-verified
gitleaks detect --source . --log-opts="--all"

# 5. Check Node.js dependencies
npm audit
```

### What TruffleHog Detects
- Anthropic API keys (`sk-ant-*`)
- OpenAI API keys (`sk-proj-*`, `sk-*`)
- Google/Gmail tokens
- Dropbox access tokens
- AWS credentials
- Database connection strings with passwords
- 800+ additional secret patterns

---

## 4. .gitignore Templates

### ContractAnalyzer — Enhanced `.gitignore`
Add the following to the existing `.gitignore`:

```gitignore
# ─── Secrets & Credentials ───────────────────────────────
.env
.env.*
!.env.example
*.pem
*.key
credentials.json
secrets.json
config.local.py
*_credentials.*

# ─── Sensitive Script Outputs ────────────────────────────
send_report_email.py.local
output/
input_pdfs/

# ─── Python ──────────────────────────────────────────────
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
env/
.venv/
*.egg-info/
dist/
build/
.pytest_cache/
.mypy_cache/
.coverage
htmlcov/
*.log

# ─── Jupyter / Notebooks ─────────────────────────────────
.ipynb_checkpoints/
*.ipynb

# ─── Node / Frontend ─────────────────────────────────────
node_modules/
dist/
.vite/
.next/
.nuxt/
*.tsbuildinfo

# ─── Docker ──────────────────────────────────────────────
.docker/

# ─── OS ──────────────────────────────────────────────────
.DS_Store
.DS_Store?
._*
Thumbs.db
Desktop.ini

# ─── IDE ─────────────────────────────────────────────────
.vscode/
.idea/
*.swp
*.swo
```

### ProjectScraper — Enhanced `.gitignore` (for public version)
Complete replacement `.gitignore`:

```gitignore
# ─── Secrets & Credentials ───────────────────────────────
.env
.env.*
!.env.example
*.pem
*.key
credentials.json
secrets.json

# ─── Intelligence Output (NEVER commit) ──────────────────
Cohesity/
Rubrik/
Commvault/
Veeam/
AI_Cluster_Research/
BI_Tools/
Expanded_Competitive_Analysis/
Sigma_Complete/
Unstructured/
*.tar.gz
*.docx
*.pptx
*.xlsx
ocr_output/
ocr_samples/
ocr_tools/

# ─── Node.js ─────────────────────────────────────────────
node_modules/
dist/
.npm/
*.tsbuildinfo
package-lock.json  # optional — include this if you want reproducible builds

# ─── Playwright ──────────────────────────────────────────
test-results/
playwright-report/
playwright/.cache/

# ─── Logs & Output ───────────────────────────────────────
*.log
logs/
output/
downloads/

# ─── Python (utility scripts) ────────────────────────────
__pycache__/
*.pyc
venv/
.venv/

# ─── OS ──────────────────────────────────────────────────
.DS_Store
Thumbs.db
```

---

## 5. Git History Cleanup

### Cleaning ContractAnalyzer (Remove Gmail Password from History)

The Gmail password `sxugqgnxpfgvxcik` was committed in `3727817` (Phase 1 commit). Here are two methods:

#### Method A: Replace the secret string with BFG (Recommended)

```bash
# Step 1: Create a file listing strings to replace
echo "sxugqgnxpfgvxcik" > /tmp/passwords.txt

# Step 2: Make a fresh clone (BFG needs a bare clone)
cd ~
git clone --mirror https://github.com/ericfbrown1-boop/ContractAnalyzer.git ContractAnalyzer-mirror.git

# Step 3: Run BFG to replace all occurrences
bfg --replace-text /tmp/passwords.txt ContractAnalyzer-mirror.git

# Step 4: Cleanup and force-push
cd ContractAnalyzer-mirror.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force

# Step 5: Re-clone fresh copy
cd ~
git clone https://github.com/ericfbrown1-boop/ContractAnalyzer.git ContractAnalyzer-clean
```

#### Method B: Remove the entire file from history

```bash
# If you want to remove send_report_email.py entirely from history
bfg --delete-files send_report_email.py ContractAnalyzer-mirror.git
```

#### Method C: git filter-repo (More control)

```bash
# Install
pip install git-filter-repo

# Replace the password in all history
cd ~/ContractAnalyzer
git filter-repo --replace-text /tmp/passwords.txt

# Force push
git push origin --force --all
git push origin --force --tags
```

### ⚠️ Post-Cleanup: Required Actions
1. **Rotate the Gmail app password immediately** (if not done yet)
2. All collaborators must re-clone the repo (history is rewritten)
3. Delete any GitHub forks if they exist
4. File a GitHub support ticket to purge cached data: https://support.github.com/request/remove-data

### Cleaning ProjectScraper (Remove Confidential Data)

**Recommended: Use Option B (new repo) from Section 2 instead.**

If you must clean the existing repo:

```bash
# Create list of directories/files to remove
# BFG can delete entire directories
cd ~
git clone --mirror https://github.com/ericfbrown1-boop/ProjectScraper.git ProjectScraper-mirror.git

# Remove sensitive directories from all history
bfg --delete-folders Cohesity --delete-folders Rubrik --delete-folders Commvault --delete-folders Veeam --delete-folders BI_Tools --delete-folders AI_Cluster_Research ProjectScraper-mirror.git

# Also remove .docx and .pptx files
bfg --delete-files '*.docx' --delete-files '*.pptx' --delete-files '*.tar.gz' ProjectScraper-mirror.git

# Finalize
cd ProjectScraper-mirror.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

---

## 6. Ongoing Security (After Going Public)

### Enable These GitHub Features Immediately After Making Public

**1. Secret Scanning (Free on Public Repos)**
Go to: Repo → Settings → Security → Code security and analysis
- Enable "Secret scanning" — GitHub will scan for 200+ secret types
- Enable "Push protection" — blocks pushes containing secrets before they land

**2. Dependabot Alerts (Free)**
- Enable "Dependabot alerts" for vulnerable dependencies
- Enable "Dependabot security updates" to auto-create PRs for patches

**3. Code Scanning with CodeQL (Free on Public Repos)**
Add to `.github/workflows/codeql.yml`:
```yaml
name: "CodeQL"
on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]
  schedule:
    - cron: '0 6 * * 1'

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      security-events: write
    strategy:
      matrix:
        language: [ 'python' ]  # Add 'javascript' for ProjectScraper
    steps:
    - uses: actions/checkout@v4
    - uses: github/codeql-action/init@v3
      with:
        languages: ${{ matrix.language }}
    - uses: github/codeql-action/autobuild@v3
    - uses: github/codeql-action/analyze@v3
```

**4. Branch Protection Rules**
Go to: Repo → Settings → Branches → Add rule for `main`
- Require pull request reviews before merging
- Require status checks to pass
- Prevent force pushes (ironically, disable after history cleanup)

**5. SECURITY.md File**
Create this file in the root of each repo:

```markdown
# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| latest  | ✅ Yes    |

## Reporting a Vulnerability

Please do NOT report security vulnerabilities through public GitHub issues.

Email security concerns to: ericfbrown1@gmail.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact

You can expect a response within 48 hours.
```

**6. Ongoing Monitoring — Set Up Pre-commit Hook**

```bash
# Install pre-commit (Python)
pip install pre-commit

# Create .pre-commit-config.yaml in repo root:
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
EOF

# Install the hook
pre-commit install
```

This blocks any future commit containing secrets.

---

## 7. License Recommendation

### For ContractAnalyzer
**Recommend: MIT License**

- ContractAnalyzer is a personal tool you built; sharing it publicly is primarily for portfolio/community value
- MIT is the most permissive — lets anyone use, fork, and build on it
- No patent protection needed for this use case
- Apache 2.0 is a good alternative if you want explicit patent protection

```
MIT License

Copyright (c) 2026 Eric Brown

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

### For ProjectScraper (if made public)
**Recommend: MIT License** — same reasoning; it's a crawler utility tool.

### What to Avoid
- **GPL** — would require anyone who uses your code to also open-source their modifications; usually too restrictive for personal tools
- **No license** — this actually means "all rights reserved" by default; contributors can't legally use it

---

## 8. Information Disclosure Risks (Summary Table)

| Item | Risk | Location | Mitigation |
|------|------|----------|------------|
| Gmail app password | 🔴 CRITICAL | ContractAnalyzer git history | BFG cleanup + rotate password |
| Cohesity pricing deck | 🔴 CRITICAL | ProjectScraper git history | New repo or BFG cleanup |
| Morgan Stanley contract terms | 🟠 HIGH | ContractAnalyzer script body | Sanitize to [CLIENT] placeholders |
| Absolute paths (`/Users/ericbrown/`) | 🟡 MEDIUM | Multiple files | Replace with relative paths or env vars |
| Default DB credentials | 🟡 MEDIUM | ContractAnalyzer config.py | OK since they're dev defaults only |
| Email address `ericfbrown1@gmail.com` | 🟡 LOW | Multiple scripts | Expected; use a public contact email in README |
| MinIO default admin password | 🟡 MEDIUM | ContractAnalyzer config.py | Note in README these are dev-only defaults |
| Competitive intel JSON files | 🟠 HIGH | ProjectScraper many dirs | Never commit to public repo |

---

## 9. Quick Reference: Priority Order

```
TODAY (before anything else):
  1. Revoke Gmail app password sxugqgnxpfgvxcik at accounts.google.com
  2. Decide: make ProjectScraper public as-is (bad), clean it (hard), or new repo (easy)

THIS WEEK (ContractAnalyzer):
  3. Install trufflehog + gitleaks, run full history scan
  4. BFG cleanup: remove Gmail password from git history
  5. Update send_report_email.py to use env vars
  6. Update .gitignore with enhanced template
  7. Add LICENSE + SECURITY.md
  8. Enable GitHub secret scanning + Dependabot
  9. Make ContractAnalyzer public ✅

THIS WEEK (ProjectScraper):
  10. Create fresh repo (Option B) with just code/ files
  11. Add proper .gitignore
  12. Add LICENSE + SECURITY.md + README
  13. Make new repo public ✅
  14. Keep original ProjectScraper repo private (has intelligence data)
```

---

*Report generated by Jarvis, AI assistant to Eric Brown | March 8, 2026*  
*Full report location: `/Users/ericbrown/.openclaw/workspace/plans/github-public-repo-security.md`*
