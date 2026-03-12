# LlamaParse + LlamaIndex Integration Plan
## Contract Analyzer Enhancement

**Prepared for:** Eric Brown, CFO & COO, Cohesity
**Date:** March 7, 2026

---

## Executive Summary

**LlamaParse** is a cloud-based PDF parser by LlamaIndex that outperforms pdfplumber + Tesseract on complex documents (contracts, tables, scanned images). **LlamaIndex** is a RAG (Retrieval-Augmented Generation) framework that would add a conversational query layer on top of your contract data — letting you ask questions like "Which contracts have uncapped liability?" across all 12 Morgan Stanley contracts.

**Bottom line:** LlamaParse would improve extraction quality (especially for the scanned 1998 MSLA). LlamaIndex would add a powerful interactive query layer. Combined cost increase: ~$15–30/month over current setup. **Recommended as a Phase 2 enhancement.**

---

## 1. Current vs Proposed Architecture

### Current Pipeline
```
PDF → pdfplumber (embedded text)
  ↓ fallback
PDF → Tesseract OCR (scanned images)
  ↓ fallback
PDF → Claude Vision (degraded scans)
  ↓
Full text → Claude API (claude-sonnet-4-6) → JSON analysis
  ↓
12 JSON files → report_generator.py → Word report
```

**Strengths:** Free OCR (Tesseract), works offline, full control.
**Weaknesses:** Tesseract struggles with complex layouts (tables, headers), OCR artifacts on scanned docs, no interactive query capability.

### Proposed Pipeline (with LlamaParse + LlamaIndex)
```
PDF → LlamaParse API (cloud OCR + layout understanding)
  ↓
Structured Markdown (tables preserved, headers tagged, clean text)
  ↓
Claude API (claude-sonnet-4-6) → JSON analysis → Word report
  ↓
LlamaIndex ingestion (chunk + embed all contract text + JSON analyses)
  ↓
Vector index (local or cloud) → Interactive query interface
  ↓
Web UI: "What are the termination provisions for Schedule 15?"
```

---

## 2. LlamaParse — PDF Parsing Upgrade

### What It Does
- Cloud-based document parser optimized for LLM consumption
- Handles scanned PDFs, complex tables, multi-column layouts, headers/footers
- Outputs clean Markdown or JSON with structure preserved
- Built-in OCR for image-only PDFs (like the 1998 MSLA)
- Understands document hierarchy (section headings, clause numbering)

### Why It's Better Than Current Stack
| Feature | pdfplumber + Tesseract | LlamaParse |
|---------|----------------------|------------|
| Embedded text PDFs | ✅ Good | ✅ Excellent |
| Scanned image PDFs | ⚠️ OK (artifacts) | ✅ Excellent (AI-powered OCR) |
| Table extraction | ⚠️ Basic | ✅ Preserves structure |
| Section hierarchy | ❌ None | ✅ Headers tagged |
| Contract-specific | ❌ Generic | ✅ Optimized for documents |
| Setup complexity | Medium (Tesseract install) | Low (API call) |
| Cost | Free | Credits-based |

### Pricing
| Plan | Included Credits | Price | Pages (basic mode) |
|------|-----------------|-------|--------------------|
| **Free** | 10,000 | $0 | ~10,000 pages |
| **Starter** | 40,000 | ~$50/month | ~40,000 pages |
| **Pro** | 400,000 | ~$500/month | ~400,000 pages |

**Your usage:** 12 contracts × ~20 pages avg = ~240 pages per run. At 1 credit/page (basic mode), that's 240 credits per full analysis. The **Free tier (10K credits)** would last you ~40 full runs — more than enough.

**Advanced mode** (with AI agent parsing for complex docs like the 1998 MSLA): ~90 credits/page. The scanned 12-page MSLA would cost ~1,080 credits. Still well within free tier.

