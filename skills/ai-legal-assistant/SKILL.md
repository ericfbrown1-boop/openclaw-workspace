---
name: ai-legal-assistant
description: "AI-powered contract review and legal document analysis. Use when: user says legal review, contract review, review this contract, analyze this agreement, check for risks, generate NDA, check compliance, compare contracts, or translate legalese. Triggers on: legal review, detailed legal review, review contract, contract analysis, contract risks, NDA, compliance check. NOT for: actual legal advice (always disclaim)."
---

# AI Legal Assistant

Contract review, risk analysis, document generation, and compliance checking — powered by Claude.

⚠️ **DISCLAIMER:** This is AI-generated legal analysis, NOT legal advice. Always recommend consulting a licensed attorney before signing.

## Commands

| Command | What It Does |
|---------|-------------|
| `review <file>` | Full contract review — Safety Score, clause analysis, recommendations |
| `risks <file>` | Deep risk analysis with severity scoring per clause |
| `compare <file1> <file2>` | Side-by-side contract comparison |
| `plain <file>` | Translate legalese to plain English |
| `negotiate <file>` | Counter-proposals for unfavorable clauses |
| `missing <file>` | Find protections that SHOULD be there but aren't |
| `nda <description>` | Generate custom NDA (mutual, one-way, employee, vendor) |
| `terms <url>` | Generate Terms of Service from website scan |
| `privacy <url>` | Generate Privacy Policy from website data collection scan |
| `agreement <type>` | Generate business agreements (freelancer, partnership, SOW, MSA) |
| `freelancer <file>` | Freelancer-perspective contract review |
| `compliance <url>` | Compliance gap analysis (GDPR, CCPA, ADA, PCI-DSS, SOC 2) |
| `report-pdf` | Generate professional PDF report from last analysis |

## Input Handling

Accept contracts as: **file path** (read directly), **pasted text**, or **URL** (web_fetch). If no input provided, ask for it.

## Full Contract Review (`review`)

The flagship command. Runs 5 analysis passes sequentially on the contract:

### Pass 1: Ingest & Classify
- Read contract text from file/paste/URL
- Classify type: Service Agreement, Employment, NDA, SaaS, Freelancer, Partnership, Lease, Sales, Investment
- Extract metadata: parties, dates, term, governing law, total value

### Pass 2: Clause Analysis (20% of score)
Identify and categorize every clause. Taxonomy:
- Payment/Financial, Liability/Indemnification, IP/Ownership, Termination, Confidentiality
- Non-Compete/Restrictive, Governance/Dispute, Data/Privacy, Insurance, Warranty
- Force Majeure, Amendment, Assignment, Survival, Representations

### Pass 3: Risk Scoring (25% of score)
Score each clause 1-10 against these dimensions:
- Financial Exposure (uncapped liability, penalties)
- Liability Transfer (indemnification shifted to one party)
- Restrictive Covenants (non-competes, exclusivity scope)
- Ambiguous Terms ("reasonable efforts", undefined terms)
- One-Sided Terms (unilateral amendment, asymmetric termination)
- Auto-Renewal Traps (short cancellation windows, price escalation)
- IP Overreach (work product capturing pre-existing IP)

**Hidden risk patterns to hunt:**
- Definition section landmines (broad definitions expanding liability)
- Cross-reference traps (Section X quietly references a waiver)
- Buried carve-outs (sub-sub-clause exceptions)
- Survival clauses (indefinite post-termination obligations)
- Incorporation by reference (external docs that can change)

### Pass 4: Compliance Check (20% of score)
Check against applicable frameworks:
- **GDPR** — Data Processing Agreement, lawful basis, data subject rights, cross-border transfers
- **CCPA/CPRA** — Service provider obligations, sale of data, opt-out rights
- **Employment Law** — Non-compete enforceability varies by state (CA bans most)
- **UCC** — Warranty disclaimers, limitation of liability
- **Consumer Protection** — Unconscionability, adhesion contract issues

### Pass 5: Recommendations (20% of score)
For each high/medium risk clause:
- Specific alternative language (copy-paste ready)
- Negotiation talking points
- Priority tier: P0 (dealbreaker), P1 (strong push), P2 (nice to have), P3 (acceptable)

