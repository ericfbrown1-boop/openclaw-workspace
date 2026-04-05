---
name: project-dynamo
description: >
  M&A carve-out analysis for Cohesity's potential acquisition of the Dell Data Domain
  business (Project Dynamo). Use when Eric asks about: Project Dynamo, Dell Data Domain
  acquisition, Data Domain carve-out, accretion/dilution analysis for Cohesity M&A,
  Dell data protection divestiture, or any strategic analysis of Cohesity acquiring
  a Dell division. Covers: deal rationale, standalone financials, valuation, accretion/
  dilution modeling, carve-out complexity (stranded costs, TSA), integration planning,
  competitive impact, regulatory risk, and go/no-go recommendation framework.
---

# Project Dynamo — Cohesity Acquisition of Dell Data Domain

## Overview

Project Dynamo is the internal codename for Cohesity's potential acquisition of the Dell
PowerProtect Data Domain business unit via a carve-out from Dell Technologies. This skill
provides the analytical framework, financial modeling approach, and decision criteria for
evaluating whether this deal is strategically sound and financially accretive.

## Target Profile: Dell PowerProtect Data Domain

### What It Is
- **Product family**: PowerProtect Data Domain (DD) — purpose-built backup appliances
- **Heritage**: Acquired by EMC in 2009 ($2.1B), passed to Dell via Dell-EMC merger (2016)
- **Market position**: Gartner Magic Quadrant Leader for 20 consecutive years (through 2025)
- **Installed base**: Estimated 60,000+ systems globally across Fortune 500 enterprises
- **Form factors**: Physical appliances (DD3300–DD9900), virtual edition (DDVE), cloud (DDMC)
- **Key capability**: Inline deduplication (up to 65:1 ratio), immutable snapshots, multi-cloud tiering

### Estimated Financials (derived from Dell ISG disclosures)
- Dell ISG "Storage" subsegment: ~$16.3B revenue (FY2025)
- Data protection (incl. Data Domain + PowerProtect DP): estimated $3.5–4.5B revenue
- Data Domain specifically: estimated $2.0–3.0B revenue (appliance + maintenance/support)
- Gross margin: estimated 55–65% (hardware + software + support mix)
- Recurring revenue (maintenance/support): estimated 40–50% of total Data Domain revenue
- EBITDA margin: estimated 25–35% (before corporate allocation adjustments)

## Analysis Framework

Execute each phase in order. Store intermediate outputs in `memory/project-dynamo/`.

### Phase 1: Strategic Rationale Assessment

Evaluate along five dimensions:

1. **Market consolidation logic**
   - Combined Cohesity + Veritas + Data Domain market share vs. competitors
   - Cohesity pre-Veritas: ~5% market share; post-Veritas: ~19%; with DD: potentially 30%+
   - Competitive positioning vs. Rubrik, Commvault, Veeam
   - Does this create a defensible #1 position?

2. **Product portfolio complementarity**
   - Cohesity DataProtect: modern, cloud-native, secondary storage
   - Veritas NetBackup: legacy enterprise, large installed base
   - Data Domain: purpose-built appliance, deduplication IP, hardware revenue stream
   - Gap analysis: what does DD add that Cohesity/Veritas doesn't have?

3. **Customer base overlap & expansion**
   - DD customer base: Fortune 500, heavily enterprise, long refresh cycles (5–7 years)
   - Cross-sell opportunity: migrate DD customers to Cohesity platform over time
   - Retention risk: DD customers may evaluate alternatives during ownership change

4. **Technology & IP value**
   - Data Domain OS (DDOS) and deduplication algorithms
   - Boost protocol for high-speed backup/restore
   - Cloud tiering and disaster recovery IP
   - Patent portfolio assessment

5. **Seller motivation & timing**
   - Dell ISG strategic focus shifting to AI servers and storage
   - Data protection declining as % of Dell revenue — non-core asset
   - Dell may prefer divestiture over continued R&D investment
   - Timing: post-Veritas integration adds execution risk for Cohesity

### Phase 2: Standalone Financial Model

Build a 5-year standalone model for the Data Domain business:

```
Key assumptions to research & validate:
├── Revenue: Base year, growth rate (-3% to +2% — mature product)
├── Revenue mix: Hardware vs. software vs. maintenance/support
├── Gross margin: By revenue stream
├── OpEx: R&D (product roadmap), S&M (dedicated sales?), G&A
├── CapEx: Minimal (fabless hardware model, OEM components)
├── Working capital: Inventory, AR/AP cycles
└── Stranded costs: What Dell corporate functions support DD today?
```

**Critical carve-out adjustments:**
- Identify shared services currently provided by Dell (IT, HR, finance, legal, facilities)
- Estimate stranded costs Dell will retain vs. costs Cohesity must replicate
- Model TSA (Transition Services Agreement) — typically 12–24 months, at cost + margin
- Standalone overhead build-out: $50–150M annually depending on scope

### Phase 3: Valuation

Apply multiple methodologies:

1. **Comparable transactions**
   - Cohesity/Veritas merger (~$7B implied; 14% market share)
   - Thoma Bravo/Veritas ($1.5B for data protection unit)
   - Broadcom/Symantec enterprise security ($10.7B)
   - OpenText/Micro Focus ($5.8B)
   - Relevant multiples: EV/Revenue 2–4x; EV/EBITDA 8–14x for mature data infrastructure

2. **DCF (Discounted Cash Flow)**
   - WACC: 10–12% (reflect integration risk premium)
   - Terminal growth rate: 1–2% (mature market)
   - FCF projections from standalone model
   - Scenario analysis: bull / base / bear

