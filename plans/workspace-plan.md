# PLAN.md — Contract PDF Ingestion & Automated Analysis System (v2)

> **Type:** Architecture Plan (no code)  
> **Created:** 2026-03-06 (revised)  
> **Status:** Ready for implementation  
> **Target Hardware:** PowerSpec PC (EFBPowerSpec) — Docker/Ubuntu/WSL2  
> **Revision Note:** Updated from v1 to account for Docker-based IDE, RTX 5080 16GB VRAM constraint, and PyTorch nightly (cu128) requirement.

---

## 0. Development Environment Summary

All development and runtime happens inside Docker containers on the PowerSpec PC:

| Component | Detail |
|-----------|--------|
| **Host OS** | Windows 11 Home (Build 26200) + WSL2 |
| **Linux** | Ubuntu 22.04 (via WSL2) |
| **CPU** | Intel Core i9-14900KF — 24 cores / 32 threads @ 3.2 GHz |
| **RAM** | 64 GB DDR5 |
| **GPU** | NVIDIA RTX 5080 — 16 GB VRAM — Blackwell sm_120 |
| **NVIDIA Driver** | 591.86 (CUDA 13.1 runtime) |
| **Docker** | Docker Desktop with NVIDIA Container Toolkit GPU passthrough |
| **Base Image** | nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04 |
| **Python** | 3.12 (deadsnakes PPA inside Docker) |
| **PyTorch** | Nightly (cu128) — stable does NOT support sm_120 |
| **IDE** | VS Code + Dev Containers (.devcontainer/devcontainer.json) |
| **Remote Access** | Remote Coder @ https://100.67.128.123:8443 (Tailscale) |
| **AI Orchestration** | OpenClaw/Jarvis on MacBook Pro (100.101.203.113) via Telegram |
| **GitHub** | github.com/ericfbrown1-boop |

### Key Constraints
1. **16 GB VRAM limit** — Llama 3.3 70B (40GB+ even quantized) will NOT fit. Must use models ≤13B or offload strategies.
2. **PyTorch nightly only** — All CUDA/ML code must use `cu128` nightly builds.
3. **Everything in Docker** — No native installs on Windows. All services are containers.
4. **SSH keys don't persist** — Docker container rebuilds lose GitHub SSH keys. Must automate key injection.
5. **Docker Desktop must be running** — Before any GPU work or container operations.

---

## 1. Discovery & Analysis

### 1.1 Local LLM Selection (Revised for 16GB VRAM)

| Model | Parameters | Quantized Size | Context Window | Fits 16GB VRAM? | Verdict |
|-------|-----------|---------------|---------------|-----------------|---------|
| **Llama 3.3 70B Instruct** | 70B | ~35-40 GB (Q4) | 128K | ❌ NO | Too large even quantized |
| **Qwen 2.5 14B Instruct** | 14B | ~8 GB (Q4_K_M) | 128K | ✅ YES | Strong instruction-following, good structured output |
| **Llama 3.2 11B Instruct** | 11B | ~6.5 GB (Q4_K_M) | 128K | ✅ YES | Good general quality, leaves room for KV cache |
| **Mistral Nemo 12B** | 12B | ~7 GB (Q4_K_M) | 128K | ✅ YES | Excellent for structured extraction tasks |
| **Phi-4 14B** | 14B | ~8 GB (Q4_K_M) | 16K | ✅ YES but short context | Great reasoning but only 16K context — too short for full contracts |
| **Qwen 2.5 32B Instruct** | 32B | ~18 GB (Q4_K_M) | 128K | ⚠️ TIGHT | Fits with minimal KV cache headroom; may OOM on long docs |

**Decision: Qwen 2.5 14B Instruct (Q4_K_M)** — PRIMARY CHOICE

**Rationale:**
- 8 GB quantized leaves 8 GB for KV cache, OS overhead, and batch processing
- 128K context window handles contracts up to ~300 pages in a single pass
- Strong at structured JSON output extraction (critical for contract analysis)
- Excellent multilingual support (useful if contracts contain non-English clauses)
- Active community with frequent updates

