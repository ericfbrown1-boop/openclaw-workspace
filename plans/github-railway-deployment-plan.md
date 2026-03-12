# GitHub + Railway Deployment Plan
## Project Scraper & Contract Analyzer

**Prepared for:** Eric Brown, CFO & COO, Cohesity
**Date:** March 7, 2026

---

## Executive Summary

Railway (railway.app) is a cloud platform that deploys apps directly from GitHub repos with auto-deploy on push. It supports Docker, handles environment variables securely, and charges per-second for actual resource usage. Both Project Scraper and Contract Analyzer can run on Railway with custom Dockerfiles. Estimated monthly cost: **$15–50/month** depending on usage.

---

## 1. Railway Overview

### What It Is
- Cloud deployment platform — push code to GitHub, get a live URL
- Supports Docker, Node.js, Python natively
- Auto-deploys on every `git push` to connected branch
- Managed infrastructure — no server management needed

### Pricing (2026)
| Plan | Monthly Base | Included | Limits |
|------|-------------|----------|--------|
| **Free** | $0 ($1/mo after 30-day trial) | $5 credits | 1 vCPU, 0.5 GB RAM |
| **Hobby** | $5 minimum | $5 credits | 48 vCPU, 48 GB RAM, 5 GB storage |
| **Pro** | $20 minimum | $20 credits | 1000 vCPU, 1 TB RAM, 1 TB storage |
| **Enterprise** | Custom | Custom | SSO, RBAC, HIPAA, dedicated VMs |

**Resource Pricing (pay-as-you-go):**
- CPU: ~$0.000463/vCPU-min (~$0.67/vCPU-day)
- Memory: ~$0.000231/GB-min (~$0.33/GB-day)
- Volumes: $0.015/GB-month (for persistent storage)
- Egress: $0.05/GB

### Key Features
- **GitHub integration:** Connect repo → auto-deploy on push
- **Environment variables:** Secure secrets management (API keys)
- **Volumes:** Persistent storage for uploaded files
- **Custom Dockerfiles:** Full control over system packages (Tesseract, Playwright, etc.)
- **Custom domains:** yourapp.yourdomain.com
- **Logs & monitoring:** Built-in dashboard

---

## 2. Architecture: Contract Analyzer on Railway

### Current Architecture (Local)
```
PDF files → pdfplumber/Tesseract OCR → Claude API → JSON analysis → Word report
```
All runs on Eric's MacBook Pro via CLI scripts.

### Proposed Railway Architecture
```
┌─────────────────────────────────────────────┐
│                   Railway                     │
│                                               │
│  ┌──────────────┐    ┌────────────────────┐  │
│  │  Web UI       │    │  Worker Service     │  │
│  │  (Flask/      │───▶│  (Python +          │  │
│  │   FastAPI)    │    │   Tesseract +       │  │
│  │               │    │   pdfplumber)       │  │
│  │  - Upload PDF │    │                     │  │
│  │  - View status│    │  → Claude API       │  │
│  │  - Download   │    │  → JSON + DOCX      │  │
│  │    reports    │    │                     │  │
│  └──────────────┘    └────────────────────┘  │
│         │                      │              │
│         └──────┬───────────────┘              │
│                ▼                              │
│  ┌────────────────────────┐                  │
│  │  Volume (persistent)    │                  │
│  │  /data/uploads/         │                  │
│  │  /data/output/          │                  │
│  └────────────────────────┘                  │
└─────────────────────────────────────────────┘
```

### Dockerfile for Contract Analyzer
```dockerfile
FROM python:3.11-slim

# Install system dependencies (Tesseract, Poppler for pdf2image)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port for web UI
EXPOSE 8000

# Run with Gunicorn for production
CMD ["gunicorn", "web_app:app", "--bind", "0.0.0.0:8000", "--timeout", "600", "--workers", "2"]
```

### Web UI (New — Flask/FastAPI)
You'd need to add a simple web app (web_app.py) with:
1. **Upload page:** Drag & drop PDFs
2. **Processing status:** Shows progress as each contract is analyzed (websocket updates)
3. **Results dashboard:** View all contracts, risk scores, key flags
4. **Download:** Get the Word report or individual JSONs
5. **Query interface:** Ask questions about the contracts (future: LlamaIndex integration)

### Environment Variables (Railway Dashboard)
```
ANTHROPIC_API_KEY=sk-ant-api03-...
GOOGLE_SHEETS_CREDENTIALS=<base64-encoded service account JSON>
OUTPUT_DIR=/data/output
UPLOAD_DIR=/data/uploads
```

### Step-by-Step Deployment

1. **Create Railway account:** https://railway.com → Sign up with GitHub
2. **Install Railway CLI:**
   ```bash
   brew install railway
   railway login
   ```
3. **Create new project:**
   ```bash
   cd ~/ContractAnalyzer
   railway init
   ```
4. **Connect GitHub repo:**
   - Railway Dashboard → New Project → Deploy from GitHub
   - Select `ericfbrown1-boop/ContractAnalyzer`
   - Set branch: `main`
5. **Add environment variables:**
   - Railway Dashboard → Variables → Add `ANTHROPIC_API_KEY`, etc.
6. **Add Dockerfile** (as above) and `requirements.txt` to repo
7. **Add web_app.py** (Flask/FastAPI web interface — ~200 lines)
8. **Add persistent volume:**
   - Railway Dashboard → Service → Volumes → Mount at `/data`
9. **Push to deploy:**
   ```bash
   git add -A && git commit -m "feat: add Railway web deployment"
   git push origin main
   # Railway auto-deploys!
   ```
10. **Custom domain (optional):**
    - Railway Dashboard → Settings → Custom Domain → `contracts.yourdomain.com`

