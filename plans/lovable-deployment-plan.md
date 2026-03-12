# Lovable Deployment Plan: Project Scraper & Contract Analyzer
**Prepared:** 2026-03-07  
**For:** Eric Brown, CFO & COO, Cohesity  
**By:** Jarvis (AI Research Agent)

---

## Executive Summary

**Bottom line up front:** Lovable is the wrong tool for both programs in their current form. It excels at rapid UI prototyping for front-end-heavy apps, but both of your programs are fundamentally backend-heavy workloads requiring Python, headless browsers, OCR binaries, and long-running processes — none of which Lovable can run natively.

**The good news:** Both programs *can* become polished web apps. The recommended path is a **hybrid architecture** — Lovable or React for the UI front-end, combined with a proper backend host (Railway or Render) for the heavy lifting. Contract Analyzer already *has* a React frontend and FastAPI backend; it's essentially ready to deploy today. Project Scraper needs a small backend API wrapper written around its Node.js/Playwright core.

**Estimated all-in cost:** $50–$120/month for both apps running continuously.  
**Realistic timeline:** 2–3 weeks to full deployment.

---

## Section 1: What is Lovable?

Lovable (lovable.dev) is an AI-powered web app builder that generates React + TypeScript code from natural language prompts. Think of it as "ChatGPT that writes your entire frontend and wires up a Supabase database for you."

### What Lovable Actually Does

- **Frontend generation:** Creates Vite + React + TypeScript UIs with Tailwind CSS and shadcn/ui components
- **Database:** Integrates with Supabase (hosted PostgreSQL) — tables, auth, row-level security, all auto-generated
- **Serverless backend:** Deploys Supabase Edge Functions (JavaScript/TypeScript only, Deno runtime)
- **Hosting:** Deploys the React app to Lovable's own CDN/hosting
- **GitHub sync:** Two-way sync with GitHub repos — you can export code and keep editing in Cursor/VS Code
- **Custom domains:** Supported on Pro+ plans
- **Secrets management:** API keys stored in Supabase Vault, accessed via Edge Functions only (never in client code)
- **Security scanning:** Automated RLS analysis, code review, npm dependency audit before publishing

### What Lovable Cannot Do

| Capability | Status | Why |
|---|---|---|
| Run Python | ❌ Not supported | Supabase Edge Functions are JS/TS (Deno) only |
| Run Playwright/headless browsers | ❌ Not supported | Sandboxed serverless environment, no Chromium binary |
| Tesseract OCR | ❌ Not supported | Requires native binary, not available in serverless |
| Long-running processes (>30s) | ❌ Not supported | Serverless timeouts (typically 10–30 seconds) |
| Docker containers | ❌ Not supported | Lovable is not a container host |
| Cron/scheduled jobs | ⚠️ Limited | Supabase pg_cron exists but is very basic |
| Background workers (Celery, etc.) | ❌ Not supported | No persistent process support |
| File processing >50MB | ⚠️ Limited | Supabase Storage has limits; no streaming |
| Custom runtimes | ❌ Not supported | Locked to Deno/JS for Edge Functions |

### Lovable Pricing (2026)

**Platform subscription (for building the app with AI prompts):**
| Plan | Monthly | Annual | Credits/month | Key Features |
|---|---|---|---|---|
| Free | $0 | — | 30 | No custom domain, Lovable badge |
| Pro | $25 | $21/mo | 100 | Custom domain, no badge, code mode |
| Pro 200 | $50 | $42/mo | 200 | Same as Pro, 2x credits |
| Pro 400 | $100 | $84/mo | 400 | Power users |
| Business | $50+ | $42+/mo | 100+ | SSO, data training opt-out |

**Important caveat:** Credits are consumed per AI prompt, and complex changes burn credits fast. Users report burning through a $25 plan in days during active development. Budget $50–$100/month for the build phase.

**Hosting:** After building, the deployed app runs on Lovable's CDN at no additional charge (included in plan). However, you still pay Supabase for database/storage usage.

---

## Section 2: Current Program Analysis