**Fallback: Llama 3.2 11B Instruct** — if Qwen quality is insufficient on legal text

**Future upgrade path:** When PyTorch stable supports sm_120, revisit AWQ/GPTQ quantization of 32B models or use tensor parallelism if Eric adds a second GPU.

### 1.2 Inference Server Selection (Revised)

| Server | RTX 5080 sm_120 Support | Docker Ready | Notes |
|--------|------------------------|-------------|-------|
| **vLLM** | ⚠️ May need nightly | Yes (official image) | Best throughput, but requires CUDA compatibility check for Blackwell |
| **llama.cpp (llama-server)** | ✅ GGUF format, CPU fallback | Yes | Most portable, GGUF quantization, works regardless of CUDA version |
| **Ollama** | ✅ Wraps llama.cpp | Yes (official image) | Simplest setup, OpenAI-compatible API, pull models directly |
| **TGI (HuggingFace)** | ⚠️ May need nightly | Yes | Good but heavier setup |

**Decision: Two-tier inference**
1. **PRIMARY: Ollama** — Simplest deployment, pulls GGUF models directly, OpenAI-compatible API at `http://ollama:11434`. Proven sm_120 support via llama.cpp backend. Perfect for Docker Compose.
2. **STRETCH: vLLM** — If/when vLLM nightly confirms Blackwell sm_120 support, switch for better throughput on concurrent requests. Keep as optional upgrade.

**Why Ollama over raw llama.cpp:** Ollama provides model management (pull/list/delete), automatic quantization selection, health checks, and an OpenAI-compatible `/v1/chat/completions` endpoint — all critical for a Docker-native workflow.

### 1.3 PDF Extraction & OCR Tool Selection (Unchanged from v1)

| Tool | Type | Speed | Docker Friendly | Verdict |
|------|------|-------|----------------|---------|
| **PyMuPDF (fitz)** | Native text extraction | Very fast | ✅ pip install | **✅ DIGITAL PDFs** |
| **Marker (by Datalab)** | Full OCR + layout pipeline | 122 pg/min (GPU) | ✅ pip install + torch | **✅ SCANNED PDFs** |
| Tesseract + OCRmyPDF | Traditional OCR | 20-30 pg/min | ✅ apt install | Fallback only |

**Decision: Same two-tier pipeline as v1:**
1. PyMuPDF for digital PDFs (milliseconds, no GPU needed)
2. Marker for scanned PDFs (uses GPU via PyTorch — must use nightly cu128 build)

⚠️ **Marker + PyTorch nightly:** Marker depends on Surya (PyTorch-based OCR). Must verify Surya works with PyTorch nightly cu128 on sm_120. If not, fall back to Tesseract for OCR.

### 1.4 Supporting Infrastructure

| Component | Tool | Docker Image | Notes |
|-----------|------|-------------|-------|
| **Task Queue** | Redis 7 | `redis:7-alpine` | Lightweight, proven |
| **Object Storage** | MinIO | `minio/minio:latest` | S3-compatible, stores PDFs + results |
| **Database** | PostgreSQL 16 + pgvector | `pgvector/pgvector:pg16` | Metadata + vector search |
| **Embeddings** | BGE-large-en-v1.5 | Runs in analysis container | ~1.3 GB model, fits alongside LLM |
| **API** | FastAPI | Custom Dockerfile | Python 3.12 |
| **Dashboard** | React + Vite | `node:20-alpine` (build) + nginx (serve) | Static SPA |
| **Monitoring** | Prometheus + Grafana | Official images | Optional Phase 5 |
| **Reverse Proxy** | Traefik or Caddy | Official images | TLS + routing |

---

## 2. Architecture & Design

### 2.1 Docker Compose Architecture