### Estimated Cost: Contract Analyzer
- Idle web UI (always on): ~$3/month (0.25 vCPU, 256MB RAM)
- Processing 12 contracts: ~$0.50 per run (30 min burst at 1 vCPU, 1GB RAM)
- Volume storage: ~$0.15/month (1 GB)
- **Total: ~$5–10/month** for typical usage

---

## 3. Architecture: Project Scraper on Railway

### Challenge: Playwright + Chromium
Project Scraper uses Playwright to crawl websites, which requires a full Chromium binary. This works on Railway but needs a custom Dockerfile with Playwright's system dependencies.

### Dockerfile for Project Scraper
```dockerfile
FROM mcr.microsoft.com/playwright:v1.44.0-jammy

WORKDIR /app

# Install Node.js dependencies
COPY package*.json ./
RUN npm ci

# Install Playwright browsers
RUN npx playwright install chromium

# Copy application code
COPY . .

EXPOSE 3000

CMD ["node", "server.js"]
```

### Web UI Concept
1. **Target URL input:** Enter a company website (e.g., rubrik.com)
2. **Crawl configuration:** Max pages, depth, include/exclude patterns
3. **Live progress:** Pages discovered, pages crawled, content extracted
4. **Results:** Site map, extracted content, Google Sheets export
5. **History:** Previous crawl results

### Estimated Cost: Project Scraper
- Playwright + Chromium needs more RAM: ~1-2 GB
- Active crawling: ~$0.02/hour (1 vCPU, 2GB RAM)
- Idle (if always on): ~$8/month
- **Better approach:** Use Railway's sleep feature — service starts on request, sleeps when idle
- **Total: ~$5–15/month** depending on crawl frequency

---

## 4. Personal vs Corporate Use

### Personal Use (Recommended Starting Point)
- Railway Hobby plan ($5/month)
- GitHub personal account (already set up)
- Direct URL access (Railway provides `*.up.railway.app` domain)
- Basic auth (username/password) on the web UI
- Good for: testing, personal contract analysis, ad-hoc crawls

### Internal Corporate Use (Cohesity)
Would require:
- Railway **Enterprise** plan (SSO, RBAC, HIPAA BAAs)
- Or: Deploy to Cohesity's own infrastructure (AWS/GCP/Azure with Docker)
- Corporate GitHub (GitHub Enterprise or Cohesity's org)
- VPN/Zero-trust access (Zscaler, Cloudflare Access, etc.)
- SOC 2 compliance considerations
- IT security review for handling customer contracts (Morgan Stanley data)

**Recommendation:** Start personal, prove value, then work with Cohesity IT for corporate deployment if needed.

---

## 5. Comparison: Railway vs Alternatives

| Feature | Railway | Render | Fly.io | Heroku |
|---------|---------|--------|--------|--------|
| GitHub auto-deploy | ✅ | ✅ | ✅ | ✅ |
| Docker support | ✅ | ✅ | ✅ | ✅ (paid) |
| Persistent volumes | ✅ (5GB hobby) | ✅ | ✅ | ❌ (add-on) |
| Playwright support | ✅ (Docker) | ✅ (Docker) | ✅ (Docker) | ❌ (difficult) |
| Pricing model | Per-second | Per-instance | Per-second | Per-dyno |
| Sleep when idle | ✅ | ✅ (free tier) | ✅ | ✅ |
| Custom domains | ✅ | ✅ | ✅ | ✅ |
| SSO/Enterprise | ✅ | ✅ | ❌ | ✅ |
| **Best for** | **Simple deploys** | Static sites | Global edge | Legacy apps |

**Verdict:** Railway is the best choice for these projects — simplest GitHub integration, per-second billing (no waste), Docker support, and persistent volumes.

---

## 6. Implementation Timeline

| Phase | Task | Time |
|-------|------|------|
| Week 1 | Add web_app.py (Flask UI) to Contract Analyzer | 4–6 hours |
| Week 1 | Create Dockerfile + requirements.txt | 1–2 hours |
| Week 1 | Deploy Contract Analyzer to Railway | 1 hour |
| Week 2 | Add server.js (Express UI) to Project Scraper | 4–6 hours |
| Week 2 | Create Dockerfile for Playwright | 1–2 hours |
| Week 2 | Deploy Project Scraper to Railway | 1 hour |
| Week 3 | Add auth, polish UI, custom domain | 2–4 hours |
| **Total** | | **~15–22 hours** |

---

## 7. Risks & Gotchas

1. **Playwright memory:** Chromium needs 1-2 GB RAM. Railway Hobby allows up to 48 GB, so this is fine, but costs more per-minute.
2. **Long-running jobs:** Contract Analyzer can take 30+ minutes for all 12 PDFs. Railway has no hard timeout for Docker services, but you should use background job processing (Celery or similar) with a web socket for status updates.
3. **Volume storage limits:** Hobby plan = 5 GB. Enough for PDFs and reports, but watch if you accumulate many crawl results.
4. **Cold starts:** If using sleep-when-idle, first request takes 10–30 seconds to spin up.
5. **Morgan Stanley data sensitivity:** Customer contracts are highly sensitive. For corporate use, ensure Railway's security posture (SOC 2 Type II) meets Cohesity's requirements, or deploy to Cohesity's own cloud.
6. **API key exposure:** Railway's env vars are encrypted at rest, but ensure the web UI itself has authentication so random people can't trigger Claude API calls on your dime.

---

## 8. Recommendation

**Start with Contract Analyzer on Railway Hobby ($5/month).** It's the simpler deployment (no Playwright), higher immediate value (you use it regularly), and lower risk. Add Project Scraper as a second service once the first is stable.

**Total estimated cost for both apps: $10–25/month** for personal use.

---

*Prepared by Jarvis AI for Eric Brown*