### 2A: Project Scraper
**Location:** `~/ProjectScraper/code/`  
**Stack:** Node.js + Playwright (headless Chromium)  
**What it does:**
- Launches a headless Chromium browser
- Crawls target company websites (e.g., rubrik.com) following internal links
- Maps site structure (sections, hierarchy, URLs)
- Downloads one sample document per section
- Exports data to Google Sheets via Zapier MCP

**Key dependencies:**
- `playwright` (requires Chromium binary ~150MB)
- `fs`, `path` (Node.js standard library)
- Runs as a long-duration CLI process (crawls can take 30+ minutes)

**Lovable compatibility:** ❌ **Fundamentally incompatible with Lovable backend**
- Playwright requires a full Chromium installation — unavailable in Supabase Edge Functions
- Crawls are long-running (30+ minutes) — well beyond serverless timeouts
- The scraping logic is pure backend; there's nothing inherently frontend about it

### 2B: Contract Analyzer
**Location:** `~/ContractAnalyzer/`  
**GitHub:** `ericfbrown1-boop/ContractAnalyzer`  
**Stack:** Docker Compose with 7 services  
**What it does:**
- Accepts PDF contract uploads via REST API
- Processes through Docling (OCR), extracting text from both digital and scanned PDFs
- Sends extracted text to Claude API for structured analysis (42 fields, CUAD taxonomy)
- Scores risk using weighted taxonomy
- Presents results in a React dashboard with AG Grid

**Service inventory:**
| Service | Technology | Lovable Compatible? |
|---|---|---|
| Frontend | React + Vite | ✅ Yes — Lovable's core |
| API | FastAPI (Python) | ❌ Python, needs real server |
| Worker | Celery (Python) | ❌ Background process |
| OCR | Docling (Docker image) | ❌ Container, binary deps |
| Database | PostgreSQL + pgvector | ✅ Via Supabase |
| Cache/Queue | Redis | ❌ Needs persistent process |
| File Storage | MinIO (S3) | ✅ Via Supabase Storage |

**Lovable compatibility:** ⚠️ **Frontend only** — React UI could be rebuilt/hosted in Lovable, but all backend services need a real container host. Given that the frontend already exists and is React-based, the value of rebuilding it in Lovable is minimal.

---

## Section 3: Recommended Architecture

### Architecture A: Project Scraper as a Web App

**The concept:** A simple web dashboard where you enter a target company URL, click "Run Scraper," watch the crawl progress live, and download results — all without touching the terminal.

```
┌─────────────────────────────────────────────────┐
│           BROWSER (User Interface)               │
│  Lovable-generated React App OR simple HTML      │
│  - URL input form                                │
│  - Progress feed (WebSocket/polling)             │
│  - Results table with download button           │
└────────────────────┬────────────────────────────┘
                     │ REST API calls
┌────────────────────▼────────────────────────────┐
│           BACKEND (Railway or Render)            │
│  Node.js + Express wrapper around crawler.js     │
│  - POST /crawl  → starts a crawl job            │
│  - GET  /status/:id → job progress              │
│  - GET  /results/:id → JSON results             │
│  Playwright with Chromium installed              │
│  Job queue: Bull (Redis-backed) for concurrency  │
└────────────────────┬────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
┌─────────▼──────┐    ┌────────▼────────┐
│  Redis (job    │    │  Google Sheets  │
│  queue state)  │    │  API (results   │
│  Railway add-on│    │  export)        │
└────────────────┘    └────────────────┘
```

**Why this works:**
- The crawling logic in `crawler.js` barely needs to change — just wrap it in an Express route
- Railway supports Node.js + Playwright natively (you can install Chromium via `npx playwright install`)
- Jobs are queued so multiple crawls don't collision
- WebSocket or Server-Sent Events give live progress without polling

---

### Architecture B: Contract Analyzer as a Web App

**The concept:** The architecture already exists. It's a complete Docker Compose stack with a React frontend and FastAPI backend. The only missing piece is cloud hosting.