```
docker-compose.yml
├── ollama          (GPU)   — LLM inference server + Qwen 2.5 14B
├── worker-extract  (CPU)   — PDF extraction (PyMuPDF + Marker)
├── worker-analyze  (CPU*)  — LLM analysis orchestrator (calls Ollama API)
├── api             (CPU)   — FastAPI ingestion + results API
├── dashboard       (CPU)   — React SPA (nginx)
├── redis           (CPU)   — Task queue
├── postgres        (CPU)   — Metadata + pgvector
├── minio           (CPU)   — Object storage (PDFs + reports)
└── monitoring      (CPU)   — Prometheus + Grafana (Phase 5)

* worker-analyze calls Ollama over HTTP — does NOT need GPU directly
```

### 2.2 Dockerfile Hierarchy

```
dockerfiles/
├── base.Dockerfile          # nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04
│                            # + Python 3.12, PyTorch nightly cu128, common deps
│
├── extraction.Dockerfile    # FROM base
│                            # + PyMuPDF, Marker, Surya, Tesseract (fallback)
│
├── analysis.Dockerfile      # FROM python:3.12-slim (no GPU needed!)
│                            # + httpx, celery, redis, pydantic
│                            # Calls Ollama API over HTTP
│
├── api.Dockerfile           # FROM python:3.12-slim
│                            # + FastAPI, uvicorn, SQLAlchemy, MinIO client
│
└── dashboard.Dockerfile     # Multi-stage: node:20 build → nginx serve
```

**Key insight:** Only the `ollama` container and `worker-extract` (for Marker OCR) need GPU access. The analysis worker calls Ollama's HTTP API — it does NOT need a GPU itself. This prevents GPU memory contention.

### 2.3 Dev Container Configuration

```json
// .devcontainer/devcontainer.json
{
  "name": "Contract PDF Analyzer",
  "dockerComposeFile": "../docker-compose.yml",
  "service": "api",
  "workspaceFolder": "/workspace",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-toolsai.jupyter",
        "redhat.vscode-yaml",
        "bradlc.vscode-tailwindcss"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python3",
        "python.testing.pytestEnabled": true
      }
    }
  },
  "forwardPorts": [8000, 3000, 9090, 11434],
  "postCreateCommand": "pip install -e '.[dev]'"
}
```

### 2.4 High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DOCKER COMPOSE NETWORK                          │
│                                                                     │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────────────────┐  │
│  │ MinIO    │◄───│  API         │───▶│  Redis                    │  │
│  │ (S3)     │    │  (FastAPI)   │    │  - pdf_extract queue      │  │
│  │ Port 9000│    │  Port 8000   │    │  - llm_analyze queue      │  │
│  └──────────┘    └──────────────┘    │  - post_process queue     │  │
│                                      └──────────┬────────────────┘  │
│                                                  │                   │
│  ┌───────────────────────────────────────────────┼───────────────┐  │
│  │           EXTRACTION WORKERS (GPU optional)   │               │  │
│  │                                               ▼               │  │
│  │  ┌─────────┐   Digital?   ┌────────┐                         │  │
│  │  │ PyMuPDF │◄── YES ─────│Classify │                         │  │
│  │  └────┬────┘              └────┬────┘                         │  │
│  │       │                    NO  │                               │  │
│  │       │               ┌───────▼──────┐                        │  │
│  │       │               │ Marker (OCR) │ ← GPU for scanned PDFs │  │
│  │       │               └───────┬──────┘                        │  │
│  │       └───────┬───────────────┘                               │  │
│  │               ▼                                                │  │
│  │    ┌─────────────────┐                                        │  │
│  │    │ Markdown Output │──▶ Redis: llm_analyze queue            │  │
│  │    └─────────────────┘                                        │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │           ANALYSIS WORKERS (CPU only — calls Ollama HTTP)     │  │
│  │                                                               │  │
│  │  ┌──────────────────┐    ┌─────────────────────────────┐     │  │
│  │  │  Ollama Server   │◄───│  Analysis Worker             │     │  │
│  │  │  Qwen 2.5 14B   │    │  - 5-pass analysis pipeline  │     │  │
│  │  │  Port 11434      │    │  - Structured JSON output    │     │  │
│  │  │  🎮 GPU (RTX 5080)│   │  - Retry + validation       │     │  │
│  │  └──────────────────┘    └─────────────┬───────────────┘     │  │
│  └────────────────────────────────────────┼─────────────────────┘  │
│                                           │                         │
│  ┌────────────────────────────────────────┼─────────────────────┐  │
│  │           STORAGE & SERVING            │                     │  │
│  │                                        ▼                     │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐ │  │
│  │  │ PostgreSQL   │  │ pgvector     │  │ React Dashboard    │ │  │
│  │  │ + pgvector   │  │ embeddings   │  │ Port 3000          │ │  │
│  │  │ Port 5432    │  │              │  │ (nginx)            │ │  │
│  │  └──────────────┘  └──────────────┘  └────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.5 GPU Memory Budget (RTX 5080 — 16 GB)

