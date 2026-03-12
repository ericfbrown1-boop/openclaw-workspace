# Contract Analyzer — Cloud Deployment Guide
**Created:** 2026-03-09 | **Author:** Jarvis | **Target Platform:** Railway.app

---

## Architecture Overview

Your ContractAnalyzer is already a well-architected system (FastAPI + React + PostgreSQL + Redis + Celery + MinIO). The local docker-compose.yml works great on your Mac/PC, but Railway requires each service to be a **separate Railway service** (not Docker Compose).

Here's how the deployed system looks:

```
┌─────────────────────────────────────────────────────────────┐
│                     RAILWAY PROJECT                          │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Frontend   │    │  FastAPI API  │    │ Celery Worker│  │
│  │ React/Nginx  │───▶│   (Python)   │───▶│  (Python)    │  │
│  │ your-app.up  │    │              │    │              │  │
│  └──────────────┘    └──────┬───────┘    └──────┬───────┘  │
│                             │                   │           │
│              ┌──────────────┴──────────────┐    │           │
│              │                             │    │           │
│  ┌───────────▼──┐    ┌──────────────┐  ┌──▼────┴───────┐  │
│  │  PostgreSQL  │    │    Redis     │  │   Docling OCR │  │
│  │  (managed)   │    │  (managed)   │  │   (service)   │  │
│  └──────────────┘    └──────────────┘  └───────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
    ┌─────────▼──┐  ┌────────▼───┐  ┌──────▼──────┐
    │ Claude API │  │ Cloudflare │  │  Custom     │
    │ (Anthropic)│  │ R2 Storage │  │  Domain     │
    └────────────┘  │ (for PDFs) │  └─────────────┘
                    └────────────┘
```

**Key difference from local:** Replace MinIO with **Cloudflare R2** (S3-compatible, free 10GB/month) and drop Ollama (use Claude API only on Railway).

---

## Prerequisites

Before you start, make sure you have:

### Accounts to Create
- [ ] **Railway.app** — https://railway.com (you already have this)
- [ ] **Cloudflare** — https://cloudflare.com (free R2 for file storage)
- [ ] **Anthropic** — https://console.anthropic.com (you already have this)
- [ ] **GitHub** — https://github.com (you already have this)

### Tools to Install
```bash
# Railway CLI
brew install railway

# Docker Desktop (already installed)
# GitHub CLI (optional but handy)
brew install gh
```

### Verify Railway CLI
```bash
railway login
# Opens browser → authenticate with GitHub
railway whoami  # Should show your account
```

### API Keys You'll Need
- `ANTHROPIC_API_KEY` — your existing Claude API key
- Cloudflare R2: Account ID, Access Key ID, Secret Access Key (created in step 3)

---

## Step 1: Dockerize (Prep Your Dockerfiles for Railway)

Your project already has Dockerfiles! But we need to make a few tweaks for Railway compatibility.

### 1a. Update the API Dockerfile

Railway injects `PORT` automatically. Your current Dockerfile hardcodes `8000`. Fix it:

**File:** `api/Dockerfile`
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies including Tesseract OCR (fallback if Docling isn't used)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Railway provides PORT env var — use it
EXPOSE ${PORT:-8000}

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]
```

### 1b. Update the Frontend Dockerfile

The frontend needs to proxy API calls to the Railway API service (not localhost):

**File:** `frontend/Dockerfile`
```dockerfile
# ── Stage 1: Build ────────────────────────────────────────────────
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

# Pass API URL at build time (Railway injects VITE_API_URL)
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

COPY . .
RUN npm run build

# ── Stage 2: Serve ────────────────────────────────────────────────
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

# Nginx config — proxy /api calls to the backend
# RAILWAY_API_URL is replaced at container startup via envsubst
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE ${PORT:-80}