```
┌─────────────────────────────────────────────────┐
│           CONTRACT ANALYZER FRONTEND             │
│  Existing React + Vite app (~/ContractAnalyzer/  │
│  frontend/)                                      │
│  Deployed to: Vercel (free tier, ideal for React)│
│  Features already built:                         │
│  - Drag-and-drop PDF upload                      │
│  - Contract table with AG Grid                   │
│  - Risk scoring dashboard                        │
│  - Contract detail view                          │
└────────────────────┬────────────────────────────┘
                     │ REST API calls to Railway
┌────────────────────▼────────────────────────────┐
│           CONTRACT ANALYZER BACKEND              │
│  Railway (Docker Compose → separate services)    │
│  ├── FastAPI API server                         │
│  ├── Celery worker(s)                           │
│  └── Docling OCR service                        │
└────────────────────┬────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
┌─────────▼──────┐    ┌────────▼────────┐
│  Supabase OR   │    │  Supabase       │
│  Railway       │    │  Storage OR     │
│  PostgreSQL    │    │  Railway Volume │
└────────────────┘    └────────────────┘
```

**Why this works:**
- The frontend is already React — deploy to Vercel in under 10 minutes
- Railway supports Docker Compose natively — you can deploy the entire backend stack from your existing `docker-compose.yml` with minimal changes
- Supabase can replace PostgreSQL + MinIO, reducing operational complexity (optional)

---

## Section 4: Detailed Migration Steps

### Project Scraper: CLI → Web App

**Estimated effort: 3–5 days**

**Step 1: Create Express API wrapper** (Day 1)
```javascript
// server.js — wrap existing crawler.js logic
const express = require('express');
const { v4: uuidv4 } = require('uuid');
const app = express();

// POST /crawl — starts a new crawl job
app.post('/crawl', async (req, res) => {
  const { targetUrl, sections } = req.body;
  const jobId = uuidv4();
  // Queue crawl via Bull
  await crawlQueue.add({ jobId, targetUrl, sections });
  res.json({ jobId, status: 'queued' });
});

// GET /status/:id — check job progress
app.get('/status/:id', async (req, res) => {
  const job = await crawlQueue.getJob(req.params.id);
  res.json({ status: job.state, progress: job.progress() });
});
```

**Step 2: Refactor crawler.js for API use** (Day 1–2)
- Extract `runCrawl(config)` as an exported async function
- Add progress callbacks (emit events: `started`, `page_crawled`, `doc_downloaded`, `complete`)
- Return structured JSON results instead of writing to local files

**Step 3: Set up Railway project** (Day 2)
- Create Railway project, add Node.js service
- Add Playwright system dependencies to `Dockerfile`:
  ```dockerfile
  FROM node:20-slim
  RUN npx playwright install-deps chromium
  RUN npx playwright install chromium
  ```
- Add Redis add-on for job queue
- Set environment variables: `GOOGLE_SHEETS_API_KEY`, `CRAWL_TIMEOUT_MS`

**Step 4: Build the React UI** (Day 3–4)
- Create new Lovable project (or use Create React App/Vite directly)
- Prompt Lovable: *"Build a web dashboard for a web crawler. It has a URL input field, a 'Start Crawl' button, a live progress feed showing pages crawled, and a results table with columns: URL, Section, Title, Content Summary, Doc Downloaded."*
- Wire the UI to the Railway backend API

**Step 5: Connect Google Sheets output** (Day 4–5)
- Replace Zapier MCP with direct Google Sheets API calls from the Node.js backend
- Use service account credentials stored as Railway environment variables

**Step 6: Deploy and test** (Day 5)
- Railway auto-deploys on GitHub push
- Test full crawl of a sample domain
- Verify Google Sheets export works

---

### Contract Analyzer: Local Docker → Cloud Deployment

**Estimated effort: 2–4 days** (the hard work is done — architecture already exists)

**Step 1: Deploy frontend to Vercel** (Day 1, ~30 min)
```bash
cd ~/ContractAnalyzer/frontend
npx vercel --prod
# Set environment variable: VITE_API_URL=https://your-railway-backend.railway.app
```