| Consumer | Estimated VRAM | Notes |
|----------|---------------|-------|
| Qwen 2.5 14B Q4_K_M | ~8 GB | GGUF quantized via Ollama |
| KV Cache (32K context) | ~2-3 GB | Scales with context length |
| Marker OCR (when active) | ~2-3 GB | Surya models for scanned PDFs |
| CUDA/Driver overhead | ~1 GB | Fixed |
| **Total** | **~13-15 GB** | Fits within 16 GB with margin |

⚠️ **Important:** Marker OCR and Ollama inference should NOT run simultaneously at peak. The extraction queue and analysis queue should be configured with concurrency limits to prevent OOM:
- Ollama: `OLLAMA_NUM_PARALLEL=1` (single concurrent request)
- Marker: Max 1 concurrent OCR job when GPU is in use
- If only digital PDFs (PyMuPDF, no GPU), Ollama can use full VRAM

### 2.6 LLM Analysis Strategy (Same 5-pass as v1)

| Pass | Purpose | Prompt Strategy |
|------|---------|-----------------|
| 1 — Section Extraction | Identify and label contract sections | "Parse this contract and return JSON array of sections with titles and page ranges" |
| 2 — Term Extraction | Extract key terms per section | "Extract defined terms, parties, dates, monetary values, obligations" |
| 3 — Risk Analysis | Flag problematic clauses | "Identify liability caps, indemnification gaps, auto-renewal traps, termination penalties" |
| 4 — Obligation Mapping | Map who owes what to whom | "List obligations with responsible party, deadline, consequence of breach" |
| 5 — Summary | Executive summary | "500-word summary: parties, purpose, key terms, risks, recommended actions" |

**Context strategy for 14B model:** With 128K context but smaller model capacity, chunk contracts >50K tokens into sections and analyze per-section. Aggregate results in a final pass. This compensates for the smaller model's reduced ability to track long-range dependencies compared to 70B.

---

## 3. Task Decomposition

### Phase 1: Foundation & Docker Setup (Week 1-2)

| # | Task | Dependencies | Agent | Notes |
|---|------|-------------|-------|-------|
| 1.1 | Create project repo structure, .devcontainer config, and base Dockerfiles | None | Coder | GitHub repo: ericfbrown1-boop/contract-pdf-analyzer |
| 1.2 | Build `base.Dockerfile` — CUDA 12.8 + Python 3.12 + PyTorch nightly cu128 | None | Coder | Test: `python -c "import torch; print(torch.cuda.is_available())"` must pass |
| 1.3 | Create `docker-compose.yml` with all services (Ollama, Redis, PostgreSQL, MinIO, API) | 1.1 | Coder | GPU passthrough for Ollama container only |
| 1.4 | Deploy Ollama container, pull Qwen 2.5 14B model, verify GPU inference | 1.3 | Coder | Test: `curl ollama:11434/v1/chat/completions` with test prompt |
| 1.5 | Set up PostgreSQL schema: `contracts`, `extractions`, `analyses`, `audit_log` + pgvector extension | 1.3 | Coder | Include Alembic migrations |
| 1.6 | Configure MinIO buckets: `raw-pdfs/`, `extracted/`, `analysis/`, `reports/` | 1.3 | Coder | |
| 1.7 | Build FastAPI ingestion API skeleton (upload endpoint, health check, status tracking) | 1.5, 1.6 | Coder | |