### Contract Safety Score

| Score | Grade | Label | Action |
|-------|-------|-------|--------|
| 90-100 | A+ | Safe | Sign with minor review |
| 80-89 | A | Good | Minor issues to address |
| 70-79 | B | Fair | Some clauses need attention |
| 60-69 | C | Caution | Negotiate before signing |
| 40-59 | D | Risky | Strong negotiation needed |
| 0-39 | F | Dangerous | Do not sign without major revisions |

### Output Format

Save as `CONTRACT-REVIEW-[company]-[date].md`:
```
# Contract Review Report
⚠️ LEGAL DISCLAIMER: AI-generated, not legal advice.

## Contract Safety Score: [X]/100 — Grade: [X] ([Label])
## Executive Summary (3-4 sentences)
## Contract Details (table: type, parties, date, term, value, jurisdiction)
## Risk Dashboard (🔴 High / 🟡 Medium / 🟢 Low counts)
## Clause-by-Clause Analysis (grouped by risk level)
  - What it says (plain English)
  - Why it's risky
  - What you could lose
  - Recommended change (specific language)
## Missing Protections
## Obligations & Deadlines (table)
## Compliance Flags
## Negotiation Priorities (ranked)
## Recommended Next Steps (checklist)
```

## Risk Analysis (`risks`)

Deep clause-by-clause analysis only (no recommendations). For each clause scoring 5+:
- Risk score (1-10), category, financial exposure estimate
- Specific explanation of the danger
- Worst-case scenario description
- Comparison to industry standard

## Contract Comparison (`compare`)

Side-by-side analysis of two contracts/versions:
- Additions, removals, modifications flagged
- Risk delta (did changes make it better or worse?)
- Favorability shift per clause
- Red flags in new language

## Plain English Translation (`plain`)

Every clause translated to plain English. Flag deliberately confusing language with ⚠️.

## Counter-Proposals (`negotiate`)

For each unfavorable clause:
- Current language (quoted)
- Proposed replacement language (ready to redline)
- Talking points for negotiation call
- BATNA if they refuse
- Ready-to-send email template at the end

## Missing Protections (`missing`)

Scan for what SHOULD be in the contract but isn't. Common missing items by type:
- **All contracts**: Force majeure, dispute resolution, limitation of liability, severability, entire agreement
- **Service**: SLA, acceptance criteria, change order process, insurance requirements
- **Employment**: Severance, COBRA, equity vesting acceleration
- **SaaS**: Data portability, uptime guarantee, breach notification
- **Freelancer**: Kill fee, revision limits, portfolio rights

Urgency ratings: 🔴 Critical / 🟡 Important / 🟢 Recommended. Include ready-to-insert clause language.

## NDA Generator (`nda`)

Ask for: parties, type (mutual/one-way/employee/vendor), duration, jurisdiction, specific exclusions. Generate complete NDA with plain English annotations per section.

## Terms of Service (`terms`)

Scan URL with web_fetch. Detect: account features, payments, user content, API usage. Generate GDPR/CCPA compliant ToS with sections for each detected feature.

## Privacy Policy (`privacy`)

Scan URL with web_fetch. Detect: cookies, analytics, forms, third-party scripts, payment processing. Generate compliant privacy policy matching actual data collection.

## Business Agreements (`agreement`)

Types: freelancer, partnership, SOW, MSA, consulting, licensing, joint venture. Interactive Q&A to gather details, then generate complete agreement.

## Compliance Audit (`compliance`)

Scan URL with web_fetch. Check against: GDPR, CCPA, ADA/WCAG, PCI-DSS, CAN-SPAM, SOC 2. Score each framework (compliant/partial/non-compliant). Output remediation steps.

## PDF Report (`report-pdf`)

Generate professional PDF from the most recent analysis using the script at `scripts/generate_legal_pdf.py`. Requires `pip3 install reportlab`.

## Tone & Style

- Professional but accessible — explain legal concepts in plain English
- Risk indicators: 🔴 High Risk, 🟡 Medium Risk, 🟢 Low Risk
- Be specific about WHY something is risky, not just THAT it is
- Always suggest specific alternative language
- Include disclaimer at top of every output