**Step 2: Prepare Railway deployment** (Day 1–2)
- Create Railway project from GitHub repo
- Railway supports multi-service Docker Compose — deploy `api`, `worker`, `docling` as separate Railway services
- Critical: Update `docker-compose.yml` to use Railway's internal networking

**Step 3: Migrate PostgreSQL to Supabase** (Day 2–3, optional but recommended)
- Create Supabase project
- Export schema from local PostgreSQL: `pg_dump --schema-only`
- Apply to Supabase via SQL editor
- Update `DATABASE_URL` in Railway environment variables
- Advantage: Supabase free tier includes 500MB database + 1GB storage

**Step 4: Migrate MinIO to Supabase Storage** (Day 2–3, optional)
- Update `ocr_service.py` to use Supabase Storage SDK instead of MinIO client
- Alternatively, keep MinIO as a Railway volume (simpler but less reliable)

**Step 5: Configure secrets** (Day 3)
Railway environment variables to set:
```
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
LLM_PROVIDER=anthropic
```

**Step 6: CORS configuration** (Day 3)
- Update FastAPI CORS settings to allow the Vercel frontend domain:
  ```python
  origins = ["https://your-app.vercel.app", "https://your-custom-domain.com"]
  ```

**Step 7: Test end-to-end** (Day 4)
- Upload a test contract PDF
- Verify Celery task processes it
- Check Claude API analysis results
- Confirm Word report generation works

---

## Section 5: Where Lovable Fits (and Where It Doesn't)

| Use Case | Lovable? | Better Alternative |
|---|---|---|
| **Build Project Scraper UI** | ✅ Yes | Lovable, then export to GitHub |
| **Build Contract Analyzer UI** | ⚠️ Redundant | Already exists in React — just deploy it |
| **Host Project Scraper backend** | ❌ No | Railway (Node.js + Playwright) |
| **Host Contract Analyzer backend** | ❌ No | Railway (Docker Compose) |
| **Database** | ✅ Via Supabase | Supabase directly |
| **File storage** | ✅ Via Supabase | Supabase Storage |
| **Scheduled scraping (cron)** | ❌ Too limited | Railway cron jobs |
| **PDF processing** | ❌ No | Railway + Docling |
| **AI analysis (Claude)** | ✅ Via Edge Function | Direct API call from FastAPI |

**Verdict: Lovable is useful for one thing — rapidly building or iterating on the React UI for Project Scraper.** You could use Lovable to generate the dashboard UI in a few hours, then export the code to GitHub and deploy the frontend to Vercel. That's Lovable's sweet spot.

For everything else, Railway is your best friend.

---

## Section 6: Cost Estimate

### Option A: Minimal Setup (Both Apps)

| Service | Purpose | Monthly Cost |
|---|---|---|
| Railway Starter | Project Scraper backend (Node.js + Playwright + Redis) | $5–$20 |
| Railway Starter | Contract Analyzer backend (FastAPI + Celery + Docling) | $20–$50 |
| Supabase Free | Contract Analyzer DB + Storage | $0 |
| Vercel Free | Contract Analyzer frontend | $0 |
| Lovable Pro | Building/iterating UIs with AI prompts | $25 (build phase only) |
| Anthropic API | Claude calls for contract analysis | $5–$30 (usage-based) |
| Google Sheets API | Project Scraper output | $0 |
| **Total** | | **~$55–$125/month** |

Railway pricing breakdown:
- Base: $5/month minimum
- Usage: ~$0.000463/vCPU-minute, ~$0.000231/GB-RAM-minute
- For a typical web app with moderate usage: $10–$30/month per service

### Option B: Consolidated (Single Railway Project)

Run both apps on Railway under one project:
- Railway Pro plan: $20/month flat (includes $20 in resource credits)
- All services within credit limit if usage is moderate
- **Estimated total: $50–$80/month**

### One-time Lovable spend for UI building:
- Project Scraper UI: ~$25–$50 in credits (one-time)
- Contract Analyzer UI refresh (optional): ~$25 (one-time)
- **Total one-time: $50–$75**

---

## Section 7: Timeline