### Phase 2: Extraction Pipeline (Week 2-3)

| # | Task | Dependencies | Agent | Notes |
|---|------|-------------|-------|-------|
| 2.1 | Build `extraction.Dockerfile` — base image + PyMuPDF + Marker + Tesseract | 1.2 | Coder | Verify Marker works with PyTorch nightly cu128 on sm_120 |
| 2.2 | Implement PDF classifier (digital vs scanned via PyMuPDF text density threshold) | 2.1 | Coder | Threshold: >95% non-whitespace = digital |
| 2.3 | Implement PyMuPDF extraction worker → Markdown output | 2.2 | Coder | Celery worker consuming `pdf_extract` queue |
| 2.4 | Implement Marker OCR extraction worker → Markdown output | 2.2 | Coder | GPU-aware: check VRAM availability before starting |
| 2.5 | Build chunking pipeline (recursive text splitter, 2K tokens, 200 overlap) | 2.3, 2.4 | Coder | |
| 2.6 | Deploy BGE-large-en-v1.5 embedding model inside analysis container, store vectors in pgvector | 2.5 | Coder | Runs on CPU — no GPU needed for embeddings |
| 2.7 | Celery worker config with concurrency limits (max 1 GPU job at a time) | 2.3, 2.4 | Coder | Prevent Marker + Ollama GPU contention |

### Phase 3: LLM Analysis Engine (Week 3-5)

| # | Task | Dependencies | Agent | Notes |
|---|------|-------------|-------|-------|
| 3.1 | Build `analysis.Dockerfile` — Python 3.12 slim + httpx + Celery + Pydantic | None (parallel) | Coder | NO GPU — calls Ollama over HTTP |
| 3.2 | Design and test 5 analysis prompt templates against sample contracts | 3.1, 1.4 | Coder + manual review | Test with Ollama API directly, iterate on JSON output quality |
| 3.3 | Build LLM analysis Celery worker — orchestrates 5-pass analysis per contract | 3.1, 3.2, 2.5 | Coder | Sequential passes, structured JSON validation between each |
| 3.4 | Implement structured output parsing (Pydantic models, JSON retry logic, fallback prompts) | 3.3 | Coder | If JSON parse fails, retry with "fix this JSON" prompt |
| 3.5 | Build analysis result storage (PostgreSQL JSONB columns + indexed fields for search) | 3.3, 1.5 | Coder | |
| 3.6 | Implement context-length-aware chunking: if contract >50K tokens, split into sections and analyze per-section | 3.3 | Coder | Compensates for 14B model's limitations on very long docs |

### Phase 4: API & Dashboard (Week 5-7)

| # | Task | Dependencies | Agent | Notes |
|---|------|-------------|-------|-------|
| 4.1 | Extend FastAPI with analysis results endpoints (per-contract, bulk, search, export) | 3.5 | Coder | |
| 4.2 | Implement semantic search API (pgvector similarity search across contract corpus) | 2.6, 4.1 | Coder | |
| 4.3 | Build `dashboard.Dockerfile` — React + Vite → nginx | None (parallel) | Coder | Multi-stage build |
| 4.4 | Build React dashboard — upload, status tracking, results viewer, risk heatmap | 4.1 | Coder | |
| 4.5 | Implement report generation (PDF summary reports via ReportLab, CSV/JSON export) | 4.1 | Coder | |
| 4.6 | Add JWT authentication and role-based access control | 4.1 | Coder | |