3. **Sum-of-parts**
   - Hardware appliance business value
   - Recurring maintenance/support stream value (higher multiple)
   - IP/patent portfolio value
   - Customer base / installed base value

4. **Implied valuation range**
   - Expected range: $4–8B depending on assumptions
   - Key sensitivity: recurring revenue % and retention rate

### Phase 4: Accretion/Dilution Analysis

Model the combined entity impact:

```
Accretion/Dilution Framework:
├── Cohesity standalone metrics (post-Veritas, pre-IPO estimates)
│   ├── Revenue: ~$2.5B+ (Cohesity + Veritas combined)
│   ├── EBITDA: estimated $500–700M
│   └── Growth rate: 5–10% (blended)
├── Data Domain standalone (from Phase 2)
├── Transaction assumptions
│   ├── Purchase price range ($4–8B)
│   ├── Funding mix: debt vs. equity vs. seller financing
│   ├── Interest rate on new debt
│   └── Shares issued (if equity component)
├── Synergies (cost + revenue)
│   ├── Cost synergies: $200–400M (eliminate duplicate R&D, G&A, sales overlap)
│   ├── Revenue synergies: $100–200M (cross-sell, upsell, platform migration)
│   └── Synergy realization timeline: 30% Y1, 60% Y2, 90% Y3
├── Integration costs
│   ├── One-time: $200–500M (IT migration, rebranding, severance, facilities)
│   └── Ongoing TSA costs: $50–100M/year for 12–24 months
└── Output
    ├── Pro forma EPS impact by year (Y1–Y3)
    ├── Pro forma leverage (Net Debt / EBITDA)
    ├── IRR at various exit multiples
    └── Payback period for acquisition premium
```

**Accretive if:**
- Combined EBITDA grows faster than standalone entities
- Cost synergies exceed incremental debt service
- Revenue retention exceeds 85% through transition
- Integration costs stay within modeled range

### Phase 5: Carve-Out Risk Assessment

Carve-outs from large conglomerates carry specific risks. Evaluate each:

| Risk Category | Key Questions | Mitigation |
|---|---|---|
| **Stranded costs** | What Dell shared services does DD rely on? What is the cost to replicate? | Negotiate TSA, build standalone infrastructure pre-close |
| **TSA dependency** | Duration, cost, service levels? What if Dell underperforms on TSA? | SLA with penalties, parallel build of internal capabilities |
| **Customer retention** | Will DD customers stay or use transition as buying event? | Retention programs, contractual lock-ins, early engagement |
| **Talent retention** | How many DD-dedicated employees? Key person risk? | Retention packages, cultural assessment, role clarity |
| **IP separation** | Clean separation of DD IP from broader Dell storage IP? | Legal audit, patent assignment agreements, licensing |
| **Channel disruption** | DD sold through Dell direct + channel partners — will channel remain? | Channel incentive programs, partner agreements |
| **Regulatory** | Antitrust review (combined 30%+ market share in backup appliances) | Pre-file with DOJ/FTC, prepare remedies if needed |
| **Integration overload** | Veritas integration still in progress — can Cohesity absorb DD simultaneously? | Phased integration, dedicated PMO, timeline buffer |

### Phase 6: Go / No-Go Decision Framework

Score each dimension 1–5 (5 = highly favorable):

| Criterion | Weight | Score | Weighted |
|---|---|---|---|
| Strategic fit with Cohesity vision | 20% | ? | ? |
| Financial accretion (Y2+) | 20% | ? | ? |
| Customer base quality & retention risk | 15% | ? | ? |
| Technology / IP value | 10% | ? | ? |
| Carve-out execution complexity | 15% | ? | ? |
| Regulatory risk | 10% | ? | ? |
| Integration capacity (given Veritas) | 10% | ? | ? |
| **TOTAL** | **100%** | | **?/5.0** |

**Thresholds:**
- **≥ 3.5**: Proceed to detailed due diligence and LOI
- **3.0–3.49**: Conditional proceed — address specific concerns first
- **< 3.0**: Do not proceed — risks outweigh strategic value

## Output Deliverables

For each analysis run, produce:

1. **Executive Summary** (2 pages) — deal thesis, key metrics, recommendation
2. **Strategic Rationale Memo** (3–5 pages) — Phase 1 findings
3. **Standalone Financial Model** — 5-year projections with assumptions
4. **Valuation Range** — Comparable transactions, DCF, sum-of-parts
5. **Accretion/Dilution Analysis** — Pro forma EPS, leverage, IRR
6. **Risk Matrix** — Phase 5 assessment with mitigations
7. **Go/No-Go Scorecard** — Phase 6 weighted scoring

Deliver as Word document emailed to ericfbrown1@gmail.com (cc: Eric.brown@cohesity.com).

## Data Sources

- Dell Technologies SEC filings (10-K, 10-Q) — ISG segment disclosures
- IDC Worldwide Quarterly Purpose-Built Backup Appliance Tracker
- Gartner Magic Quadrant for Backup and Data Protection Platforms
- Cohesity internal financials (Eric has access)
- Comparable M&A transactions (Capital IQ, PitchBook, public filings)
- KPMG/EY carve-out benchmarking studies
- See `references/carve-out-best-practices.md` for detailed carve-out methodology
- See `references/data-domain-market-intel.md` for product and competitive intelligence

## Confidentiality

⚠️ **Project Dynamo is HIGHLY CONFIDENTIAL.** Do not reference this project name, deal
structure, or any analysis outside of direct communications with Eric. Do not include
Project Dynamo content in daily briefings, group chats, or any external communications.
All documents should be marked "CONFIDENTIAL — Project Dynamo" in headers/footers.
