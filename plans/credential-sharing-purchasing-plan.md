# Jarvis: Secure Credential Sharing & AI Purchasing Authority
**Plan Version:** 1.0  
**Date:** 2026-03-11  
**Author:** Jarvis (AI Assistant to Eric Brown, CFO & COO, Cohesity)  
**Status:** Draft — Awaiting Eric's Review & Approval

---

## 1. Executive Summary

Eric Brown wants to extend two meaningful capabilities to Jarvis, his AI assistant running on OpenClaw:

1. **Secure credential sharing** — Jarvis gains access to a curated, minimal set of API tokens and service credentials so it can autonomously perform tasks like refreshing OAuth tokens, interacting with Google Workspace, managing Dropbox uploads, and operating SaaS subscriptions — without ever touching Eric's personal passwords, banking, or Cohesity corporate accounts.

2. **AI purchasing authority** — Jarvis gets a real virtual credit card with hard-coded merchant restrictions, monthly spend caps, and Telegram-based approval workflows — enabling it to autonomously pay for API credits, Railway deployments, domain names, and SaaS subscriptions within pre-approved guardrails.

**Why now?** Jarvis is already performing complex automation (financial analysis, scraping, memory management, coding pipelines), but repeatedly hits dead ends when OAuth tokens expire or when a service needs to be renewed. Giving Jarvis structured access eliminates these friction points without meaningfully increasing security risk — provided the architecture follows least-privilege principles.

**Core principle throughout:** Jarvis should have the minimum access required for each task, with clear kill switches, audit trails, and explicit separation from Eric's personal vault.

---

## 2. Credential Sharing Architecture

### 2.1 Recommended Solution: 1Password Shared Vault via Service Account

**Recommendation: Use a dedicated "Jarvis Shared" vault in Eric's 1Password Teams/Business account, accessed by Jarvis via a Service Account token.**

This is the cleanest architecture because:
- Both Eric and Jarvis already use 1Password (`op` CLI v2.32.1 installed)
- Service accounts provide per-vault, per-permission access with immutable scopes
- Token revocation is instant (disable/delete the service account)
- Full audit trail via 1Password usage reports
- No additional infrastructure to deploy or maintain
- End-to-end encrypted — 1Password never sees plaintext

**Prerequisites:**
- Eric must be on 1Password **Teams or Business** (not personal/family) — service accounts require an organizational account
- If Eric is currently on a personal plan, upgrade to Teams ($19.95/month for 10 users) or create a separate Teams account for this purpose

### 2.2 Vault Structure

```
Eric's 1Password Teams Account
├── [Personal] — Eric's personal passwords (NEVER accessible to Jarvis)
├── [Private] — Eric's private vault (NEVER accessible to Jarvis)
├── [Employee] — Built-in vault (NEVER accessible to Jarvis)
├── Shared (default) — Team shared vault (NEVER accessible to Jarvis)
│
├── 🤖 Jarvis-API [NEW VAULT] — READ-ONLY for Jarvis Service Account
│   ├── Anthropic API Key
│   ├── OpenAI API Key  
│   ├── Google OAuth Tokens (gmail, drive, calendar)
│   ├── Dropbox API Token
│   ├── Twitter/X Bearer Token (if monitoring enabled)
│   ├── Railway API Token
│   ├── Jarvis Virtual Card Details (Privacy.com)
│   └── OpenClaw Gateway Token
│
└── 🤖 Jarvis-Purchasing [NEW VAULT] — READ-ONLY for Jarvis Service Account
    ├── Privacy.com Virtual Card — Anthropic (merchant-locked, $500/mo)
    ├── Privacy.com Virtual Card — OpenAI (merchant-locked, $300/mo)
    ├── Privacy.com Virtual Card — Railway (merchant-locked, $100/mo)
    ├── Privacy.com Virtual Card — General SaaS (category-locked, $200/mo)
    └── Privacy.com Account API Key
```

**Key restrictions enforced by 1Password architecture:**
- Service accounts **cannot** be granted access to Personal, Private, Employee, or default Shared vaults
- The creator (Eric) can only grant access to vaults he has access to
- A service account cannot create another service account
- Permissions are immutable — must create a new service account to change scope

