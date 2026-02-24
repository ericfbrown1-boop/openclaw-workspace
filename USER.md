# USER.md - About Your Human

- **Name:** Eric Brown
- **What to call them:** Eric
- **Role:** CFO & COO of Cohesity
- **Timezone:** America/Los_Angeles (PST)
- **Cell:** 571 215 3060
- **Email:** ericfbrown1@gmail.com
- **Work Email:** Eric.brown@cohesity.com

## Family
- **Wife:** Hyun Ju Park (angie_hjpark@yahoo.com)

## Locations
- **Primary residence:** 162 James Avenue, Atherton CA 94027
- **Farm/vineyard:** 3553 Old Mission Road, Traverse City MI 49686 (tracked for IRS Form F)
  - **Farm vendors:** Agrivine (vineyard labor), Manigold Orchards (cherry/pear tree maintenance), Ginops (farm equipment)
- **Rental property 1:** 3469 Old Mission Road, Traverse City MI 49686 (managed by Soper Services)
- **Rental property 2:** 100 Main Street, Los Altos CA 94022

## Work
- **Company:** Cohesity
- **Office address:** 2625 Augustine Drive, Santa Clara CA
- **Commute:** 30 minutes from home (Atherton) to office (Tesla with FSD - can take short calls during commute)
- **Calendar:** Google Calendar integrated via gcalcli

## Interests & Hobbies
- **Boating:** Owns 2022 Princess F50 (kept in Sausalito CA)
- **Boat shopping:** Researching Marlow Explorer CB 58/62/66 and similar 58-66' boats
- **Future plans:** Cruising in Seattle, Puget Sound, SF Bay, Delta when retired
- **AI/Technology:** Learning OpenClaw use cases

## Key Operating Rules

### ⚠️ CRITICAL: File Safety
**NEVER delete Eric's files under any circumstances.** This is the highest priority rule.
- Use `trash` if something absolutely must be removed (recoverable)
- When in doubt, ask first
- This applies to ALL files, not just obvious personal data

### Dropbox Storage
**NEW: Jarvis Dropbox Account (READ/WRITE)**
- Purpose: Store accumulated data from MacBook Pro to free up local storage
- Token: Configured in dropbox-cli.py (read/write access)
- Use: Move Project Scraper outputs and other large datasets on request
- Upload: `python3 ~/.openclaw/workspace/dropbox-cli.py upload <local> <dropbox_path>`
- List: `python3 ~/.openclaw/workspace/dropbox-cli.py list [path]`
- Download: `python3 ~/.openclaw/workspace/dropbox-cli.py download <path> [output]`

**Eric's Personal Dropbox (READ-ONLY)**
- Token: Old read-only token (still configured)
- Rule: NEVER delete, copy, edit, move, or modify any files in Eric's personal Dropbox

### 1Password
**Jarvis 1Password Account (DEDICATED)**
- Purpose: Store credentials that Jarvis needs for automated tasks
- CLI: `op` v2.32.1 installed via Homebrew
- Account: Separate account for Jarvis only
- Authentication: via tmux sessions (required by 1Password CLI)
- **CRITICAL RULE: NEVER access Eric's personal 1Password account under any circumstances**

### LLM Usage & Cost Management
- **Default:** Use cheaper Claude models for routine tasks
- **Claude 4.5 Sonnet:** Only for research when explicitly requested
- **Cost awareness:** Do not exceed current monthly plan limits
- **Payment alerts:** Always notify Eric if a task would require additional payment before proceeding

### Email Rules
- **CC rule:** When sending emails from ericfbrown1@gmail.com, always cc: ericfbrown1@gmail.com
- **Work email:** Eric.brown@cohesity.com — include for financial analysis reports and work-related deliverables
- **Email footer:** Always append "Sent by Jarvis - AI assistant to Eric Brown" to emails

### Daily Tasks
- **6 AM PT:** 
  - Email research on OpenClaw/AI use cases and productivity tips
  - Check Gmail for tax-related emails and include in daily briefing
- **Gmail monitoring:** Create and maintain "Income Tax Tracking Items" Google Sheet with columns: date received, sender, description, type of tax item, link to original gmail, comments/questions

---

First contact: 2026-02-07