### Phase 5: Hardening & Monitoring (Week 7-9)

| # | Task | Dependencies | Agent | Notes |
|---|------|-------------|-------|-------|
| 5.1 | Add Prometheus metrics to all services + Grafana dashboards | All | Coder | GPU utilization, queue depth, inference latency, OCR throughput |
| 5.2 | Implement retry logic, dead-letter queues, error recovery in Celery | All | Coder | |
| 5.3 | Load testing — target: 200 contracts/hour on single RTX 5080 | All | Coder | Realistic for 14B model |
| 5.4 | Implement GPU memory monitoring and automatic throttling | All | Coder | If VRAM >14GB, pause Marker OCR jobs |
| 5.5 | Add audit logging, data retention policies, MinIO lifecycle rules | All | Coder | |
| 5.6 | Docker health checks for all containers + restart policies | All | Coder | |

### Phase 6: Optimization (Week 9-10)

| # | Task | Dependencies | Agent | Notes |
|---|------|-------------|-------|-------|
| 6.1 | Prompt optimization — A/B test prompts against labeled contract dataset | 3.2 | Researcher + Coder | |
| 6.2 | Evaluate Qwen 2.5 32B (Q3_K_M, ~18GB) if quality insufficient | 5.3 | Coder | May require reducing KV cache or disabling concurrent Marker |
| 6.3 | Evaluate vLLM with Blackwell support (when available) for throughput upgrade | 5.3 | Coder | |
| 6.4 | Implement Redis caching for repeated clause patterns | All | Coder | |
| 6.5 | Fine-tune Qwen 2.5 14B on contract-specific dataset (QLoRA) | 6.1 | Coder | QLoRA fits in 16GB VRAM for training |

---

## 4. Risk Assessment

### Critical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **14B model quality insufficient for legal analysis** | Medium | Degraded accuracy | Benchmark against 10 manually-reviewed contracts before committing. Fallback: use Claude API for high-value contracts only. |
| **GPU OOM when Marker OCR + Ollama run simultaneously** | High | Container crash | Celery concurrency limits: max 1 GPU consumer. Queue priority: Ollama > Marker. Monitor VRAM via nvidia-smi. |
| **PyTorch nightly cu128 breaks Marker/Surya** | Medium | OCR pipeline down | Pin specific nightly version in Dockerfile. Test Marker independently before integration. Fallback: Tesseract (CPU-only). |
| **LLM hallucination in contract analysis** | High | Incorrect risk flags | Source page references in every prompt. Confidence scoring. Never present as legal advice. Human review workflow. |
| **RTX 5080 sm_120 not supported by vLLM/TGI** | Medium | Can't upgrade inference server | Stay on Ollama (llama.cpp backend, proven sm_120). Revisit quarterly. |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Docker Desktop crashes or WSL2 memory leak** | Medium | All services down | WSL2 memory limit in `.wslconfig` (48GB). Docker Desktop auto-restart. Persistent volumes survive restarts. |
| **SSH keys lost on container rebuild** | High | GitHub push fails | Mount SSH keys as Docker volume from WSL2 home, or use GitHub PAT in env var. |
| **Storage growth** | High | Disk full | MinIO lifecycle policies. Compress extracted text. Monitor disk in Grafana. |
| **Model updates break prompts** | Medium | Analysis regression | Pin Ollama model tag (e.g., `qwen2.5:14b-instruct-q4_K_M`). Prompt regression test suite. |

### Compliance Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Contracts contain PII** | High | Data breach | All processing local (no cloud APIs). MinIO server-side encryption. RBAC on all endpoints. |
| **Users treat AI analysis as legal advice** | High | Liability | Clear disclaimers. Confidence scores. Human-in-the-loop review. |

---

## 5. Technology Stack Summary