### 2.3 Creating the Jarvis Service Account

**Step-by-step (Eric performs this once):**

```bash
# 1. Sign in to 1Password.com (NOT op CLI — web UI required for initial setup)
# Navigate to: Developer > Directory > Other > Create a Service Account

# 2. Name it: "Jarvis-Agent"
# 3. Grant access to: "Jarvis-API" vault (READ only), "Jarvis-Purchasing" vault (READ only)
# 4. Do NOT grant vault creation permissions
# 5. Save the generated service account token to 1Password immediately
#    (shown only once — treat like a master password)

# After creation, Jarvis can use it:
export OP_SERVICE_ACCOUNT_TOKEN="ops_xxxxxxxxxxxxx"
op item get "Anthropic API Key" --vault "Jarvis-API" --field credential
```

**In Jarvis's OpenClaw configuration (openclaw.json), store the service account token via SecretRef:**
```json
{
  "skills": {
    "entries": {
      "1password": {
        "apiKey": {
          "source": "env",
          "provider": "env",
          "id": "OP_SERVICE_ACCOUNT_TOKEN"
        }
      }
    }
  }
}
```

The `OP_SERVICE_ACCOUNT_TOKEN` environment variable is set in `~/.zshrc` or via a launchd plist — never stored in plaintext in any file.

### 2.4 Access Controls: Read-Only vs Read-Write

| Vault | Jarvis Access | Eric Access | Notes |
|-------|--------------|-------------|-------|
| Jarvis-API | READ ONLY | FULL | Jarvis reads tokens; Eric rotates them |
| Jarvis-Purchasing | READ ONLY | FULL | Jarvis reads card details; Eric manages limits |
| Personal | NONE | FULL | Jarvis can never access this |
| Private | NONE | FULL | Jarvis can never access this |
| Employee | NONE | FULL | Jarvis can never access this |
| Shared (default) | NONE | FULL | Jarvis can never access this |
| Cohesity Work | NONE | FULL | Jarvis can never access this |

**What READ-ONLY means in practice:**
- Jarvis can retrieve item fields (tokens, API keys, card numbers)
- Jarvis cannot create, modify, or delete any items
- Jarvis cannot see vault metadata for vaults it lacks access to
- Every access is logged in 1Password usage reports

### 2.5 Credential Lifecycle

#### Rotation Strategy by Credential Type

| Credential | Type | Expiry | Rotation Method |
|-----------|------|--------|-----------------|
| Anthropic API Key | Static API key | Never (manual) | Eric rotates quarterly; updates Jarvis-API vault |
| OpenAI API Key | Static API key | Never (manual) | Eric rotates quarterly; updates Jarvis-API vault |
| Google OAuth (Gmail) | OAuth 2.0 token | Access: 1hr, Refresh: variable | Jarvis auto-refreshes via `gog` CLI; stores new token |
| Google OAuth (Calendar) | OAuth 2.0 token | Same as above | Same as above |
| Dropbox API Token | OAuth 2.0 token | Expires | Phase 2: auto-refresh flow |
| Railway API Token | Static API key | Never (manual) | Eric rotates as needed |
| Twitter/X Bearer | App-level token | Never (manual) | Eric rotates annually |
| Privacy.com API Key | Static API key | Never (manual) | Eric rotates if compromised |
| Virtual Card Numbers | Static | Never (card-level) | Eric creates new card to "rotate" |

#### OAuth Auto-Refresh (Phase 2)
- Jarvis should store refresh tokens in the Jarvis-API vault (Eric grants WRITE access to a specific `oauth-tokens` section)
- On each tool invocation requiring Google auth, Jarvis checks token expiry, auto-refreshes if within 5 minutes of expiry
- Failed refreshes trigger a Telegram alert to Eric: "⚠️ Google OAuth expired — please re-authenticate via `gog auth`"

### 2.6 Kill Switch Design

**Immediate revocation (seconds):**
```
Eric logs into 1Password.com → Developer → Service Accounts → "Jarvis-Agent" → Revoke Token
```

This instantly invalidates the service account token. All subsequent `op` CLI calls by Jarvis will fail with authentication errors. No further credential access is possible.

