# Contract Analysis Taxonomy & Framework Research

> **Compiled:** 2026-03-06 | **Purpose:** Drive architecture for a production OCR + LLM contract analysis system

---

## Table of Contents

1. [Industry-Standard Contract Taxonomies](#1-industry-standard-contract-taxonomies)
2. [Comprehensive Field Extraction Schema](#2-comprehensive-field-extraction-schema)
3. [Contract Type Classification](#3-contract-type-classification)
4. [Clause-Level Taxonomy (CUAD-Extended)](#4-clause-level-taxonomy-cuad-extended)
5. [Risk Scoring Framework](#5-risk-scoring-framework)
6. [Best Practices for LLM-Based Contract Review](#6-best-practices-for-llm-based-contract-review)
7. [Reference Implementations & Open-Source Tools](#7-reference-implementations--open-source-tools)
8. [OCR + LLM Pipeline Architecture](#8-ocr--llm-pipeline-architecture)
9. [Recommended Production Taxonomy](#9-recommended-production-taxonomy)
10. [Model Recommendations](#10-model-recommendations)

---

## 1. Industry-Standard Contract Taxonomies

### 1.1 CUAD — Contract Understanding Atticus Dataset (Gold Standard)

- **Source:** The Atticus Project / NeurIPS 2021
- **Paper:** https://arxiv.org/abs/2103.06268
- **GitHub:** https://github.com/TheAtticusProject/cuad
- **HuggingFace:** https://huggingface.co/datasets/theatticusproject/cuad
- **Website:** https://www.atticusprojectai.org/cuad
- **Corpus:** 510 commercial legal contracts, 13,000+ expert annotations
- **Categories:** 41 clause types critical for M&A and corporate transactions
- **Format:** SQuAD 2.0-compatible JSON + CSV + Excel

**CUAD's 41 Clause Categories (Complete List):**

| # | Category | Type |
|---|----------|------|
| 1 | Document Name | Entity |
| 2 | Parties | Entity |
| 3 | Agreement Date | Date |
| 4 | Effective Date | Date |
| 5 | Expiration Date | Date |
| 6 | Renewal Term | Yes/No + Detail |
| 7 | Notice Period to Terminate Renewal | Yes/No + Detail |
| 8 | Governing Law | Entity (State/Country) |
| 9 | Most Favored Nation | Yes/No |
| 10 | Non-Compete | Yes/No |
| 11 | Exclusivity | Yes/No |
| 12 | No-Solicit of Customers | Yes/No |
| 13 | No-Solicit of Employees | Yes/No |
| 14 | Non-Disparagement | Yes/No |
| 15 | Termination for Convenience | Yes/No |
| 16 | Rofr/Rofo/Rofn (Right of First Refusal/Offer/Negotiation) | Yes/No |
| 17 | Change of Control | Yes/No |
| 18 | Anti-Assignment | Yes/No |
| 19 | Revenue/Profit Sharing | Yes/No |
| 20 | Price Restrictions | Yes/No |
| 21 | Minimum Commitment | Yes/No |
| 22 | Volume Restriction | Yes/No |
| 23 | IP Ownership Assignment | Yes/No |
| 24 | Joint IP Ownership | Yes/No |
| 25 | License Grant | Yes/No |
| 26 | Non-Transferable License | Yes/No |
| 27 | Affiliate License – Licensor | Yes/No |
| 28 | Affiliate License – Licensee | Yes/No |
| 29 | Unlimited/All-You-Can-Eat License | Yes/No |
| 30 | Irrevocable or Perpetual License | Yes/No |
| 31 | Source Code Escrow | Yes/No |
| 32 | Post-Termination Services | Yes/No |
| 33 | Audit Rights | Yes/No |
| 34 | Uncapped Liability | Yes/No |
| 35 | Cap on Liability | Yes/No |
| 36 | Liquidated Damages | Yes/No |
| 37 | Warranty Duration | Yes/No + Detail |
| 38 | Insurance | Yes/No |
| 39 | Covenant Not to Sue | Yes/No |
| 40 | Third Party Beneficiary | Yes/No |
| 41 | Matching Rights (ROFR/ROFO) | Yes/No |

### 1.2 LEDGAR — Large-Scale Multi-Label Legal Provision Classification

- **Paper:** https://aclanthology.org/2020.lrec-1.155/
- **Corpus:** ~100,000 provisions from ~60,000 contracts (SEC EDGAR filings)
- **Labels:** 12,000+ unique provision labels (multi-label)
- **Contract types:** Shareholder agreements, employment contracts, leases, NDAs, etc.
- **Use:** Clause-level classification and provision type identification
- **Part of LexGLUE benchmark:** https://github.com/coastalcph/lex-glue

### 1.3 SALI Alliance — Legal Matter Standard Specification (LMSS)

- **Website:** https://www.sali.org
- **GitHub:** https://github.com/sali-legal/LMSS
- **Standard:** LMSS 1.0, Revision 2
- **Tags:** 10,000+ standardized tags for legal matters
- **Code Sets:** Dozen+ standardized code sets (practice areas, document types, legal processes)
- **Adoption:** Bloomberg Law, Zuva, Litera, major law firms
- **Includes:** Document classification taxonomy (contributed by Zuva + Litera, Oct 2025)
- **Key value:** Industry-standard "common language" for legal data — free and open-source

### 1.4 WorldCC / IACCM — Most Negotiated Terms

- **Website:** https://www.worldcc.com
- **Annual Report:** "Most Negotiated Terms" (2015–2024)
- **URL:** https://www.worldcc.com/Portals/IACCM/Reports/Most-Negotiated-Terms-2024.pdf
- **Top negotiated terms consistently include:**
  1. Limitation of liability / liability caps
  2. Indemnification
  3. Liquidated damages / penalties
  4. Price / pricing changes
  5. Intellectual property
  6. Data protection / privacy
  7. Confidentiality
  8. Termination (for cause/convenience)
  9. Warranty
  10. Insurance
- **Use:** Prioritize these clauses for risk scoring — they're where the money is

### 1.5 Other Notable Standards & Datasets

| Standard/Dataset | Description | URL |
|-----------------|-------------|-----|
| **UNFAIR-ToS** | Terms of Service unfairness detection, 8 unfairness categories | Part of LexGLUE |
| **ContractNLI** | Natural language inference for contracts, 17 hypothesis categories | https://stanfordnlp.github.io/contract-nli/ |
| **EUR-LEX / EUROVOC** | 57k EU legislative documents, ~4.3k labels | EU legal taxonomy |
| **LexGLUE** | Legal NLU benchmark (7 datasets including LEDGAR, UNFAIR-ToS) | https://github.com/coastalcph/lex-glue |
| **ISO 82045** | Document management metadata standard | ISO standards body |
| **Dublin Core** | General metadata standard (applicable to legal docs) | https://www.dublincore.org |
| **AKOMA NTOSO** | XML standard for legal documents (OASIS) | Legislative/regulatory docs |

---

## 2. Comprehensive Field Extraction Schema

### 2.1 Document Identification

| Field | Data Type | Description |
|-------|-----------|-------------|
| `document_id` | string | Unique identifier (generated) |
| `document_name` | string | Title or name of agreement |
| `contract_type` | enum | See §3 for full classification |
| `contract_subtype` | string | Specific variant (e.g., "Software License," "Real Estate Lease") |
| `language` | string | ISO 639-1 code |
| `page_count` | integer | Total pages |
| `ocr_confidence` | float | Average OCR confidence score (0-1) |
| `file_hash` | string | SHA-256 of source document |

### 2.2 Party Identification

| Field | Data Type | Description |
|-------|-----------|-------------|
| `parties[]` | array | All parties to the agreement |
| `parties[].name` | string | Legal entity name |
| `parties[].role` | enum | `buyer`, `seller`, `licensor`, `licensee`, `landlord`, `tenant`, `employer`, `employee`, `service_provider`, `client`, `lender`, `borrower`, `other` |
| `parties[].entity_type` | enum | `corporation`, `llc`, `partnership`, `individual`, `government`, `nonprofit`, `trust` |
| `parties[].jurisdiction_of_formation` | string | State/country of formation |
| `parties[].address` | string | Principal address |
| `parties[].signatories[]` | array | Individuals who signed |
| `parties[].signatories[].name` | string | Signatory name |
| `parties[].signatories[].title` | string | Signatory title/role |
| `parties[].signatories[].date_signed` | date | Date of signature |

### 2.3 Key Dates & Durations

| Field | Data Type | Description |
|-------|-----------|-------------|
| `agreement_date` | date | Date of the agreement |
| `effective_date` | date | When terms take effect |
| `expiration_date` | date | When agreement expires |
| `term_duration` | string | Duration (e.g., "3 years") |
| `renewal_type` | enum | `auto_renewal`, `manual_renewal`, `none`, `evergreen` |
| `renewal_term` | string | Renewal period (e.g., "successive 1-year periods") |
| `renewal_notice_period` | string | Notice required to prevent renewal (e.g., "90 days") |
| `renewal_notice_deadline` | date | Calculated deadline for renewal notice |
| `termination_notice_period` | string | Notice required for termination |
| `key_milestones[]` | array | Milestone dates and descriptions |
| `last_amended_date` | date | Date of most recent amendment |

### 2.4 Financial Terms

| Field | Data Type | Description |
|-------|-----------|-------------|
| `total_contract_value` | currency | Total value over term |
| `annual_value` | currency | Annualized value |
| `currency` | string | ISO 4217 currency code |
| `payment_terms` | string | Payment schedule/terms (e.g., "Net 30") |
| `payment_frequency` | enum | `one_time`, `monthly`, `quarterly`, `annually`, `milestone_based` |
| `pricing_model` | enum | `fixed_fee`, `time_and_materials`, `per_unit`, `subscription`, `usage_based`, `hybrid` |
| `price_escalation` | string | Annual escalation clause (e.g., "CPI + 3%") |
| `minimum_commitment` | currency | Minimum purchase/spend commitment |
| `volume_discounts` | string | Volume discount tiers |
| `late_payment_penalty` | string | Penalty for late payment |
| `early_termination_fee` | string | Fee for early termination |
| `liquidated_damages` | string | Pre-agreed damages amount/formula |
| `liability_cap` | string | Maximum liability amount/formula |
| `revenue_sharing` | string | Revenue/profit sharing terms |
| `most_favored_nation` | boolean | MFN pricing clause present |
| `price_benchmarking` | boolean | Right to benchmark pricing |

### 2.5 Obligations & Performance

| Field | Data Type | Description |
|-------|-----------|-------------|
| `obligations[]` | array | Performance obligations |
| `obligations[].party` | string | Obligated party |
| `obligations[].description` | string | What must be done |
| `obligations[].deadline` | date/string | When it must be done |
| `obligations[].sla_metrics[]` | array | SLA targets |
| `deliverables[]` | array | Specific deliverables |
| `acceptance_criteria` | string | How deliverables are accepted |
| `acceptance_period` | string | Time to accept/reject (e.g., "30 days") |
| `service_levels[]` | array | Service level definitions |
| `service_levels[].metric` | string | What is measured |
| `service_levels[].target` | string | Target value (e.g., "99.9% uptime") |
| `service_levels[].remedy` | string | Remedy for failure (credits, etc.) |
| `audit_rights` | boolean | Right to audit performance/records |
| `reporting_requirements` | string | Required reports and frequency |

### 2.6 Risk Clauses

| Field | Data Type | Description |
|-------|-----------|-------------|
| `limitation_of_liability` | object | Liability limitation details |
| `limitation_of_liability.type` | enum | `capped`, `uncapped`, `mutual`, `one_sided` |
| `limitation_of_liability.cap_amount` | string | Cap amount or formula |
| `limitation_of_liability.exclusions` | string[] | Carve-outs from cap |
| `limitation_of_liability.consequential_damages_waiver` | boolean | Waiver of consequential damages |
| `indemnification` | object | Indemnification details |
| `indemnification.type` | enum | `mutual`, `one_sided`, `none` |
| `indemnification.scope` | string | What is covered |
| `indemnification.cap` | string | Any cap on indemnification |
| `indemnification.ip_indemnity` | boolean | IP infringement indemnity |
| `insurance_requirements[]` | array | Required insurance types and limits |
| `force_majeure` | boolean | Force majeure clause present |
| `force_majeure_events` | string | Covered events |
| `warranty_provisions[]` | array | Warranty terms |
| `warranty_duration` | string | How long warranties last |
| `disclaimer_of_warranties` | boolean | "AS IS" or warranty disclaimers |
| `representations` | string[] | Key representations made |

### 2.7 Termination Provisions

| Field | Data Type | Description |
|-------|-----------|-------------|
| `termination_for_cause` | boolean | Can terminate for breach |
| `termination_for_cause_cure_period` | string | Cure period before termination (e.g., "30 days") |
| `termination_for_convenience` | boolean | Can terminate without cause |
| `termination_for_convenience_notice` | string | Required notice period |
| `termination_for_insolvency` | boolean | Termination on bankruptcy/insolvency |
| `change_of_control_termination` | boolean | Termination on change of control |
| `material_adverse_change` | boolean | MAC clause termination |
| `post_termination_obligations` | string | Obligations surviving termination |
| `post_termination_services` | boolean | Transition/wind-down services |
| `survival_clauses` | string[] | Clauses that survive termination |
| `data_return_destruction` | string | Data handling post-termination |

### 2.8 Intellectual Property & Confidentiality

| Field | Data Type | Description |
|-------|-----------|-------------|
| `ip_ownership` | enum | `buyer`, `seller`, `joint`, `retained_by_creator`, `work_for_hire` |
| `ip_assignment` | boolean | IP assignment provision |
| `license_grant` | object | License details |
| `license_grant.type` | enum | `exclusive`, `non_exclusive`, `sole` |
| `license_grant.scope` | string | Licensed rights/field of use |
| `license_grant.territory` | string | Geographic scope |
| `license_grant.transferable` | boolean | Can sublicense/transfer |
| `license_grant.perpetual` | boolean | Perpetual or term-based |
| `license_grant.irrevocable` | boolean | Irrevocable |
| `source_code_escrow` | boolean | Source code escrow provision |
| `confidentiality_term` | string | Duration of confidentiality obligations |
| `confidentiality_scope` | string | What information is covered |
| `confidentiality_exceptions` | string[] | Standard exceptions |
| `data_protection_provisions` | boolean | GDPR/CCPA/privacy provisions |
| `data_processing_agreement` | boolean | DPA included or referenced |
| `data_handling_obligations` | string | Data security requirements |

### 2.9 Compliance & Governance

| Field | Data Type | Description |
|-------|-----------|-------------|
| `governing_law` | string | Governing law jurisdiction |
| `dispute_resolution` | enum | `litigation`, `arbitration`, `mediation`, `negotiation`, `hybrid` |
| `arbitration_body` | string | Arbitration institution (e.g., "AAA", "JAMS", "ICC") |
| `venue` | string | Forum/venue for disputes |
| `jury_waiver` | boolean | Waiver of jury trial |
| `class_action_waiver` | boolean | Waiver of class action rights |
| `regulatory_compliance` | string[] | Required regulatory compliance (e.g., "HIPAA", "SOX", "GDPR") |
| `anti_corruption` | boolean | Anti-bribery/FCPA provisions |
| `sanctions_compliance` | boolean | Sanctions/export control compliance |
| `esg_provisions` | boolean | Environmental/social/governance provisions |

### 2.10 Change Management & Assignment

| Field | Data Type | Description |
|-------|-----------|-------------|
| `amendment_procedure` | string | How contract can be amended |
| `amendment_requirement` | enum | `written_mutual_consent`, `unilateral`, `board_approval` |
| `anti_assignment` | boolean | Assignment restrictions |
| `assignment_consent_required` | boolean | Consent needed for assignment |
| `change_of_control` | object | Change of control provisions |
| `change_of_control.triggers` | string | What constitutes change of control |
| `change_of_control.consequences` | string | Rights upon change of control |
| `subcontracting` | boolean | Subcontracting allowed |
| `subcontracting_restrictions` | string | Any restrictions on subcontractors |

### 2.11 Special Clauses (High-Value Traps & Opportunities)

| Field | Data Type | Description |
|-------|-----------|-------------|
| `auto_renewal_trap` | object | Auto-renewal risk assessment |
| `auto_renewal_trap.present` | boolean | Auto-renewal clause exists |
| `auto_renewal_trap.opt_out_window` | string | Window to opt out |
| `auto_renewal_trap.next_opt_out_date` | date | Next opt-out deadline |
| `exclusivity` | boolean | Exclusivity provisions |
| `exclusivity_scope` | string | Scope of exclusivity |
| `non_compete` | object | Non-compete details |
| `non_compete.present` | boolean | Non-compete exists |
| `non_compete.duration` | string | Post-term duration |
| `non_compete.geographic_scope` | string | Geographic restrictions |
| `non_compete.activity_scope` | string | Activity restrictions |
| `no_solicit_customers` | boolean | Customer non-solicitation |
| `no_solicit_employees` | boolean | Employee non-solicitation |
| `non_disparagement` | boolean | Non-disparagement clause |
| `right_of_first_refusal` | boolean | ROFR present |
| `right_of_first_offer` | boolean | ROFO present |
| `matching_rights` | boolean | Matching rights present |
| `non_circumvention` | boolean | Non-circumvention clause |
| `covenant_not_to_sue` | boolean | Covenant not to sue |
| `third_party_beneficiary` | boolean | Third-party beneficiary rights |

---

## 3. Contract Type Classification

### Primary Contract Types (Level 1)

| Code | Type | Common Subtypes |
|------|------|-----------------|
| `MSA` | Master Service Agreement | IT Services, Professional Services, Consulting |
| `SOW` | Statement of Work | Project SOW, Consulting SOW |
| `SLA` | Service Level Agreement | IT SLA, Managed Services SLA |
| `NDA` | Non-Disclosure Agreement | Mutual NDA, One-Way NDA |
| `SPA` | Share/Stock Purchase Agreement | M&A |
| `APA` | Asset Purchase Agreement | M&A |
| `LICENSE` | License Agreement | Software, IP, Technology, Patent |
| `SAAS` | SaaS/Subscription Agreement | Cloud Services, Platform |
| `LEASE` | Lease Agreement | Commercial, Equipment, Real Estate |
| `EMP` | Employment Agreement | Executive, Standard, Contractor |
| `CONSULT` | Consulting Agreement | Independent Contractor |
| `VENDOR` | Vendor/Supplier Agreement | Supply, Purchase Order |
| `DIST` | Distribution Agreement | Exclusive, Non-Exclusive |
| `PARTNER` | Partnership/JV Agreement | Joint Venture, Strategic Alliance |
| `LOAN` | Loan/Credit Agreement | Revolving, Term Loan |
| `GUARANTEE` | Guarantee/Surety | Performance, Payment |
| `SETTLE` | Settlement Agreement | Litigation, Regulatory |
| `MERGER` | Merger Agreement | Merger, Consolidation |
| `AMEND` | Amendment/Addendum | Contract modification |
| `OTHER` | Other | Miscellaneous |

### Document Hierarchy

```
Master Agreement (MSA)
├── Amendment #1
├── Amendment #2
├── SOW #1
│   ├── Change Order #1
│   └── SLA (Exhibit A)
├── SOW #2
├── NDA (referenced)
└── DPA (Exhibit B)
```

---

## 4. Clause-Level Taxonomy (CUAD-Extended)

Building on CUAD's 41 categories, extended with enterprise CLM best practices:

### Category Groups

**Group A: Identification & Parties**
- Document name / title
- Parties (all entities)
- Party roles
- Signatories
- Agreement date
- Effective date

**Group B: Term & Renewal**
- Expiration date
- Term duration
- Renewal type (auto/manual/evergreen)
- Renewal term length
- Notice period for renewal opt-out
- Auto-renewal trap assessment

**Group C: Financial Terms**
- Total value / consideration
- Payment terms / schedule
- Pricing model
- Minimum commitments
- Volume restrictions / discounts
- Price escalation / adjustment
- Revenue / profit sharing
- Most favored nation
- Price benchmarking rights

**Group D: Intellectual Property**
- IP ownership assignment
- Joint IP ownership
- License grant (scope, exclusivity, territory)
- Transferability of license
- Perpetual / irrevocable license
- Affiliate license rights
- Source code escrow
- Unlimited / all-you-can-eat license

**Group E: Restrictive Covenants**
- Non-compete
- Non-solicitation (customers)
- Non-solicitation (employees)
- Non-disparagement
- Exclusivity
- Non-circumvention
- Right of first refusal / offer / negotiation

**Group F: Liability & Risk**
- Limitation of liability (cap)
- Uncapped liability
- Consequential damages waiver
- Indemnification (scope, cap, IP)
- Liquidated damages
- Insurance requirements
- Warranty provisions / duration
- Disclaimer of warranties
- Force majeure
- Covenant not to sue

**Group G: Termination**
- Termination for cause
- Cure period
- Termination for convenience
- Change of control termination
- Insolvency termination
- Post-termination obligations
- Post-termination services
- Survival clauses
- Data return / destruction

**Group H: Governance & Compliance**
- Governing law
- Dispute resolution mechanism
- Arbitration details
- Venue / forum selection
- Jury waiver
- Regulatory compliance requirements
- Anti-corruption / FCPA
- Sanctions / export controls
- Data protection (GDPR, CCPA)
- ESG provisions

**Group I: Operational**
- Assignment / anti-assignment
- Subcontracting rights
- Audit rights
- Reporting requirements
- Amendment procedure
- Entire agreement / integration clause
- Severability
- Waiver provisions
- Notices (addresses, methods)
- Third-party beneficiary

---

## 5. Risk Scoring Framework

### 5.1 Clause-Level Risk Rating

For each extracted clause, assign a risk score:

| Risk Level | Score | Color | Criteria |
|------------|-------|-------|----------|
| **Critical** | 5 | 🔴 Red | Missing or highly unfavorable clause; immediate legal/financial exposure |
| **High** | 4 | 🟠 Orange | Significantly deviates from standard; substantial risk |
| **Medium** | 3 | 🟡 Yellow | Moderately deviates from company playbook |
| **Low** | 2 | 🟢 Green | Minor deviations, acceptable with awareness |
| **Standard** | 1 | 🔵 Blue | Matches company standard / market standard |
| **N/A** | 0 | ⚪ Gray | Not applicable to this contract type |

### 5.2 Risk Categories & Weights

| Category | Weight | Critical Triggers |
|----------|--------|-------------------|
| **Liability Exposure** | 25% | Uncapped liability, no consequential damages waiver, one-sided indemnity |
| **Financial Risk** | 20% | No cap on damages, aggressive penalties, unfavorable MFN |
| **Termination Risk** | 15% | No termination for convenience, long cure periods, lock-in traps |
| **IP Risk** | 15% | IP assignment to counterparty, broad license grants, no escrow |
| **Compliance Risk** | 10% | Missing regulatory provisions, no data protection |
| **Operational Risk** | 10% | No audit rights, no SLA, no reporting |
| **Renewal/Lock-in Risk** | 5% | Auto-renewal with short opt-out, evergreen without termination |

### 5.3 Overall Contract Risk Score

```
Contract Risk Score = Σ (Category_Weight × Category_Risk_Score) / 5.0

Scale: 0.0 (no risk) → 1.0 (maximum risk)

Risk Bands:
  0.0 - 0.2  → LOW RISK      (Standard terms, minimal issues)
  0.2 - 0.4  → MODERATE RISK  (Some deviations, review recommended)
  0.4 - 0.6  → HIGH RISK      (Significant issues, legal review required)
  0.6 - 0.8  → VERY HIGH RISK (Multiple critical issues, executive attention)
  0.8 - 1.0  → CRITICAL RISK  (Do not execute without major revision)
```

### 5.4 Company Playbook Integration

The risk scoring should compare extracted terms against a configurable **company playbook** that defines:

1. **Preferred position** — ideal language for each clause
2. **Acceptable fallback** — acceptable alternatives
3. **Walk-away position** — terms that require escalation
4. **Industry baselines** — market-standard positions by contract type

This approach is used by enterprise CLM tools like:
- **Icertis RiskAI** — https://www.icertis.com/products/ai-applications/riskai/
- **LexCheck** — AI playbook-based scoring: https://blog.lexcheck.com
- **Sirion AI** — Contract risk framework: https://www.sirion.ai
- **LegalSifter ReviewPro** — Pattern-based risk detection

---

## 6. Best Practices for LLM-Based Contract Review

### 6.1 Prompt Engineering for Legal Extraction

**Best practices from Databricks, NetDocuments, and academic research:**

#### Strategy 1: Role + Schema + Examples (Structured Extraction)

```
You are an expert legal contract analyst specializing in {contract_type} review.

TASK: Extract the following fields from the contract text below.
For each field, provide:
- value: the extracted value
- confidence: high/medium/low
- source_text: exact quote from the contract
- page_reference: page number if available

FIELDS TO EXTRACT:
{json_schema}

RULES:
1. If a field is not present in the contract, set value to null
2. For dates, normalize to ISO 8601 format (YYYY-MM-DD)
3. For currency, include amount and currency code
4. For boolean clauses, also extract the relevant text passage
5. If ambiguous, note the ambiguity in a "notes" field

CONTRACT TEXT:
{document_text}

OUTPUT FORMAT: JSON
```

#### Strategy 2: Chain-of-Thought for Risk Analysis

```
Analyze this contract clause for risk exposure.

CLAUSE: "{clause_text}"
CLAUSE TYPE: {clause_type}
COMPANY POSITION: {playbook_position}

Think step by step:
1. What does this clause actually require/permit?
2. How does it compare to the company's preferred position?
3. What is the worst-case financial/legal exposure?
4. What specific language creates risk?
5. What modifications would reduce risk?

Provide your analysis as structured JSON with risk_score (1-5),
risk_explanation, suggested_revision, and negotiation_points.
```

#### Strategy 3: Multi-Pass Extraction (Recommended for Production)

1. **Pass 1 — Classification:** Identify contract type and structure
2. **Pass 2 — Entity extraction:** Parties, dates, values (high-precision fields)
3. **Pass 3 — Clause identification:** Tag each section with clause categories
4. **Pass 4 — Risk analysis:** Score each clause against playbook
5. **Pass 5 — Cross-reference:** Validate internal consistency

**Key References:**
- Databricks: End-to-End Structured Extraction with LLM — https://community.databricks.com/t5/technical-blog/end-to-end-structured-extraction-with-llm-part-1-batch-entity/ba-p/98396
- NetDocuments: Structuring LLM Outputs for Legal — https://studio.netdocuments.com/post/structuring-llm-outputs
- arXiv: Metadata Extraction with LLMs — https://arxiv.org/html/2510.19334v1
- Springer: Legal Knowledge via Prompt Engineering — https://link.springer.com/chapter/10.1007/978-3-032-06326-7_2

### 6.2 Chunking Strategy for Long Contracts

| Approach | Best For | Notes |
|----------|----------|-------|
| **Section-based chunking** | Well-structured contracts | Split on headings/section numbers |
| **Sliding window** | Poorly formatted OCR output | Overlap of 10-20% between chunks |
| **Semantic chunking** | Mixed document quality | Use embedding similarity to find natural breaks |
| **Full document** | Short contracts (<50 pages) | Use models with 128K+ context |
| **Hybrid** | Production systems | Section-based first, sliding window as fallback |

### 6.3 Output Structure for Legal Teams

Enterprise legal teams expect output in these formats:

1. **Executive Summary** — 1-page risk overview with traffic-light scores
2. **Key Terms Sheet** — Tabular extraction of all critical fields
3. **Clause-by-Clause Analysis** — Detailed review with risk flags
4. **Deviation Report** — Comparison to company playbook
5. **Action Items** — Required follow-ups with assignees and deadlines
6. **Machine-Readable JSON** — For CLM system integration

---

## 7. Reference Implementations & Open-Source Tools

### 7.1 Open Source Contract Analysis Platforms

#### OpenContracts (⭐ Top Pick)
- **GitHub:** https://github.com/Open-Source-Legal/OpenContracts (also https://github.com/JSv4/OpenContracts)
- **Description:** Enterprise-grade, API-first LLM workspace for unstructured documents
- **Features:**
  - Data extraction with custom schemas
  - Document annotation and labeling
  - Redaction capabilities
  - Rights management
  - LLM prompt playground
  - Docling integration for PDF parsing
  - Docker-based deployment
- **Stack:** Django, React, Celery, PostgreSQL, Docker
- **Why it matters:** Closest to a production-ready open-source contract analysis platform

#### Unstract
- **GitHub:** https://github.com/Zipstack/unstract
- **Website:** https://unstract.com
- **Description:** No-code LLM platform for unstructured document extraction
- **Features:**
  - API deployment for document extraction
  - ETL pipeline (folder → process → warehouse)
  - MCP Server for AI agent integration
  - n8n workflow integration
  - Docker Compose deployment
  - Supports Ollama for local LLM
- **Best for:** Building automated contract processing pipelines

#### LLMWare
- **GitHub:** https://github.com/llmware-ai/llmware
- **Description:** Unified framework for enterprise RAG pipelines with small specialized models
- **Key models:**
  - **BLING models** (~1B params) — CPU-based contract analysis
  - **SLIM models** (1-3B params) — Structured output extraction (dicts, JSON, SQL)
  - **DRAGON models** (7B) — RAG-optimized
- **Contract analysis example:** `examples/Use_Cases/contract_analysis_on_laptop_with_bling_models.py`
- **Why it matters:** Can run contract analysis on a laptop without GPU, suitable for sensitive/airgapped deployments

#### Azure Ally Legal Assistant
- **GitHub:** https://github.com/Azure-Samples/ally-legal-assistant
- **Description:** Word plugin using Azure OpenAI for contract analysis
- **Features:** Real-time Q&A, auto-markup, contract review within Microsoft Word
- **Best for:** Teams already in the Microsoft ecosystem

#### Contract Analyzer (ahmetkumass)
- **GitHub:** https://github.com/ahmetkumass/contract-analyzer
- **Description:** Open-source tool for extracting key information from legal contracts
- **Best for:** Lightweight/quick-start extraction

### 7.2 Document Processing / OCR Platforms

#### Docling (IBM) — ⭐ Top Pick for OCR
- **GitHub:** https://github.com/docling-project/docling
- **Stars:** 20k+ (as of early 2026)
- **Features:**
  - PDF, DOCX, PPTX, images → Markdown / JSON
  - Extensive OCR support (scanned PDFs, images)
  - Visual Language Model support (GraniteDocling)
  - Table extraction
  - Layout analysis with AI models
  - FastAPI server mode (docling-serve)
- **Integration:** Used by OpenContracts, LangChain, LlamaIndex
- **Best for:** The OCR/parsing layer of any contract pipeline

#### Paperless-GPT
- **GitHub:** https://github.com/icereed/paperless-gpt
- **Description:** LLM-powered OCR for paperless-ngx document management
- **OCR providers:** Google DocAI, Docling, Azure, Tesseract
- **Best for:** Document digitization pipeline

#### LLM Document OCR (Mercoa)
- **GitHub:** https://github.com/mercoa-finance/llm-document-ocr
- **Description:** LLM-based OCR and document parsing for Node.js
- **Docker support:** Yes, Alpine base image
- **Best for:** Node.js-based pipelines

#### Other OCR Options
| Tool | Type | Best For |
|------|------|----------|
| **ocrmypdf** | CLI tool | Adding OCR layer to existing PDFs (Tesseract-based) |
| **Azure Document Intelligence** | Cloud API | Highest accuracy on complex layouts |
| **Unstructured.io** | Python library | Document parsing with multiple strategies |
| **Marker** | Python library | PDF → Markdown conversion |
| **Surya** | Python library | OCR + layout analysis |
| **olmOCR** | VLM-based | Vision model-based OCR |

### 7.3 Relevant Academic Implementations

| Project | Paper/Source | Focus |
|---------|-------------|-------|
| **CUAD Models** | https://github.com/TheAtticusProject/cuad | Baseline models for 41 clause types |
| **LexGLUE** | https://github.com/coastalcph/lex-glue | Legal NLU benchmark with multiple tasks |
| **Legal-BERT** | HuggingFace | BERT pre-trained on legal text |
| **ContractNLI** | Stanford NLP | Natural language inference for contracts |

---

## 8. OCR + LLM Pipeline Architecture

### 8.1 Recommended Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                       │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────────┐ │
│  │ File Drop │  │ Email/API │  │ CLM System Webhook   │ │
│  └─────┬─────┘  └─────┬─────┘  └──────────┬───────────┘ │
│        └──────────────┼──────────────────────┘           │
│                       ▼                                  │
│              ┌─────────────────┐                         │
│              │  Queue (Redis/  │                         │
│              │  RabbitMQ/SQS)  │                         │
│              └────────┬────────┘                         │
└───────────────────────┼─────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  PROCESSING LAYER                        │
│                                                          │
│  Step 1: DOCUMENT PREPROCESSING                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ • PDF quality assessment (native text vs scanned) │   │
│  │ • Page-level image extraction                     │   │
│  │ • Orientation correction / deskew                 │   │
│  │ • Resolution normalization                        │   │
│  └──────────────────────────┬───────────────────────┘   │
│                              ▼                           │
│  Step 2: OCR + PARSING (Docling / Azure DocAI)          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ • Text extraction with position info             │   │
│  │ • Table detection and extraction                 │   │
│  │ • Layout analysis (headers, sections, exhibits)  │   │
│  │ • OCR confidence scoring per page                │   │
│  │ • Output: Structured Markdown + JSON             │   │
│  └──────────────────────────┬───────────────────────┘   │
│                              ▼                           │
│  Step 3: DOCUMENT CLASSIFICATION (LLM Pass 1)           │
│  ┌──────────────────────────────────────────────────┐   │
│  │ • Contract type identification (MSA/NDA/SOW/etc) │   │
│  │ • Language detection                             │   │
│  │ • Document structure mapping (sections/exhibits) │   │
│  │ • Quality flag (OCR artifacts, missing pages)    │   │
│  └──────────────────────────┬───────────────────────┘   │
│                              ▼                           │
│  Step 4: FIELD EXTRACTION (LLM Pass 2)                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │ • Party extraction with role classification      │   │
│  │ • Date extraction and normalization              │   │
│  │ • Financial terms extraction                     │   │
│  │ • Section-by-section clause tagging              │   │
│  │ • Schema: See §2 Comprehensive Extraction Schema │   │
│  │ • Output: Structured JSON per schema             │   │
│  └──────────────────────────┬───────────────────────┘   │
│                              ▼                           │
│  Step 5: RISK ANALYSIS (LLM Pass 3)                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │ • Compare each clause to company playbook        │   │
│  │ • Score risk per category (§5 Framework)         │   │
│  │ • Identify missing critical clauses              │   │
│  │ • Flag auto-renewal traps and lock-ins           │   │
│  │ • Generate deviation report                      │   │
│  │ • Calculate overall contract risk score          │   │
│  └──────────────────────────┬───────────────────────┘   │
│                              ▼                           │
│  Step 6: VALIDATION & QA                                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │ • Cross-reference extracted dates for consistency│   │
│  │ • Verify party names match across sections       │   │
│  │ • Check financial terms add up                   │   │
│  │ • Flag low-confidence extractions for human QA   │   │
│  │ • Confidence threshold: auto-approve >0.9,       │   │
│  │   human review 0.7-0.9, reject <0.7             │   │
│  └──────────────────────────┬───────────────────────┘   │
└──────────────────────────────┼──────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────┐
│                    OUTPUT LAYER                           │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────┐  │
│  │ Structured   │ │ Risk Report  │ │ CLM Integration │  │
│  │ JSON/DB      │ │ (PDF/HTML)   │ │ (API push)      │  │
│  └─────────────┘ └──────────────┘ └─────────────────┘  │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────┐  │
│  │ Dashboard    │ │ Alert System │ │ Human Review    │  │
│  │ (Analytics)  │ │ (Deadlines)  │ │ Queue           │  │
│  └─────────────┘ └──────────────┘ └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 8.2 Technology Stack Recommendations

| Component | Recommended | Alternative |
|-----------|-------------|-------------|
| **OCR/Parsing** | Docling (IBM) | Azure Document Intelligence, Unstructured.io |
| **LLM (Cloud)** | Claude Opus 4.6 / GPT-4o | Claude Sonnet for high-volume |
| **LLM (Local)** | Qwen2.5-VL-72B, DeepSeek-R1 | LLMWare BLING/SLIM for CPU |
| **Queue** | Redis + Celery | RabbitMQ, AWS SQS |
| **Database** | PostgreSQL + pgvector | Elasticsearch for search |
| **Vector Store** | pgvector / Chroma | Pinecone, Weaviate |
| **API** | FastAPI (Python) | Express.js (Node) |
| **Frontend** | React + AG Grid | Next.js |
| **Deployment** | Docker Compose → K8s | AWS ECS, GCP Cloud Run |
| **File Storage** | S3-compatible (MinIO) | GCS, Azure Blob |

### 8.3 Docker Compose Skeleton

```yaml
version: '3.8'
services:
  # OCR / Document Parsing
  docling:
    image: docling-project/docling-serve:latest
    ports: ["8001:8001"]

  # LLM Inference (local option)
  ollama:
    image: ollama/ollama:latest
    volumes: ["ollama_data:/root/.ollama"]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  # API Server
  api:
    build: ./api
    environment:
      - DATABASE_URL=postgresql://...
      - DOCLING_URL=http://docling:8001
      - LLM_PROVIDER=anthropic  # or ollama
    depends_on: [db, redis, docling]

  # Worker (Celery)
  worker:
    build: ./api
    command: celery -A app worker -Q contracts
    depends_on: [db, redis, docling]

  # Database
  db:
    image: pgvector/pgvector:pg16
    volumes: ["pg_data:/var/lib/postgresql/data"]

  # Queue
  redis:
    image: redis:7-alpine

  # Frontend
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
```

---

## 9. Recommended Production Taxonomy

Based on all research, here is the **recommended unified taxonomy** for a production system:

### Tier 1: Always Extract (Every Contract)

These fields should be extracted for 100% of contracts:

```json
{
  "document": {
    "id": "auto-generated UUID",
    "name": "string",
    "type": "enum (see §3)",
    "subtype": "string",
    "page_count": "integer",
    "ocr_confidence": "float",
    "language": "string",
    "file_hash": "string"
  },
  "parties": [{
    "name": "string",
    "role": "enum",
    "entity_type": "enum",
    "jurisdiction": "string",
    "address": "string",
    "signatories": [{"name": "string", "title": "string", "date": "date"}]
  }],
  "dates": {
    "agreement_date": "date",
    "effective_date": "date",
    "expiration_date": "date",
    "term_duration": "string"
  },
  "renewal": {
    "type": "enum",
    "term": "string",
    "notice_period": "string",
    "next_opt_out_date": "date"
  },
  "financial": {
    "total_value": "currency",
    "currency": "string",
    "payment_terms": "string"
  },
  "governance": {
    "governing_law": "string",
    "dispute_resolution": "enum",
    "venue": "string"
  },
  "termination": {
    "for_cause": "boolean",
    "cure_period": "string",
    "for_convenience": "boolean",
    "notice_period": "string"
  },
  "risk_score": {
    "overall": "float (0-1)",
    "liability": "float",
    "financial": "float",
    "ip": "float",
    "compliance": "float",
    "termination": "float",
    "flags": ["string"]
  }
}
```

### Tier 2: Extract by Contract Type

Additional fields extracted based on the contract type:

| Contract Type | Additional Fields |
|--------------|-------------------|
| **MSA/SOW** | SLA metrics, deliverables, acceptance criteria, subcontracting |
| **License** | IP ownership, license scope/territory/exclusivity, source code escrow |
| **NDA** | Confidentiality term, scope, exceptions, return/destruction |
| **Employment** | Non-compete, non-solicit, compensation, benefits, IP assignment |
| **Lease** | Rent escalation, maintenance obligations, improvements, subletting |
| **M&A (SPA/APA)** | Representations & warranties, indemnification baskets/caps, earn-outs |
| **SaaS** | Data protection, uptime SLA, data portability, vendor lock-in |
| **Loan** | Interest rate, covenants, default triggers, collateral |

### Tier 3: Deep Analysis (On Demand)

Full clause-by-clause analysis with:
- CUAD 41-category clause tagging
- Playbook deviation scoring
- Suggested redline markup
- Negotiation recommendations
- Historical comparison to similar contracts

---

## 10. Model Recommendations

### For Production Contract Analysis (2026)

| Use Case | Model | Context | Cost | Notes |
|----------|-------|---------|------|-------|
| **Classification + Quick Extract** | Claude 4.5 Sonnet | 200K | $$ | Fast, accurate, good for Tier 1 |
| **Deep Analysis + Risk** | Claude Opus 4.6 | 200K | $$$$ | Best reasoning for complex clauses |
| **High Volume Batch** | GPT-4o-mini / Sonnet | 128K/200K | $ | Cost-effective for large backlogs |
| **Vision/OCR+Extract** | Qwen2.5-VL-72B | 131K | Self-hosted | Best open-source VLM for contracts |
| **Local/Airgapped** | LLMWare BLING/SLIM | 4-8K | Free | CPU-only, good for sensitive data |
| **Local Advanced** | DeepSeek-R1 | 128K | Self-hosted | Strong reasoning, open weights |
| **OCR Layer** | Docling + Tesseract | N/A | Free | Best open-source OCR pipeline |

### Key Insights from SiliconFlow 2026 Review

1. **Qwen2.5-VL-72B-Instruct** — Top-ranked for contract processing; handles images, tables, and layouts
2. **GLM-4.5V** — MoE architecture with 12B active params; cost-efficient with "Thinking Mode" for deep reasoning
3. **DeepSeek-R1** — 671B total / 37B active; strong chain-of-thought reasoning for legal analysis

---

## Appendix A: Key URLs & Resources

### Datasets
| Resource | URL |
|----------|-----|
| CUAD Dataset | https://www.atticusprojectai.org/cuad |
| CUAD GitHub | https://github.com/TheAtticusProject/cuad |
| CUAD HuggingFace | https://huggingface.co/datasets/theatticusproject/cuad |
| CUAD Paper | https://arxiv.org/abs/2103.06268 |
| LEDGAR Paper | https://aclanthology.org/2020.lrec-1.155/ |
| LexGLUE Benchmark | https://github.com/coastalcph/lex-glue |
| ContractNLI | https://stanfordnlp.github.io/contract-nli/ |
| SALI LMSS | https://github.com/sali-legal/LMSS |

### Open-Source Tools
| Tool | URL |
|------|-----|
| OpenContracts | https://github.com/Open-Source-Legal/OpenContracts |
| Unstract | https://github.com/Zipstack/unstract |
| LLMWare | https://github.com/llmware-ai/llmware |
| Docling (IBM) | https://github.com/docling-project/docling |
| Paperless-GPT | https://github.com/icereed/paperless-gpt |
| Ally Legal Assistant | https://github.com/Azure-Samples/ally-legal-assistant |
| Contract Analyzer | https://github.com/ahmetkumass/contract-analyzer |

### Industry Standards & Reports
| Resource | URL |
|----------|-----|
| SALI Alliance | https://www.sali.org |
| WorldCC Most Negotiated Terms | https://www.worldcc.com |
| Zuva Document Taxonomy | https://zuva.ai/blog/zuva-releases-enhanced-document-classifier/ |

### Enterprise CLM References
| Vendor | Notable For |
|--------|-------------|
| **Icertis** | RiskAI — playbook-based contract scoring |
| **Sirion** | AI-native CLM, hundreds of metadata fields |
| **Ironclad** | Contract data extraction and lifecycle |
| **Agiloft** | No-code CLM with SALI standards support |
| **LexCheck** | AI contract risk scoring with color-coded analysis |
| **SpotDraft** | Contract metadata abstraction |
| **LegalSifter** | ReviewPro — 10 years of legal AI algorithms |
| **Brightleaf** | AI extraction + expert legal review validation |

### Academic & Research
| Resource | URL |
|----------|-----|
| Legal Contract NLP Survey (2025) | https://link.springer.com/article/10.1007/s10462-025-11359-8 |
| LLM Metadata Extraction Paper | https://arxiv.org/html/2510.19334v1 |
| Enhancing Contract Negotiations with LLM | https://aclanthology.org/2024.nllp-1.11.pdf |
| Legal Prompt Engineering (Springer) | https://link.springer.com/chapter/10.1007/978-3-032-06326-7_2 |

---

## Appendix B: Quick-Start Extraction Prompt Template

```python
SYSTEM_PROMPT = """You are an expert legal contract analyst. Extract structured 
metadata from the provided contract text following the exact schema below.

For each field:
- Extract the value as specified
- Rate confidence as "high", "medium", or "low"
- Include the exact source text (verbatim quote, max 200 chars)
- If not found, set value to null with confidence "high" (confirmed absent)

Be precise. Do not infer values not stated in the text. 
Flag any ambiguities in the "notes" field."""

EXTRACTION_SCHEMA = {
    "contract_type": "Classify: MSA|NDA|SOW|SLA|LICENSE|SAAS|LEASE|EMP|...",
    "parties": [{"name": "str", "role": "str", "entity_type": "str"}],
    "effective_date": "ISO 8601 date",
    "expiration_date": "ISO 8601 date",
    "total_value": {"amount": "number", "currency": "ISO 4217"},
    "governing_law": "jurisdiction string",
    "auto_renewal": "boolean",
    "renewal_notice_period": "duration string",
    "termination_for_convenience": "boolean",
    "liability_cap": "description of cap",
    "indemnification_type": "mutual|one_sided|none",
    "confidentiality_term": "duration string",
    "ip_ownership": "description",
    "dispute_resolution": "litigation|arbitration|mediation",
    "risk_flags": ["list of concerning provisions"]
}
```

---

*This research document is a living reference. Update as new standards, tools, and models emerge.*