### Integration Code (Python)
```python
from llama_parse import LlamaParse

parser = LlamaParse(
    api_key="llx-...",
    result_type="markdown",  # or "text" or "json"
    parsing_instruction="Extract all contract terms, dates, financial values, and party names. Preserve table structure."
)

# Replace current extract_pdf_text() function
documents = parser.load_data("08_MS_MSLA_1998.pdf")
contract_text = documents[0].text
# Feed to Claude for analysis (same as current pipeline)
```

### Migration: 3 Lines of Code Changed
The existing `extract_pdf_text()` function in `process_local.py` would become:
1. Try LlamaParse API first (best quality)
2. Fall back to pdfplumber (if API unavailable/offline)
3. Fall back to Tesseract (if no embedded text)

---

## 3. LlamaIndex — Interactive Query Layer

### What It Does
LlamaIndex is a RAG framework that:
1. **Ingests** your documents (PDFs, JSON analyses, Word reports)
2. **Chunks** them into searchable segments
3. **Embeds** them into vectors (using OpenAI or local embeddings)
4. **Indexes** them for fast retrieval
5. **Queries** them using an LLM (Claude) with relevant context

### How It Would Work for Contract Analyzer

#### Use Case 1: Natural Language Contract Q&A
```
User: "What is the liability cap for Schedule 15?"
LlamaIndex: Retrieves relevant chunks from Schedule 15 analysis
Claude: "Schedule 15 has no explicit liability cap in the Schedule itself. 
The 1998 MSLA (parent agreement) likely contains the governing liability 
provisions, but this document has OCR quality issues. The Software License 
& Consulting Agreement (#4) has a $50M aggregate cap that may apply."
```

#### Use Case 2: Cross-Contract Analysis
```
User: "Which contracts allow termination for convenience?"
LlamaIndex: Searches all 12 contract analyses
Claude: "Only 3 of 12 contracts include termination for convenience:
1. Limited Use Agreement (#2) — Yes, with 90-day notice
2. Master HW/SW Eval (#1) — Yes, either party
3. Software License & Consulting (#4) — Yes, with 30-day notice
The remaining 9 contracts do NOT include termination for convenience."
```

#### Use Case 3: Deal Preparation
```
User: "What pricing precedents exist for the next Morgan Stanley renewal?"
LlamaIndex: Pulls from New Deal Considerations, Financial Terms across all contracts
Claude: "Current pricing precedents include: 2% cap (LUA), 3% cap (Schedule 7/Site License),
5% cap (SW License during cap period), 7% cap (Subscription Addendum). The most recent 
active agreement (Schedule 15) was priced at $27.75M/48 months (~$6.94M/year)..."
```

### Integration Architecture
```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.anthropic import Anthropic

# Configure Claude as the LLM
Settings.llm = Anthropic(model="claude-sonnet-4-6", api_key="sk-ant-...")

# Ingest all contract analyses
documents = SimpleDirectoryReader("/Users/ericbrown/ContractAnalyzer/output/").load_data()

# Build searchable index
index = VectorStoreIndex.from_documents(documents)

# Query
query_engine = index.as_query_engine()
response = query_engine.query("What are the change-of-control provisions across all contracts?")
print(response)
```

### Web UI Options

**Option A: Streamlit (simplest — 1 day to build)**
```python
import streamlit as st
from llama_index.core import VectorStoreIndex

st.title("Morgan Stanley Contract Analyzer")
query = st.text_input("Ask a question about the contracts:")
if query:
    response = query_engine.query(query)
    st.write(response)
```

**Option B: LlamaIndex's create-llama CLI (built-in web app)**
```bash
npx create-llama@latest --framework fastapi --ui shadcn
# Generates a full React + FastAPI app with chat UI
```

**Option C: Custom Flask/FastAPI + React (most control — 1 week)**
- Full dashboard with contract list, risk scores, query interface
- Could integrate with the Railway deployment plan

---

## 4. Cost Comparison

