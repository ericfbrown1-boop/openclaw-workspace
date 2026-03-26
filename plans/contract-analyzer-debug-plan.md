# ContractAnalyzer Debug & Fix Plan

## Problem
The report downloads with all N/A fields. The March 11 successful run produced rich analysis (parties with roles, entity attribution, financial terms, risk flags with severity, executive summaries). The current Railway deployment produces flat tier1/tier2 fields that the report generator can't map to the expected schema.

## Root Cause: Schema Mismatch Between Extraction and Report Generator

The system has TWO different extraction schemas that are out of sync:

### Schema A: What `report_service.py` (2776 lines) Expects
The report generator was written to consume the **rich schema** from March 11:
```python
{
  "filename": "...",
  "document_name": "...",
  "parties": [{"name": "...", "role": "licensor", "entity_type": "...", "cohesity_note": "..."}],
  "contract_type": "LICENSE",
  "contract_subtype": "Unlimited Site License Addendum...",
  "key_dates": {"agreement_date": "2016-06-30", "effective_date": "...", ...},
  "financial_terms": {"total_value": {"amount": 1470000, "currency": "SGD"}, ...},
  "termination_provisions": {"for_cause": true, "for_convenience": false, ...},
  "risk_flags": [{"flag": "no_termination_convenience", "severity": "high", "details": "..."}],
  "risk_score": 0.72,
  "entity_attribution": {"mapping_applied": true, "original_party": "...", ...},
  "executive_summary": "This Unlimited Site License...",
  "ocr_metadata": {"method": "pdfplumber+tesseract", "ocr_pages": [...], ...},
  "tier1_extraction": {27 fields with {value, confidence, source_text}},
  "tier2": {"LICENSE": {...}},
  "recommendations": [{"priority": "...", "title": "...", "details": "..."}]
}
```

### Schema B: What `extraction.py` + `contract_tasks.py` Currently Produce
The current extraction pipeline produces a **flat schema**:
```python
# tier1_fields: stored in ExtractionResult table
{"contract_type": {"value": "...", "confidence": 0.98, "source_text": "..."}, ...}

# tier2_fields: stored in ExtractionResult table
{"software_products": {"value": [...], "confidence": null, "source_text": null}, ...}

# risk_score: stored in RiskScore table
{"overall_score": 0.575, "liability_score": 0.8, "flags": [...], "details": {...}}
```

### What `build_report_data()` Does
It reads from the database (Contract + ExtractionResult + RiskScore tables) and tries to assemble the report data. But the ExtractionResult rows are flat key-value pairs, NOT the rich structured format the report generator expects.

**The report generator looks for `result["parties"]` but gets `result["tier1_fields"]["parties"]["value"]`.**
**It looks for `result["key_dates"]` but that key doesn't exist — dates are flat in tier1_fields.**
**It looks for `result["entity_attribution"]` but that was never part of the extraction pipeline.**

## Step-by-Step Fix Plan

### Step 1: Read `build_report_data()` in report_service.py
Understand exactly how it transforms DB rows into the report data dict. Identify every field it tries to access.

### Step 2: Read `generate_report()` in report_service.py
Understand the full DOCX generation — what fields it reads from the data dict to populate tables, sections, and text.

### Step 3: Create a data transformation layer
Add a function `transform_db_to_report_schema()` in report_service.py that:
- Takes the flat ExtractionResult rows + RiskScore from the database
- Transforms them into the rich schema (Schema A) that the report generator expects
- Maps:
  - `tier1_fields.contract_type.value` → `contract_type`
  - `tier1_fields.parties.value` → `parties` (with role/entity structure)
  - `tier1_fields.agreement_date.value` + effective + expiration → `key_dates`
  - `tier1_fields.contract_value.value` + payment_terms → `financial_terms`
  - `tier1_fields.termination_*` → `termination_provisions`
  - RiskScore.flags → `risk_flags` with severity and details
  - RiskScore.overall_score → `risk_score`
  - Build `entity_attribution` from parties (check for Veritas/Symantec/Cohesity)
  - Generate `executive_summary` from extracted fields (or add LLM call)
  - Include `ocr_metadata` from Contract model

### Step 4: Update `build_report_data()` to use the transformer
Instead of returning raw DB rows, call `transform_db_to_report_schema()` on each contract's data before returning.

### Step 5: Test locally with one contract
Run `scripts/regenerate_report.py` or hit the API endpoint to generate a report for one contract. Verify the DOCX has populated fields.

### Step 6: Push to Railway and verify
Git push → Railway auto-deploys → test report download.

## Files to Modify
1. `api/app/services/report_service.py` — Add `transform_db_to_report_schema()`, update `build_report_data()`
2. Possibly `api/app/routers/projects.py` — If the report endpoint needs updating

## Files to Reference (DO NOT modify)
- `Dropbox/Contract Analyzer/UOB/01*_analysis.json` — Gold standard output format
- `api/app/services/extraction.py` — Current extraction prompts/schema
- `api/app/tasks/contract_tasks.py` — Current pipeline
- `api/app/tasks/report_tasks.py` — Report generation task

## Verification
- Download DOCX report from Railway
- Verify all contract fields are populated (not N/A)
- Verify parties have names, roles
- Verify dates are present
- Verify financial terms show amounts
- Verify risk flags show severity and details
- Compare structure to March 11 successful report

## This Should Be Executed on PowerSpec
The ContractAnalyzer repo is at `C:/Users/ericf/ContractAnalyzer/`. Changes push to GitHub → Railway auto-deploys.