```
┌──────────────────────────────────────────────────────┐
│              TECHNOLOGY STACK (v2)                     │
├──────────────────────────────────────────────────────┤
│ LLM:           Qwen 2.5 14B Instruct (Q4_K_M GGUF) │
│ Inference:     Ollama (OpenAI-compatible API)         │
│ PDF (digital): PyMuPDF (fitz)                         │
│ PDF (scanned): Marker (Surya OCR) + Tesseract backup │
│ Embeddings:    BGE-large-en-v1.5 (CPU)               │
│ Vector DB:     PostgreSQL 16 + pgvector              │
│ Task Queue:    Redis 7 + Celery                      │
│ Object Store:  MinIO (S3-compatible)                 │
│ Database:      PostgreSQL 16                         │
│ API:           FastAPI (Python 3.12)                 │
│ Dashboard:     React + Vite + TypeScript             │
│ Runtime:       Docker Compose (all services)         │
│ IDE:           VS Code + Dev Containers              │
│ Monitoring:    Prometheus + Grafana                   │
│ GPU:           NVIDIA RTX 5080 16GB (sm_120)         │
│ CUDA:          12.8 + PyTorch nightly cu128          │
│ Remote Access: Tailscale + Remote Coder              │
│ Orchestration: OpenClaw/Jarvis (MacBook Pro)         │
└──────────────────────────────────────────────────────┘
```

---

## 6. Key Design Decisions & Rationale (v2 Changes)

1. **Qwen 2.5 14B over Llama 3.3 70B** — 70B models require 40GB+ VRAM even quantized. RTX 5080 has 16GB. Qwen 2.5 14B fits comfortably at 8GB quantized, leaving room for KV cache and Marker OCR. Quality trade-off is real but manageable with better prompts and multi-pass analysis.

2. **Ollama over vLLM** — vLLM may not yet support Blackwell sm_120 architecture. Ollama uses llama.cpp backend which has proven sm_120 support. Simpler Docker deployment, built-in model management, and OpenAI-compatible API. Swap to vLLM later when Blackwell support is confirmed.

3. **Everything in Docker Compose** — Matches Eric's IDE workflow (VS Code Dev Containers). All services defined in one `docker-compose.yml`. GPU passthrough only for Ollama and extraction worker. Easy to start/stop entire stack.

4. **CPU-only analysis workers** — Analysis workers call Ollama's HTTP API; they don't need GPU access. This prevents GPU memory contention and allows scaling analysis workers independently.

5. **GPU memory budgeting with concurrency limits** — Single RTX 5080 shared between Ollama inference and Marker OCR. Celery configured to never run both GPU workloads simultaneously.

6. **PyTorch nightly pinning** — Pin specific nightly date in Dockerfiles to prevent breakage. Test Marker/Surya compatibility before upgrading nightly version.

7. **Coder agent drives implementation via Remote Coder** — OpenClaw Coder agent on MacBook connects to PowerSpec via Tailscale (100.67.128.123:8443) to execute commands. All code lives in Docker on the PowerSpec.

---

## 7. Estimated Throughput (Single RTX 5080)

| Metric | Estimate |
|--------|----------|
| Qwen 2.5 14B inference speed | ~40-60 tokens/sec output |
| Average contract | ~15K tokens input |
| Time per analysis pass | ~10-15 seconds |
| 5 passes per contract | ~50-75 seconds total LLM time |
| Digital PDF extraction | <1 second (PyMuPDF) |
| Scanned PDF OCR | ~30-60 seconds per 10-page doc (Marker) |
| **Contracts per hour (digital)** | **~50-70** |
| **Contracts per hour (scanned)** | **~30-40** |
| **Contracts per day (8hr)** | **~400-560 (digital) / ~240-320 (scanned)** |

---

*This plan is ready for implementation. Start with Phase 1 (Docker foundation) — tasks 1.1 through 1.4 can begin immediately. Phase 3.1 (analysis Dockerfile) can run in parallel since it has no dependencies.*

*The Coder agent should clone the repo on the PowerSpec via Remote Coder, then open VS Code Dev Containers to work inside the Docker environment.*