### Current Monthly Cost
| Component | Cost |
|-----------|------|
| Claude API (12 contracts × ~$0.30) | ~$3.60/run |
| Tesseract OCR | Free |
| pdfplumber | Free |
| **Total per run** | **~$3.60** |

### Proposed Monthly Cost (LlamaParse + LlamaIndex)
| Component | Cost |
|-----------|------|
| LlamaParse (free tier, 10K credits) | $0 |
| Claude API (analysis, same as before) | ~$3.60/run |
| Embeddings (OpenAI text-embedding-3-small) | ~$0.02/run |
| Claude API (queries, ~$0.01/query) | ~$0.50/month (est. 50 queries) |
| **Total per run + monthly queries** | **~$4.12 + $0.50/month** |

**Net increase: ~$0.50–1.00/month** — negligible for the added query capability.

If you upgrade to LlamaParse Starter for higher quality: **+$50/month** (but the free tier is likely sufficient for 12 contracts).

---

## 5. Implementation Steps

### Phase 1: LlamaParse Integration (2–3 hours)
1. Sign up at https://cloud.llamaindex.ai/ (free account)
2. Get API key
3. `pip install llama-parse`
4. Update `extract_pdf_text()` in process_local.py to try LlamaParse first
5. Re-run on the 1998 MSLA to compare quality vs Tesseract
6. If quality is better, re-run all 12 contracts

### Phase 2: LlamaIndex Query Layer (4–6 hours)
1. `pip install llama-index llama-index-llms-anthropic llama-index-embeddings-openai`
2. Create `scripts/query_engine.py` — ingests all JSON analyses + original text
3. Build vector index over all 12 contracts
4. Test queries: "What is the total financial exposure?", "Which contracts expire in 2027?"
5. Add Streamlit web UI for interactive querying

### Phase 3: Web Deployment (combined with Railway plan) (1 week)
1. Dockerize the full stack (Contract Analyzer + LlamaIndex query engine)
2. Deploy to Railway
3. Add authentication
4. Custom domain

---

## 6. Pros & Cons

### Pros
- **Better OCR quality** on scanned PDFs (the 1998 MSLA would parse cleaner)
- **Table preservation** — LlamaParse understands table structure natively
- **Interactive queries** — ask questions across all contracts instead of reading the report
- **Cross-contract intelligence** — find patterns, conflicts, and risks across the portfolio
- **Deal preparation** — instant answers for renewal negotiations
- **Minimal code changes** — LlamaParse is a drop-in replacement for extract_pdf_text()
- **Free tier sufficient** — 10K credits covers extensive use

### Cons
- **Cloud dependency** — LlamaParse requires internet (vs Tesseract which runs locally)
- **API key management** — another service to manage credentials for
- **Embedding cost** — small but ongoing (OpenAI embeddings for LlamaIndex)
- **Index maintenance** — need to re-index when contracts change
- **Latency** — LlamaParse API adds ~10-30 seconds per document vs instant local Tesseract

---

## 7. Recommendation

**Do it in two phases:**

1. **Phase 1 (This week, 2-3 hours):** Add LlamaParse as the primary PDF parser, falling back to pdfplumber/Tesseract. Free tier. Immediate quality improvement on scanned docs. Minimal risk.

2. **Phase 2 (Next week, 4-6 hours):** Add LlamaIndex query engine with Streamlit UI. This transforms Contract Analyzer from a batch-processing tool into an interactive contract intelligence platform. The ROI is clearest when preparing for renewal negotiations — instead of reading a 50-page report, you ask "What pricing precedents exist for the next Schedule 15 renewal?" and get an instant, sourced answer.

**Combined with the Railway deployment plan**, you'd have a web-accessible contract analysis platform with:
- Upload new PDFs → auto-analyze
- Interactive Q&A across all contracts
- Downloadable reports
- Accessible from anywhere (not just Eric's MacBook)

---

*Prepared by Jarvis AI for Eric Brown*