CMD ["nginx", "-g", "daemon off;"]
```

**File:** `frontend/nginx.conf.template`
```nginx
server {
    listen ${PORT:-80};
    root /usr/share/nginx/html;
    index index.html;

    # Proxy API calls to Railway API service
    location /api {
        proxy_pass ${API_BACKEND_URL};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;  # Contract analysis can take a while
        client_max_body_size 50M;  # Allow large PDFs
    }

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### 1c. Create .dockerignore Files

**File:** `api/.dockerignore`
```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.env
.env.*
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/
input_pdfs/
output/
*.pdf
*.docx
*.json
!app/**/*.json
```

**File:** `frontend/.dockerignore`
```
node_modules/
dist/
.env
.env.*
*.log
```

### 1d. Create a Root .dockerignore

**File:** `.dockerignore` (at project root)
```
.git/
.github/
node_modules/
__pycache__/
*.pyc
.env
.env.*
input_pdfs/
output/
*.pdf
repomix-*.txt
```

### 1e. Test Docker Builds Locally First

```bash
cd /Users/ericbrown/ContractAnalyzer

# Build API image
docker build -t contract-api ./api

# Build Frontend image
docker build -t contract-frontend ./frontend

# Verify they work
docker run --rm -p 8000:8000 -e PORT=8000 contract-api
# In another terminal:
curl http://localhost:8000/health
```

---

## Step 2: Web UI — Your Frontend is Already Built!

You already have a React + FastAPI setup. The architecture is correct. Here's what to verify and the key upload flow:

### 2a. Verify File Upload in FastAPI (api/app/routers/upload.py)

Make sure your upload endpoint saves to **S3-compatible storage** (not local disk). After Step 3, update MinIO references to Cloudflare R2:

```python
# api/app/routers/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from app.services.storage_service import upload_to_r2
from app.tasks.contract_tasks import process_contract

router = APIRouter(prefix="/api")

@router.post("/upload")
async def upload_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload a PDF contract for analysis."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported")
    
    # Read file content
    content = await file.read()
    
    if len(content) > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(413, "File too large (max 50MB)")
    
    # Upload to Cloudflare R2
    file_key = f"contracts/{uuid4()}/{file.filename}"
    await upload_to_r2(file_key, content)
    
    # Queue for processing (Celery task)
    job = await create_processing_job(file_key, file.filename)
    background_tasks.add_task(process_contract.delay, str(job.id))
    
    return {
        "job_id": str(job.id),
        "filename": file.filename,
        "status": "queued",
        "message": "Contract uploaded and queued for analysis"
    }

@router.get("/contracts/{job_id}/status")
async def get_status(job_id: str):
    """Poll job status. Frontend polls this every 3 seconds."""
    job = await get_job(job_id)
    return {
        "job_id": job_id,
        "status": job.status,  # queued | processing | complete | failed
        "progress": job.progress,
        "result_url": f"/api/contracts/{job_id}/results" if job.status == "complete" else None
    }
```

### 2b. Add a Storage Service for Cloudflare R2

**File:** `api/app/services/storage_service.py`
```python
import boto3
from botocore.config import Config
from app.config import settings

# Cloudflare R2 is S3-compatible — use boto3 with custom endpoint
r2_client = boto3.client(
    "s3",
    endpoint_url=f"https://{settings.CF_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=settings.R2_ACCESS_KEY_ID,
    aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4"),
    region_name="auto",
)

async def upload_to_r2(key: str, content: bytes) -> str:
    """Upload file to Cloudflare R2. Returns the key."""
    r2_client.put_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=key,
        Body=content,
        ContentType="application/pdf",
    )
    return key

async def download_from_r2(key: str) -> bytes:
    """Download file from Cloudflare R2."""
    response = r2_client.get_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=key
    )
    return response["Body"].read()

def get_presigned_url(key: str, expiry_seconds: int = 3600) -> str:
    """Get a time-limited download URL."""
    return r2_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.R2_BUCKET_NAME, "Key": key},
        ExpiresIn=expiry_seconds,
    )
```

---

## Step 3: Storage — Cloudflare R2 for PDFs

Railway doesn't have persistent volumes on the Hobby plan. Use **Cloudflare R2** for PDFs (free 10GB/month, no egress fees).

### 3a. Create Cloudflare R2 Bucket

1. Go to https://dash.cloudflare.com → **R2 Object Storage**
2. Click **Create bucket** → name it `contract-analyzer`
3. Go to **Manage R2 API Tokens** → **Create API Token**
   - Permissions: **Object Read & Write**
   - TTL: No expiry
4. Save these values:
   - Account ID (in URL: `dash.cloudflare.com/<ACCOUNT_ID>/r2`)
   - Access Key ID
   - Secret Access Key

### 3b. Add R2 Config to Your Settings

**Update:** `api/app/config.py`
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Existing settings...
    DATABASE_URL: str
    REDIS_URL: str
    ANTHROPIC_API_KEY: str
    
    # Cloudflare R2 (replaces MinIO)
    CF_ACCOUNT_ID: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_BUCKET_NAME: str = "contract-analyzer"
    
    # Docling OCR service URL
    DOCLING_URL: str = "http://docling:8001"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 3c. Add boto3 to requirements.txt

```bash
# In api/requirements.txt — boto3 is already there!
# botocore is included with boto3
```

---

## Step 4: Authentication

For a personal/small-team app, the simplest approach is **HTTP Basic Auth via Nginx** (zero code changes to FastAPI):

### Option A: Simple Password Gate (Recommended for Personal Use)

Add basic auth to the frontend Nginx config:

```nginx
# frontend/nginx.conf.template — updated with auth
server {
    listen ${PORT:-80};
    root /usr/share/nginx/html;
    index index.html;
    
    # Basic auth for the entire app
    auth_basic "Contract Analyzer";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location /api {
        proxy_pass ${API_BACKEND_URL};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
        client_max_body_size 50M;
        # Pass auth header to API (optional — API can have its own auth check)
        proxy_set_header Authorization $http_authorization;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

Generate the password file:
```bash
# Install htpasswd tool
brew install httpd

# Create password file for user "eric"
htpasswd -c .htpasswd eric
# Enter password when prompted

# Base64 encode for Railway env var
cat .htpasswd | base64
# Copy the output — you'll use this as HTPASSWD_B64 env var
```

Update `frontend/Dockerfile` to inject the password file:
```dockerfile
# Add to Dockerfile before CMD:
# The HTPASSWD_B64 env var contains base64-encoded htpasswd content
RUN echo '#!/bin/sh\n\
echo "${HTPASSWD_B64}" | base64 -d > /etc/nginx/.htpasswd\n\
exec nginx -g "daemon off;"' > /docker-entrypoint-custom.sh && \
chmod +x /docker-entrypoint-custom.sh

CMD ["/docker-entrypoint-custom.sh"]
```

### Option B: FastAPI JWT Auth (Better for Multiple Users)

If you want proper login with sessions, add this to FastAPI:

```bash
# Add to api/requirements.txt
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

```python
# api/app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

router = APIRouter()
security = HTTPBasic()

# Simple hardcoded credentials (store in env vars)
USERS = {
    "eric": "your-hashed-password-here"  # Use passlib to hash
}

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify HTTP Basic Auth credentials."""
    if credentials.username not in USERS:
        raise HTTPException(401, "Invalid credentials")
    # In production, use passlib.context.verify
    is_valid = secrets.compare_digest(
        credentials.password.encode(),
        "your-password".encode()
    )
    if not is_valid:
        raise HTTPException(401, "Invalid credentials")
    return credentials.username
```

**Recommendation:** Start with Option A (Nginx basic auth). Zero code changes, instant setup.

---

## Step 5: Deploy to Railway

This is the main event. Railway doesn't support Docker Compose directly — each service gets deployed separately.

### 5a. Install Railway CLI and Login
```bash
brew install railway
railway login
```

### 5b. Create a New Railway Project
```bash
cd /Users/ericbrown/ContractAnalyzer

# Link to your Railway account
railway init
# ? Project name: ContractAnalyzer
# Creates a new project and links this directory
```

Or via dashboard: https://railway.com/new → **Empty Project**

### 5c. Add Managed Database Services

Railway provides **managed PostgreSQL and Redis** — much easier than running them yourself:

```bash
# Add PostgreSQL (Railway manages it for you)
railway add --plugin postgresql
# This creates a POSTGRES_URL env var automatically

# Add Redis
railway add --plugin redis
# This creates a REDIS_URL env var automatically
```

Via dashboard: In your Railway project → **+ New Service** → **Database** → **PostgreSQL** (then same for Redis).

### 5d. Deploy the FastAPI Backend

```bash
# From project root — deploy the api/ directory as a service
railway service create --name api
cd api

# Set all environment variables
railway variables set \
  ANTHROPIC_API_KEY="sk-ant-your-key-here" \
  CF_ACCOUNT_ID="your-cloudflare-account-id" \
  R2_ACCESS_KEY_ID="your-r2-key-id" \
  R2_SECRET_ACCESS_KEY="your-r2-secret" \
  R2_BUCKET_NAME="contract-analyzer" \
  LLM_PROVIDER="anthropic" \
  LOG_LEVEL="INFO"

# Link PostgreSQL and Redis (Railway auto-fills these from the managed plugins)
# DATABASE_URL and REDIS_URL are injected automatically

# Deploy
railway up --service api
```

### 5e. Deploy the Celery Worker

The Celery worker uses the **same Docker image** as the API, just a different start command:

```bash
# Create a new service for the worker
railway service create --name worker

# Set same env vars as API (Railway has shared env per project)
# Override just the start command:
railway variables set --service worker \
  START_COMMAND="celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2 -Q contracts"
```

**Important:** In your `api/Dockerfile`, make the command configurable:
```dockerfile
# Replace the CMD line with:
CMD ["sh", "-c", "${START_COMMAND:-uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2}"]
```

### 5f. Deploy Docling OCR Service

Docling runs as a separate service using its published Docker image:

```bash
railway service create --name docling
railway variables set --service docling \
  DOCLING_SERVE_PORT=8001

# Deploy from Docker image (no local build needed)
railway service --service docling connect
# Set source: Docker image → docling-project/docling-serve:latest
```

Via dashboard: **+ New Service** → **Docker Image** → `docling-project/docling-serve:latest`

### 5g. Deploy the React Frontend

```bash
cd /Users/ericbrown/ContractAnalyzer/frontend

railway service create --name frontend

# Get the API service URL from Railway dashboard (looks like: contract-api.up.railway.app)
railway variables set --service frontend \
  API_BACKEND_URL="https://your-api-service.up.railway.app" \
  VITE_API_URL="https://your-api-service.up.railway.app" \
  HTPASSWD_B64="your-base64-htpasswd-here"

railway up --service frontend
```

### 5h. Create the railway.toml Config File

This file tells Railway how to build each service:

**File:** `railway.toml` (at project root)
```toml
[build]
builder = "DOCKERFILE"

[[services]]
name = "api"
dockerfilePath = "api/Dockerfile"
[services.deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2"
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[[services]]
name = "worker"
dockerfilePath = "api/Dockerfile"
[services.deploy]
startCommand = "celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2 -Q contracts"
restartPolicyType = "ALWAYS"

[[services]]
name = "frontend"
dockerfilePath = "frontend/Dockerfile"
[services.deploy]
healthcheckPath = "/"
healthcheckTimeout = 10
```

### 5i. Verify the Deployment

```bash
# Check all services are running
railway status

# View logs
railway logs --service api
railway logs --service worker
railway logs --service frontend

# Test the API health endpoint
curl https://your-api-service.up.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0"
}
```

### 5j. Run Database Migrations

After first deploy, run Alembic migrations:
```bash
# Open a shell in the Railway API service
railway shell --service api

# Inside the container:
alembic upgrade head
exit
```

Or add this to the API startup in `api/app/main.py`:
```python
from alembic.config import Config
from alembic import command

@app.on_event("startup")
async def startup():
    """Run migrations on startup (safe — Alembic is idempotent)."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
```

---

## Step 6: Custom Domain (Optional)

Railway gives you a free `.up.railway.app` subdomain. To use your own domain:

### 6a. Add Domain in Railway Dashboard
1. Click your **frontend** service → **Settings** → **Domains**
2. Click **+ Custom Domain**
3. Enter: `contracts.yourdomain.com`
4. Railway shows you a CNAME record to add

### 6b. Configure DNS (if domain is on Cloudflare)
```
Type: CNAME
Name: contracts
Target: your-frontend.up.railway.app
Proxy: ON (orange cloud)
```

### 6c. Railway Auto-Provisions SSL
Railway uses Let's Encrypt automatically — HTTPS is included, no setup needed.

---

## Step 7: CI/CD — Auto-Deploy from GitHub

### 7a. Connect GitHub Repository

In Railway dashboard:
1. Select your **api** service → **Settings** → **Source**
2. Click **Connect GitHub Repo**
3. Select `ericfbrown1-boop/ContractAnalyzer`
4. Set **Root Directory** to `api/`
5. Set **Branch** to `main`

Repeat for the **frontend** service (Root Directory = `frontend/`).

### 7b. Deploy on Push

Now every `git push` to `main` triggers an automatic deploy:
```bash
# Make a change
git add .
git commit -m "Update contract extraction logic"
git push origin main
# Railway automatically builds and deploys!
```

### 7c. Set Up a Staging Branch (Optional but Smart)

```bash
# Create a staging environment in Railway
railway environment create staging

# Deploy staging on push to 'dev' branch
# (Configure in Railway dashboard → Environment → Triggers)
```

### 7d. Add GitHub Actions for Pre-Deploy Tests

**File:** `.github/workflows/deploy.yml`
```yaml
name: Test & Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          cd api
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx
      
      - name: Run tests
        run: |
          cd api
          pytest tests/ -v
        env:
          DATABASE_URL: sqlite+aiosqlite:///./test.db
          REDIS_URL: redis://localhost:6379
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      
  # Railway auto-deploys on push to main — no explicit deploy step needed
  # Just ensure tests pass before Railway picks up the push
```

---

## Cost Estimate

### Railway Pricing (as of March 2026)

| Plan | Monthly Cost | Included Credits | Best For |
|------|-------------|------------------|---------|
| Hobby | $5/month | $5 usage credit | Personal use |
| Pro | $20/month | $20 usage credit | Small team |
| Enterprise | Custom | Custom | Large scale |

### Resource Usage Estimate for ContractAnalyzer

**Services running:**
| Service | RAM | CPU | Estimated Cost/Month |
|---------|-----|-----|---------------------|
| FastAPI API | 512MB | 0.5 vCPU | ~$3 |
| Celery Worker | 512MB | 0.5 vCPU | ~$3 |
| React Frontend | 128MB | 0.1 vCPU | ~$1 |
| Docling OCR | 1GB | 1 vCPU | ~$6 |
| PostgreSQL (managed) | 512MB | — | ~$5 |
| Redis (managed) | 256MB | — | ~$3 |
| **Total** | | | **~$21/month** |

**Storage (Cloudflare R2):**
| Usage | Cost |
|-------|------|
| First 10GB stored | FREE |
| 10GB–100GB | $0.015/GB/month |
| Bandwidth | FREE (no egress fees!) |

**Claude API (Anthropic):**
| Volume | Estimated Cost |
|--------|---------------|
| 10 contracts/day | ~$5/month |
| 50 contracts/day | ~$25/month |
| 200 contracts/day | ~$100/month |

### Total Monthly Cost by Usage Level

| Usage Level | Railway | Cloudflare R2 | Claude API | **Total** |
|-------------|---------|---------------|------------|-----------|
| Personal (10 contracts/day) | $20 | Free | $5 | **~$25/month** |
| Small Team (50/day) | $20 | Free | $25 | **~$45/month** |
| Medium (200/day) | $40 | $1 | $100 | **~$141/month** |

### Alternative Platforms Comparison

| Platform | Monthly Cost | Best For | Tradeoffs |
|----------|-------------|---------|-----------|
| **Railway** ⭐ | ~$21 | Developer UX, fast deploy | Less config than AWS |
| **Render** | ~$25 | Similar to Railway | Slightly slower deploys |
| **Fly.io** | ~$18 | Edge deployment, global | More complex setup |
| **AWS (ECS)** | ~$35–80 | Enterprise scale | Complex, steep learning curve |
| **GCP Cloud Run** | ~$15–30 | Serverless, per-request | Cold starts on low traffic |

**Verdict:** Railway is the right choice for this use case. Best balance of simplicity, cost, and features for a personal/small-team app.

---

## Monitoring & Logging

### Built-in Railway Monitoring

Railway dashboard provides:
- Real-time CPU/RAM/network graphs
- Log streaming (`railway logs --service api`)
- Deployment history

### 10a. Add Structured Logging to FastAPI

```python
# api/app/main.py — add logging setup
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "service": "api", "message": "%(message)s"}',
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Log every contract upload
@router.post("/upload")
async def upload_contract(file: UploadFile = File(...)):
    logger.info(f"Contract upload started: {file.filename}, size: {file.size}")
    # ... processing ...
    logger.info(f"Contract upload complete: job_id={job.id}")
```

### 10b. Add Sentry for Error Tracking (Free Tier)

```bash
# api/requirements.txt
sentry-sdk[fastapi]==2.19.0
```

```python
# api/app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,  # Get free DSN at sentry.io
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,  # 10% of requests for performance monitoring
    environment="production",
)
```

Set the env var:
```bash
railway variables set SENTRY_DSN="https://your-key@sentry.io/your-project"
```

Sentry free tier: 5,000 errors/month — more than enough for personal use.

### 10c. Add a Simple Health Dashboard

```python
# api/app/routers/health.py
from fastapi import APIRouter
from app.database import get_db
from app.config import settings
import redis.asyncio as aioredis
import time

router = APIRouter()

@router.get("/health")
async def health_check():
    """Comprehensive health check — called by Railway and monitoring."""
    start = time.time()
    
    checks = {}
    
    # Database check
    try:
        async with get_db() as db:
            await db.execute("SELECT 1")
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
    
    # Redis check
    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"
    
    # R2 Storage check
    try:
        r2_client.head_bucket(Bucket=settings.R2_BUCKET_NAME)
        checks["storage"] = "healthy"
    except Exception as e:
        checks["storage"] = f"unhealthy: {str(e)}"
    
    overall = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"
    
    return {
        "status": overall,
        "checks": checks,
        "response_time_ms": round((time.time() - start) * 1000, 2),
        "version": "1.0.0",
    }

@router.get("/metrics")
async def get_metrics():
    """Basic usage metrics."""
    async with get_db() as db:
        total = await db.execute("SELECT COUNT(*) FROM contracts")
        completed = await db.execute("SELECT COUNT(*) FROM contracts WHERE status='complete'")
        today = await db.execute("SELECT COUNT(*) FROM contracts WHERE created_at > NOW() - INTERVAL '24 hours'")
    
    return {
        "total_contracts": total.scalar(),
        "completed": completed.scalar(),
        "analyzed_today": today.scalar(),
    }
```

### 10d. UptimeRobot (Free Uptime Monitoring)

1. Go to https://uptimerobot.com → Create free account
2. **Add Monitor** → HTTP(s)
3. URL: `https://your-api.up.railway.app/health`
4. Check interval: 5 minutes
5. Alert: Email if down

Free tier: 50 monitors, 5-minute checks — perfect for personal use.

---

## Backup & Recovery

### 11a. Automated PostgreSQL Backups

Railway Pro plan includes daily automated backups. On Hobby plan, add a scheduled backup job:

**File:** `scripts/backup_db.py`
```python
#!/usr/bin/env python3
"""Daily database backup to Cloudflare R2."""
import subprocess
import boto3
from datetime import datetime
import os

def backup_database():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"/tmp/backup_{timestamp}.sql.gz"
    
    # Dump PostgreSQL
    db_url = os.environ["DATABASE_URL"]
    result = subprocess.run(
        f"pg_dump {db_url} | gzip > {backup_file}",
        shell=True, capture_output=True
    )
    
    if result.returncode != 0:
        print(f"Backup failed: {result.stderr}")
        return False
    
    # Upload to R2 (backups bucket)
    r2 = boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ['CF_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
    )
    
    backup_key = f"backups/db/{timestamp}.sql.gz"
    r2.upload_file(backup_file, "contract-analyzer-backups", backup_key)
    
    print(f"✅ Backup complete: {backup_key}")
    return True

if __name__ == "__main__":
    backup_database()
```

Add a Railway cron job service:
```bash
# In Railway project — add a Cron service
# Command: python scripts/backup_db.py
# Schedule: 0 3 * * *  (3 AM daily)
```

### 11b. Contract PDF Backup Policy

Cloudflare R2 has **99.999999999% (11 9s) durability** — your PDFs are safe. But for extra protection:

```python
# scripts/backup_contracts.py — Monthly archive to a second R2 bucket
def archive_old_contracts(older_than_days: int = 90):
    """Move contracts older than 90 days to archive bucket."""
    # List contracts older than threshold
    # Copy to archive bucket (cheaper storage tier)
    # Update database record with new location
    pass
```

### 11c. Restore Procedure

```bash
# Restore database from backup
# 1. Download backup from R2
aws s3 cp s3://contract-analyzer-backups/backups/db/20260309_030000.sql.gz /tmp/ \
  --endpoint-url https://your-account.r2.cloudflarestorage.com

# 2. Decompress and restore
gunzip -c /tmp/20260309_030000.sql.gz | psql $DATABASE_URL

# 3. Verify
railway shell --service api
python -c "from app.database import engine; print('DB OK')"
```

---

## Quick Reference: All Environment Variables

Create this file locally (never commit it!):

**File:** `.env.production` (gitignored)
```bash
# Database (auto-set by Railway managed PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
SYNC_DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Redis (auto-set by Railway managed Redis)
REDIS_URL=redis://default:password@host:6379

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-5

# Cloudflare R2 Storage
CF_ACCOUNT_ID=your-32-char-account-id
R2_ACCESS_KEY_ID=your-r2-key-id
R2_SECRET_ACCESS_KEY=your-r2-secret
R2_BUCKET_NAME=contract-analyzer

# Docling OCR (internal Railway service URL)
DOCLING_URL=http://docling.railway.internal:8001

# Auth (for Nginx basic auth on frontend)
HTPASSWD_B64=ZXJpYzokYXByMSR...base64-encoded-htpasswd

# Monitoring
SENTRY_DSN=https://your-key@o123456.ingest.sentry.io/123456

# App settings
LOG_LEVEL=INFO
ENVIRONMENT=production
MAX_UPLOAD_SIZE_MB=50
```

Set them all at once in Railway:
```bash
railway variables set --service api < .env.production
```

---

## Deployment Checklist

**One-time setup:**
- [ ] Create Cloudflare account + R2 bucket
- [ ] Generate R2 API tokens
- [ ] Create Railway project
- [ ] Add PostgreSQL plugin
- [ ] Add Redis plugin
- [ ] Connect GitHub repo to Railway services

**First deploy:**
- [ ] Build Docker images locally to verify (`docker build`)
- [ ] Set all environment variables in Railway
- [ ] Deploy API service
- [ ] Deploy Worker service
- [ ] Deploy Docling service
- [ ] Deploy Frontend service
- [ ] Run `alembic upgrade head`
- [ ] Test `/health` endpoint
- [ ] Upload a test PDF via the frontend

**Ongoing:**
- [ ] UptimeRobot monitoring configured
- [ ] Sentry error tracking configured
- [ ] Daily backup job running
- [ ] Automatic deploys on `git push` working

---

## Troubleshooting Common Issues

### "Container exits immediately"
```bash
railway logs --service api --tail 50
# Look for startup errors — usually missing env vars
```

### "Database connection refused"
```bash
# Verify DATABASE_URL format for asyncpg:
# postgresql+asyncpg://user:pass@host:5432/db  ← async
# postgresql://user:pass@host:5432/db           ← sync (for Celery/Alembic)
```

### "File upload timeout"
- Increase Nginx `proxy_read_timeout` to `600s` for large contracts
- Check that Celery worker is running (`railway logs --service worker`)

### "OCR not working"
```bash
# Verify Docling service is healthy
curl https://your-docling.up.railway.app/health
# If down, restart: railway service restart --service docling
```

### "Claude API errors"
- Check `ANTHROPIC_API_KEY` is set correctly
- Monitor usage at https://console.anthropic.com/usage
- Check rate limits (Claude Sonnet: 4000 requests/minute on paid plan)

---

*Generated by Jarvis — Eric's AI assistant | Contract Analyzer Deployment Guide v1.0*
*Last updated: 2026-03-09*