| Week | Work | Deliverable |
|---|---|---|
| **Week 1** | Deploy Contract Analyzer backend to Railway | API live at railway URL |
| **Week 1** | Deploy Contract Analyzer frontend to Vercel | Web app accessible at vercel URL |
| **Week 1** | End-to-end test (PDF upload → analysis → results) | Working Contract Analyzer web app |
| **Week 2** | Build Project Scraper Express API wrapper | Backend API with POST /crawl, GET /status |
| **Week 2** | Deploy Project Scraper backend to Railway | Scraper backend live |
| **Week 2** | Use Lovable to build Project Scraper dashboard UI | React UI generated and deployed |
| **Week 3** | Custom domains, polish, authentication (optional) | Production-ready URLs |
| **Week 3** | Test both apps with real data | Full validation |

**Realistic total: 2–3 weeks to both apps live in production.**

Contract Analyzer is closer to ready — it could be deployed in 1–2 days of focused work since the architecture is complete.

---

## Section 8: Final Recommendation

### What I recommend:

**1. Deploy Contract Analyzer first — it's nearly ready.** The Docker Compose stack is complete. The effort is configuration, not coding. Use Railway for the backend (existing Docker setup ports directly) and Vercel for the frontend. Skip Lovable entirely here — rebuilding the existing React UI in Lovable adds cost without benefit.

**2. For Project Scraper, use Lovable just for the UI.** Write the Express API wrapper yourself (1 day of work), deploy to Railway, then use Lovable's AI to quickly generate a clean dashboard UI. Export the code from Lovable to GitHub and host the frontend on Vercel. Don't use Lovable's own hosting for this — the backend lives on Railway anyway.

**3. Don't try to make either app "Lovable-native."** Lovable is an excellent rapid UI prototyping tool, but it's not designed for your use cases. Think of it as a "UI code generator" you use during the build phase, not as infrastructure.

### Platform comparison for your needs:

| Platform | Best For | Your Fit |
|---|---|---|
| **Lovable** | Building React UIs fast with AI prompts | UI generation only |
| **Railway** | Backend services, Docker, Python, Node.js | ✅ Best for both backends |
| **Render** | Production web services with Postgres | Good alternative to Railway |
| **Vercel** | React/Next.js frontend hosting | ✅ Best for frontend hosting |
| **Supabase** | Postgres DB + auth + storage + edge functions | ✅ Replace MinIO/Postgres |
| **Fly.io** | Docker apps globally distributed | Alternative to Railway |

### Risk factors to consider:

1. **Contract Analyzer OCR:** Docling is a Docker image — confirm Railway's memory limits accommodate it (it's RAM-hungry). You may need Railway's Pro plan for sufficient resources.

2. **Playwright on Railway:** Node.js + Playwright with Chromium needs a Dockerfile with the right system dependencies. Doable but requires testing.

3. **Anthropic API costs:** At scale (analyzing hundreds of contracts), Claude API costs can add up. Budget ~$0.003/1K input tokens for Claude Sonnet 3.5. A typical 10-page contract = ~5K tokens = $0.015/contract.

4. **Web scraping legality/ethics:** The Project Scraper crawls competitor sites (Rubrik, etc.). Ensure crawl delays and robots.txt respect are maintained. Some sites may block Railway IP ranges.

5. **Security:** Both apps will handle sensitive data (contracts) or proprietary research. Add authentication (Supabase Auth or Clerk) before sharing URLs externally.

---

## Appendix: Alternatives Considered

| Alternative | Why Not Primary Recommendation |
|---|---|
| **AWS Lambda** | More complex setup, cold starts hurt long-running crawls |
| **Google Cloud Run** | Good option, but Railway is simpler and cheaper at this scale |
| **DigitalOcean App Platform** | Viable, slightly less developer-friendly than Railway |
| **Heroku** | Expensive post-free-tier elimination; Railway is the modern replacement |
| **Supabase Edge Functions only** | JavaScript/TypeScript only — Python and Playwright impossible |
| **Replit** | Not production-grade; sleeps on inactivity |
| **Bolt.new** | Similar to Lovable, same frontend-only limitations |

---

*Plan prepared by Jarvis. Last updated: 2026-03-07.*