**Graduated kill switch levels:**
1. **Pause only purchasing:** Freeze all Privacy.com virtual cards (Privacy.com dashboard, 1 click)
2. **Pause credential access:** Revoke service account token (1Password, seconds)
3. **Full shutdown:** Revoke service account + freeze cards + kill OpenClaw gateway (`openclaw gateway stop`)
4. **Nuclear option:** Delete the "Jarvis-Agent" service account entirely (irreversible — must recreate)

**Pre-built kill switch script** (save to `~/bin/kill-jarvis.sh`):
```bash
#!/bin/bash
echo "🚨 Killing Jarvis access..."
# 1. Kill OpenClaw gateway
openclaw gateway stop
# 2. Alert Eric via Telegram (direct API call, no OpenClaw needed)
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${ERIC_CHAT_ID}&text=🚨 Jarvis access has been revoked. Gateway stopped."
echo "✅ Done. Manually revoke 1Password service account at: https://start.1password.com/developer-tools/active"
echo "✅ Manually freeze Privacy.com cards at: https://app.privacy.com"
```

---

## 3. What Credentials Jarvis Needs (Scoped List)

### 3.1 Required Credentials

| Service | What Jarvis Needs | Why | Risk Level |
|---------|------------------|-----|-----------|
| Anthropic | API key | Powers Claude (Jarvis itself) | Medium — rate limit abuse |
| OpenAI | API key | GPT models, Codex | Medium — cost abuse |
| Google (Gmail) | OAuth read+send | Daily briefings, monitoring | Medium — email access |
| Google (Calendar) | OAuth read | Scheduling context | Low — read-only |
| Google (Drive) | OAuth read/write | Reports, documents | Medium — file access |
| Dropbox | OAuth read/write | Report storage | Low — isolated account |
| GitHub (`gh` CLI) | Already configured | Code operations | Low — already works |
| Railway | API token | Deployment management | Medium — infra access |
| Privacy.com | API key | Virtual card management | High — financial |

### 3.2 Optional/Future Credentials

| Service | What Jarvis Needs | Notes |
|---------|------------------|-------|
| Twitter/X | Bearer token | Read-only monitoring; no posting |
| OpenClaw Gateway | Auth token | Already in environment |
| Telegram Bot | Already configured | Already works |

### 3.3 What Jarvis Should NEVER Have Access To

**Explicit exclusion list — hardcoded in vault design:**

- 🚫 Eric's personal 1Password vault
- 🚫 Banking credentials (BofA, Chase, Schwab, etc.)
- 🚫 Brokerage accounts (Schwab, Fidelity, Vanguard)
- 🚫 Social Security Number or government IDs
- 🚫 Eric's or Cohesity's corporate credit cards
- 🚫 Cohesity work systems (Salesforce, Workday, JIRA, internal SSO)
- 🚫 Eric's work email (Eric.brown@cohesity.com OAuth)
- 🚫 Wife Hyun Ju's credentials or accounts
- 🚫 Home security systems or smart locks
- 🚫 IRS, tax filing systems, or tax prep credentials
- 🚫 Apple ID / iCloud credentials
- 🚫 Any health-related accounts (insurance, medical portals)
- 🚫 Rental property management credentials (Soper Services)
- 🚫 Farm vendor accounts (Agrivine, Manigold, Ginops)
- 🚫 Real estate / mortgage accounts

---

## 4. Purchasing Authority Architecture

### 4.1 Recommended Card Provider: Privacy.com (Plus Plan)

**Recommendation: Privacy.com Plus plan with merchant-locked virtual cards per vendor.**

**Why Privacy.com over alternatives:**

| Provider | Type | Best For | Limitation for AI Use |
|---------|------|---------|----------------------|
| **Privacy.com** ✅ | Consumer virtual cards | Per-merchant locking, simple limits | Not a business card; no expense reports |
| Ramp | Corporate card | Team spend controls, receipt automation | Requires registered business entity |
| Brex | Corporate card | AI agent features (Fall 2025 release) | Requires business account, higher bar |
| Mercury | Business banking + cards | Startup banking | Requires Mercury business account |
| Stripe Issuing | Developer API | Building card products | Requires Stripe platform setup, complex |

**Privacy.com wins for this use case because:**
- Merchant-locked cards: a card issued for Anthropic.com ONLY works at Anthropic — if stolen, useless elsewhere
- Hard spending caps: any transaction exceeding the limit is automatically declined
- API access on Plus plan (needed for Jarvis to check balances, create single-use cards programmatically)
- Instant card freeze/close (1 click or API call)
- No business registration required (works on Eric's personal account)
- Real-time transaction notifications to Eric's phone

**Privacy.com Pricing:**
- Personal (free): 12 cards/month, no API access
- **Plus (~$10/month)**: 24 cards/month, API access, category-locked cards ← **Recommended**
- Pro (~$25/month): 36 cards/month, 1% cashback, no foreign transaction fees

### 4.2 Virtual Card Configuration

**Card-by-Card Setup:**

```
Card 1: "Jarvis → Anthropic"
  Type: Merchant-Locked (locks to Anthropic.com on first use)
  Monthly Limit: $300
  Transaction Limit: $300
  Purpose: API credits for Claude

Card 2: "Jarvis → OpenAI"
  Type: Merchant-Locked (locks to OpenAI.com on first use)
  Monthly Limit: $200
  Transaction Limit: $200
  Purpose: GPT/Codex API credits

Card 3: "Jarvis → Railway"
  Type: Merchant-Locked (locks to Railway.app on first use)
  Monthly Limit: $100
  Transaction Limit: $50
  Purpose: Railway deployment costs

Card 4: "Jarvis → General SaaS"
  Type: Category-Locked (Software/SaaS category only)
  Monthly Limit: $150
  Transaction Limit: $50
  Purpose: Domain renewals, SaaS subscriptions
  Note: Eric approves any new merchant before Jarvis uses this card

Card 5: "Jarvis → Single-Use Reserve"
  Type: Single-Use (auto-closes after one transaction)
  Limit: Set per-use by Eric via Telegram approval
  Purpose: One-off approved purchases

TOTAL MONTHLY CAP: ~$750/month maximum
```

**All cards stored in the Jarvis-Purchasing 1Password vault. Jarvis reads card details from 1Password; card numbers are NEVER stored in code, environment variables, or files.**

### 4.3 Approval Workflow Design

**Tier 1: Autonomous (no approval needed)**
Jarvis can spend autonomously if ALL of the following are true:
- Card is merchant-locked and already used at that merchant
- Amount ≤ current monthly cap
- Spending is for an existing subscription (auto-renewal)
- Eric has pre-approved this merchant in writing (Telegram message logged)

Examples: Paying Anthropic monthly API bill, Railway monthly hosting, existing SaaS auto-renewals.

**Tier 2: Telegram Approval Required**
Jarvis sends Eric a Telegram message and waits for "yes" before proceeding:
- New merchant never used before
- Single transaction > $50
- Amount would push monthly total > 80% of cap
- Category-locked card (General SaaS)

**Approval message format Jarvis sends:**
```
🛒 Purchase Request

Merchant: Vercel
Amount: $20/month
Purpose: Deploy Librarian Dashboard (from Project Plan: librarian-v1)
Card: Jarvis → General SaaS
Monthly spend after: $120/$150

Approve? Reply YES to confirm or NO to cancel.
Waiting 24h before auto-canceling.
```

**Tier 3: Eric-Only (Jarvis cannot proceed)**
- Any transaction > $200 single purchase
- Hardware purchases (MicroCenter, Apple, etc.)
- Travel (flights, hotels, car rentals)
- Any personal items
- Cohesity-related expenses
- Anything outside software/SaaS category

### 4.4 Receipt & Audit Trail

**Automated receipt capture:**
1. Privacy.com sends real-time transaction webhook → Jarvis captures via OpenClaw webhook
2. Jarvis fetches receipt/invoice from merchant email (Gmail monitoring)
3. Receipt stored in Dropbox: `/Jarvis Reports/Receipts/YYYY-MM/merchant-date-amount.pdf`
4. Monthly spend summary generated by Jarvis and sent to Eric via Telegram
5. All transactions logged to Google Sheet: "Jarvis Expense Log" (shared with Eric)

**IRS Compliance:**
- AI-made purchases are legally purchases by the human principal (Eric) — no different from an employee using a company card
- Receipts must be retained for 3 years minimum (7 years recommended for business expenses)
- Business purpose must be documented for each purchase — Jarvis logs this at time of purchase
- AI API costs (Anthropic, OpenAI) are immediately deductible business expenses under IRC §162
- Railway, domain, SaaS costs are also immediately deductible operational expenses
- Personal vs business classification: all Jarvis purchasing authority cards are exclusively for AI infrastructure — no personal use, ever
- Eric's accountant should be briefed on this setup annually

---

## 5. Security Risk Assessment

### 5.1 Threat Model

| Threat | Likelihood | Impact | Mitigation |
|--------|-----------|--------|-----------|
| **T1: Service account token compromised** | Low | Medium | Token stored only in env var; rotate quarterly; instant revocation |
| **T2: Jarvis prompt injection attack** | Medium | Medium | Jarvis never has write access to credential vaults; worst case reads tokens it already has |
| **T3: Virtual card number stolen** | Low | Low | Cards are merchant-locked; useless at other merchants; monthly caps limit loss |
| **T4: Jarvis makes unauthorized purchases** | Low | Low | Tier-3 purchases require Eric approval; merchant locks prevent scope creep |
| **T5: API key abuse (rate/cost)** | Low | Medium | Monthly caps per card; Anthropic/OpenAI have rate limits; Jarvis cannot modify spend limits |
| **T6: Google OAuth token stolen** | Low | High | OAuth tokens expire; only Jarvis-API vault readable; Eric's personal Google untouched |
| **T7: 1Password service account compromised** | Very Low | Medium | Read-only access; attacker can see API keys but not Eric's personal passwords |
| **T8: Privacy.com account compromised** | Very Low | Medium | Card freezing instant; monthly caps limit loss; merchant locks prevent broad use |
| **T9: MacBook Pro compromised** | Low | High | Jarvis runs on-device; if Mac is compromised, all local credentials at risk |
| **T10: OpenClaw gateway token stolen** | Low | Medium | Rotate gateway token; kill-jarvis.sh script handles emergency shutdown |

### 5.2 Blast Radius Analysis

**If Jarvis's service account token is compromised:**
- Attacker can read: API keys in Jarvis-API vault, virtual card details in Jarvis-Purchasing vault
- Attacker CANNOT access: Eric's personal vault, banking, personal passwords, Cohesity systems
- Financial exposure: limited to remaining monthly caps on virtual cards (max ~$750)
- Recovery: Revoke service account token → rotate all API keys in Jarvis-API vault → freeze Privacy.com cards → generate new cards

**If a virtual card number is stolen:**
- Card is merchant-locked → attacker can only charge the specific merchant (e.g., Anthropic)
- Monthly cap prevents runaway charges
- Recovery: Freeze card instantly via Privacy.com app → no further charges possible

**If Eric's personal 1Password is compromised (separately from Jarvis):**
- Jarvis is unaffected — Jarvis uses a service account that cannot access personal vault
- Jarvis's service account token lives in environment variable, not Eric's personal vault

**What is NOT protected by this architecture:**
- If Eric's MacBook Pro is fully compromised at the OS level, all local secrets (env vars, filesystem) are accessible to an attacker — this is outside the scope of this credential-sharing plan and requires device security hardening

### 5.3 Defense in Depth

```
Layer 1: Network     — OpenClaw gateway requires Tailscale/auth token
Layer 2: Auth        — 1Password 2SKD, service account token (immutable at creation)
Layer 3: Access      — Read-only vault permissions; no access to personal vaults
Layer 4: Spending    — Merchant-locked cards; hard monthly caps; tier-based approval
Layer 5: Monitoring  — Real-time transaction alerts to Eric's phone
Layer 6: Audit       — 1Password usage reports; Dropbox receipt archive; Google Sheet log
Layer 7: Kill Switch — Instant token revocation; instant card freeze
```

---

## 6. Implementation Phases

### Phase 1: Shared 1Password Vault with Read-Only API Credentials
**Timeline: 1-2 days | Effort: Low (Eric + 30 min)**

Tasks:
1. Verify Eric is on 1Password Teams/Business (or upgrade)
2. Create "Jarvis-API" vault in 1Password
3. Populate vault with: Anthropic API key, OpenAI API key, Dropbox token, Railway token
4. Create "Jarvis-Agent" service account with READ-ONLY access to Jarvis-API vault
5. Store service account token in Eric's personal vault AND in `~/.zshrc` as `OP_SERVICE_ACCOUNT_TOKEN`
6. Test: `op item get "Anthropic API Key" --vault "Jarvis-API" --field credential`
7. Update Jarvis's skill configuration to load API keys from 1Password at session start

**Success criteria:** Jarvis can retrieve API credentials from 1Password without tmux session auth.

**OpenClaw SecretRef integration:**
```json
// In openclaw.json skills section:
{
  "skills": {
    "entries": {
      "gog": {
        "apiKey": { "source": "exec", "provider": "exec", "id": "op item get 'Google OAuth' --vault 'Jarvis-API' --field credential" }
      }
    }
  }
}
```

### Phase 2: Auto-Refresh for OAuth Tokens
**Timeline: 1 week | Effort: Medium (Jarvis implements)**

Tasks:
1. Audit all OAuth tokens Jarvis uses (Google, Dropbox)
2. Build token-check wrapper: before any OAuth API call, verify token expiry
3. Implement auto-refresh flow using refresh_token stored in Jarvis-API vault
4. If refresh fails → Telegram alert to Eric with re-auth instructions
5. Store refreshed tokens back to Jarvis-API vault (requires upgrading to READ-WRITE on a scoped sub-vault for oauth-tokens only)
6. Test token expiry simulation

**Success criteria:** Jarvis never fails due to expired OAuth tokens; Eric is alerted if manual re-auth is needed.

### Phase 3: Virtual Card Setup with Spend Controls
**Timeline: 2-3 days | Effort: Low (Eric + 1 hour)**

Tasks:
1. Eric signs up for Privacy.com Plus plan ($10/month)
2. Link to a business credit card or bank account
3. Create 5 virtual cards per the configuration in Section 4.2
4. Create "Jarvis-Purchasing" vault in 1Password
5. Store each card's details in Jarvis-Purchasing vault (card number, expiry, CVV, billing zip)
6. Grant Jarvis service account READ-ONLY access to Jarvis-Purchasing vault
7. Configure Privacy.com to send transaction webhooks (for receipt capture)
8. Test: Jarvis reads Anthropic card from vault and validates card format

**Success criteria:** Jarvis can retrieve virtual card details from 1Password; all 5 cards configured with correct merchant locks and caps.

### Phase 4: Purchase Approval Workflow via Telegram
**Timeline: 1 week | Effort: Medium (Jarvis implements)**

Tasks:
1. Build Jarvis purchase request handler (checks tier, formats approval message)
2. Implement Telegram inline buttons for YES/NO approval
3. Implement 24-hour timeout (auto-cancel if no response)
4. Build audit log writer (Dropbox + Google Sheet)
5. Test full flow: Jarvis requests → Eric approves → Jarvis completes purchase → receipt logged

**Telegram approval format:**
```
🛒 Purchase Request #001

Merchant: Railway.app
Amount: $45.00
Purpose: Librarian Dashboard hosting (ongoing)
Card: Jarvis → Railway [merchant-locked]
This month's Railway spend: $45/$100

[✅ APPROVE]  [❌ DENY]
Expires in 24h
```

**Success criteria:** End-to-end purchase approval works via Telegram; receipts captured automatically.

### Phase 5: Librarian Dashboard Integration for Spend Tracking
**Timeline: 2-3 weeks | Effort: High (Coder agent implements)**

Tasks:
1. Add "Jarvis Spending" section to Librarian Dashboard
2. Fetch Privacy.com transaction history via API
3. Display: monthly spend by card, by merchant, vs caps
4. Show: pending approval requests
5. Allow Eric to approve/deny pending requests from Dashboard (not just Telegram)
6. Monthly spend report auto-generated as PDF → stored in Dropbox

**Success criteria:** Eric can see all Jarvis spending at a glance in the Dashboard; can approve requests from either Telegram or Dashboard.

---

## 7. Recommended Vendors — Pros, Cons, Pricing

### 7.1 Credential Management Options

#### 1Password Service Accounts ✅ RECOMMENDED
- **Pros:** Already in use, excellent security model, immutable permissions, usage audit trail, instant revocation, CLI support, SecretRef integration with OpenClaw, no additional infrastructure
- **Cons:** Requires Teams/Business plan; permissions immutable after creation (must create new SA to change scope)
- **Pricing:** 1Password Teams: $19.95/month for up to 10 users; Business: $7.99/user/month

#### 1Password Connect Server (Self-Hosted) — Not Recommended for This Use Case
- **Pros:** Unlimited re-requests after initial fetch, fully self-hosted, REST API, works without internet
- **Cons:** Requires Docker deployment, more complexity, overkill for a single AI agent on one Mac
- **Pricing:** Included with 1Password Teams/Business

#### HashiCorp Vault — Not Recommended
- **Pros:** Industry gold standard for enterprise secrets, policy engine, dynamic secrets
- **Cons:** Heavy infrastructure requirement, steep learning curve, not worth it for personal AI assistant use case
- **Pricing:** Open source (self-hosted) or HCP Vault from $0.03/hour

#### Doppler — Alternative Option
- **Pros:** Developer-friendly, excellent CLI, works with any language, team sync
- **Cons:** Cloud-hosted (less control), separate system from 1Password, additional monthly cost
- **Pricing:** Free for personal; Team plan $24/month

#### Bitwarden — Not Recommended (but viable)
- **Pros:** Open source, self-hostable, CLI available, cross-platform
- **Cons:** Less polished service account story, separate from Eric's existing 1Password setup
- **Pricing:** Free; Premium $10/year; Teams $3/user/month

### 7.2 Virtual Card Options

#### Privacy.com Plus ✅ RECOMMENDED
- **Pros:** Merchant-locked cards (best security feature), simple hard caps, API access, instant freeze, works for personal + business, proven track record, real-time alerts
- **Cons:** Not a business card (no expense categorization, no employee card management), no formal receipt management, personal account
- **Pricing:** Plus plan ~$10/month (24 cards/month, API access)

#### Ramp — Strong Alternative (if Eric opens a business account)
- **Pros:** True corporate card, excellent spend controls (per-merchant, per-MCC), built-in receipt management, accounting integrations (QuickBooks, NetSuite), 1.5% cashback, AI expense features
- **Cons:** Requires a registered business entity (Cohesity would work, but creates compliance complexity); harder to separate personal AI agent expenses from company expenses
- **Pricing:** Free for core features; no card fees

#### Brex — Not Recommended for This Use Case
- **Pros:** AI agent features announced (Fall 2025), programmable spend controls, strong integrations
- **Cons:** Designed for team/company use; using it for a personal AI assistant creates awkward organizational structures; minimum revenue requirements
- **Pricing:** Essentials: free; Premium: $12/user/month

#### Mercury — Not Recommended for This Use Case
- **Pros:** Developer-friendly, good API, virtual debit/credit cards, merchant controls
- **Cons:** Requires opening a Mercury business banking account (different from Eric's existing banking setup); adds banking complexity
- **Pricing:** Free banking; IO credit card available to Mercury customers

#### Stripe Issuing — Not Recommended
- **Pros:** Most programmatic option (full API control), can issue cards dynamically
- **Cons:** Requires building a Stripe platform integration; designed for building card products for others, not personal use; significant engineering effort
- **Pricing:** Per-transaction fees; no flat monthly cost

---

## 8. OpenClaw SecretRef Integration

OpenClaw's SecretRef system (documented in official OpenClaw docs) supports three providers:
- `env`: reads from environment variable
- `file`: reads from a local file
- `exec`: executes a command and uses stdout

**Recommended pattern for Jarvis API key access:**

```json
// openclaw.json — skills section
{
  "skills": {
    "entries": {
      "gog": {
        "apiKey": {
          "source": "exec",
          "provider": "exec", 
          "id": "op item get 'Google OAuth' --vault 'Jarvis-API' --field credential --reveal"
        }
      },
      "himalaya": {
        "apiKey": {
          "source": "exec",
          "provider": "exec",
          "id": "op item get 'Gmail App Password' --vault 'Jarvis-API' --field password"
        }
      }
    }
  }
}
```

This approach:
- Never stores credentials in plaintext in any config file
- Fetches fresh credentials at skill initialization
- Works with the 1Password service account token set in the environment
- Compatible with OpenClaw's sandboxed skill execution model

---

## 9. Appendix: What NOT to Share — Complete Exclusion List

The following items must NEVER be placed in any Jarvis-accessible vault:

### Financial
- Bank account credentials (BofA, Chase, Wells Fargo, etc.)
- Investment accounts (Schwab, Fidelity, Vanguard, Robinhood)
- Retirement accounts (401k, IRA)
- Mortgage account credentials
- Insurance account credentials (health, home, auto, life)
- Wire transfer credentials or routing/account numbers
- Tax filing credentials (TurboTax, H&R Block, IRS.gov)
- Accountant portal credentials

### Identity & Legal
- Social Security Number
- Driver's license / passport scan
- Legal document portals (estate planning, etc.)
- Notary or legal service credentials

### Work / Cohesity
- Cohesity SSO credentials
- Work email OAuth (Eric.brown@cohesity.com)
- Cohesity corporate card(s)
- Salesforce (Cohesity instance)
- Workday credentials
- JIRA/Confluence (Cohesity)
- Zoom (Cohesity account)
- Slack (Cohesity workspace)
- Snowflake (Cohesity data warehouse)
- SharePoint/OneDrive (Cohesity M365)
- Any Cohesity internal system

### Personal & Family
- Eric's personal email passwords (Gmail account password — not OAuth token)
- Hyun Ju's credentials (any account)
- Family health portal credentials
- Children's educational platform credentials
- Home security system (alarm codes, camera access)
- Smart home devices (locks, garage, etc.)
- Apple ID / App Store credentials
- iCloud credentials

### Property & Real Estate
- Rental property management (Soper Services)
- Farm vendor accounts (Agrivine, Manigold Orchards, Ginops)
- HOA portal credentials
- Real estate portal credentials (Zillow, MLS access)
- Boat management / marina credentials

### Hardware Purchases
- Jarvis is NOT authorized to purchase hardware of any kind
- MicroCenter, Apple Store, Amazon (hardware), Best Buy — all require Eric's direct involvement

---

## 10. Implementation Checklist

**Phase 1 — Eric's one-time setup actions:**
- [ ] Confirm 1Password account type (must be Teams or Business)
- [ ] Create "Jarvis-API" vault
- [ ] Add API credentials: Anthropic, OpenAI, Dropbox, Railway tokens
- [ ] Create "Jarvis-Agent" service account with READ-ONLY access to Jarvis-API
- [ ] Save service account token securely (Eric's personal vault + export in `~/.zshrc`)
- [ ] Test: run `op item get --vault "Jarvis-API"` from terminal

**Phase 1 — Jarvis implementation actions:**
- [ ] Update OpenClaw SecretRef config to load API keys via `op` CLI
- [ ] Test credential retrieval in a new session
- [ ] Update TOOLS.md with new vault/SA token setup notes
- [ ] Update daily briefing to report credential health status

**Phase 3 — Eric's Privacy.com setup:**
- [ ] Sign up for Privacy.com Plus ($10/month)
- [ ] Link bank account / funding source
- [ ] Create 5 virtual cards per Section 4.2 specifications
- [ ] Create "Jarvis-Purchasing" vault in 1Password
- [ ] Add all 5 card details to vault
- [ ] Grant Jarvis service account READ-ONLY access to Jarvis-Purchasing vault
- [ ] Configure Privacy.com transaction alerts to Eric's phone

---

*Plan authored by Jarvis. All implementation requires Eric's explicit approval before execution. Questions or modifications should be directed to Eric via Telegram.*

*Last updated: 2026-03-11*
