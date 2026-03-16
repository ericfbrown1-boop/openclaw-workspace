# Railway Project Template — Based on ContractAnalyzer

This is the reference architecture for all new Python/FastAPI projects.
Derived from Eric's production ContractAnalyzer deployment on Railway.

---

## Project Structure

```
ProjectName/
├── api/                          # Backend (FastAPI) — this is the Railway service
│   ├── Dockerfile                # Railway builds from here
│   ├── requirements.txt          # Python dependencies
│   └── app/
│       ├── __init__.py
│       ├── main.py               # FastAPI app entry point + lifespan + routers
│       ├── config.py             # pydantic-settings: ALL config from env vars
│       ├── database.py           # SQLAlchemy async engine + session + init_db()
│       ├── auth.py               # JWT auth (PyJWT + OAuth2PasswordBearer)
│       ├── models/
│       │   ├── __init__.py
│       │   ├── <domain>.py       # SQLAlchemy ORM models (UUID PKs, soft delete)
│       │   └── schemas.py        # Pydantic v2 request/response schemas
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── auth.py           # POST /api/auth/login → JWT
│       │   ├── <resource>.py     # CRUD + business endpoints
│       │   └── ...
│       ├── services/
│       │   ├── __init__.py
│       │   ├── llm_service.py    # LLM adapter pattern (Anthropic + Ollama)
│       │   ├── <domain>_service.py
│       │   └── ...
│       ├── tasks/                # Celery async tasks (optional)
│       │   ├── __init__.py
│       │   ├── celery_app.py
│       │   └── <domain>_tasks.py
│       └── static/               # Frontend SPA served from API (optional)
│           └── index.html
├── frontend/                     # React/Vite frontend (optional, can be separate)
│   ├── Dockerfile
│   ├── package.json
│   └── src/
├── docker-compose.yml            # Local dev: API + DB + Redis + MinIO
├── railway.json                  # Railway build/deploy config
├── .env.example                  # Template env vars (committed)
├── .env                          # Actual secrets (NEVER committed)
├── .gitignore
├── Procfile                      # Railway process types
└── README.md
```

---

## Dockerfile (api/Dockerfile)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# System dependencies — adjust per project
# Common: curl, build-essential, libpq-dev (PostgreSQL)
# OCR: tesseract-ocr, poppler-utils, libmagic1
# ML: add torch, transformers deps as needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies (cached layer — changes less often than code)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Non-root user (security)
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Shell form REQUIRED for $PORT expansion on Railway
CMD ["/bin/sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]
```

**Key rules:**
- Shell form CMD with `${PORT:-8000}` — Railway injects `$PORT` dynamically
- Non-root user always
- `--no-cache-dir` on pip to keep image small
- `requirements.txt` copied before code for Docker layer caching

---

## railway.json

```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "api/Dockerfile",
    "watchPatterns": [
      "api/**"
    ]
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2",
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 5,
    "numReplicas": 1
  }
}
```

**Notes:**
- `startCommand` in railway.json overrides the Dockerfile CMD
- `$PORT` (no braces) works in railway.json because Railway substitutes it before exec
- `healthcheckPath` must match the actual health endpoint in main.py
- Add extra `watchPatterns` if you have data/config dirs (e.g., `"taxonomy/**"`)

---

## Config Pattern (config.py)

Use `pydantic-settings` for ALL configuration. Zero hardcoded values.

```python
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ── Application ───────────────────────────────────────
    APP_NAME: str = "MyApp"
    APP_ENV: str = "development"         # development | staging | production
    LOG_LEVEL: str = "info"
    CORS_ORIGINS: str = "http://localhost:3000"

    # ── Database ──────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@db:5432/mydb"
    SYNC_DATABASE_URL: Optional[str] = None   # For Celery workers

    @property
    def sync_db_url(self) -> str:
        if self.SYNC_DATABASE_URL:
            return self.SYNC_DATABASE_URL
        return self.DATABASE_URL.replace("+asyncpg", "").replace("asyncpg://", "://")

    # ── Redis ─────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"

    # ── Object Storage (MinIO/S3) ─────────────────────────
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "uploads"
    MINIO_SECURE: bool = False

    # ── LLM Provider ─────────────────────────────────────
    LLM_PROVIDER: str = "anthropic"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"

    # ── Authentication ──────────────────────────────────────
    AUTH_USERNAME: str = "admin"
    AUTH_PASSWORD: str = "changeme"
    AUTH_SECRET_KEY: str = "change-this-in-production"
    AUTH_TOKEN_EXPIRE_HOURS: int = 24

    # ── Email (SMTP) — optional ────────────────────────────
    SMTP_HOST: str = ""                  # Leave empty to disable
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: bool = True

    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()
```

**Pattern: every setting has a default, every setting comes from env vars, `.env` for local dev only.**

---

## Database Pattern (database.py)

```python
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker as sync_sessionmaker
from sqlalchemy import create_engine
from app.config import settings

# Async engine (FastAPI)
async_engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_size=5, max_overflow=10)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

# Sync engine (Celery workers)
sync_engine = create_engine(settings.sync_db_url, echo=False, pool_size=5, max_overflow=10)
SyncSessionLocal = sync_sessionmaker(bind=sync_engine)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    # CRITICAL: Split pgvector extension + create_all into separate transactions
    # to avoid PostgreSQL transaction poisoning (see SKILL.md Section 4)
    async with async_engine.begin() as conn:
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except Exception:
            pass
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

---

## Main App Pattern (main.py)

```python
import logging, os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.routers import auth, <resources>

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s (%s)", settings.APP_NAME, settings.APP_ENV)
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down %s", settings.APP_NAME)

app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All API routes under /api prefix
app.include_router(auth.router, prefix="/api")
# app.include_router(<resource>.router, prefix="/api")

@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}
```

**Health endpoint is mandatory** — Railway uses it for healthchecks.

---

## Auth Pattern (auth.py + routers/auth.py)

```python
# auth.py — JWT utilities
import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def create_access_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=settings.AUTH_TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": username, "exp": expire}, settings.AUTH_SECRET_KEY, algorithm="HS256")

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, settings.AUTH_SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

```python
# routers/auth.py — Login endpoint
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import create_access_token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != settings.AUTH_USERNAME or form_data.password != settings.AUTH_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": create_access_token(form_data.username), "token_type": "bearer"}
```

---

## ORM Model Pattern

```python
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class MyModel(Base):
    __tablename__ = "my_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(512), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="pending", index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)  # Soft delete
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    children = relationship("ChildModel", back_populates="parent", cascade="all, delete-orphan")
```

**Conventions:**
- UUID primary keys everywhere
- Soft delete (`is_deleted`) — never hard delete user data
- `created_at` + `updated_at` on every table
- Status columns with index for filtering

---

## Pydantic Schema Pattern

```python
from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class MyModelSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Enables ORM mode

    id: UUID
    name: str
    status: str
    created_at: datetime

class MyModelDetail(MyModelSummary):
    # Extended fields for detail view
    children: List[ChildOut] = []

class PaginatedResponse(BaseModel):
    items: List[MyModelSummary]
    total: int
    page: int
    page_size: int
    pages: int
```

---

## LLM Service Pattern

Adapter pattern for swappable LLM providers:

```python
from abc import ABC, abstractmethod
from typing import Tuple
import anthropic, httpx
from app.config import settings

class LLMAdapter(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "") -> Tuple[str, int]:
        """Returns (generated_text, tokens_used)"""
        ...

class AnthropicAdapter(LLMAdapter):
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL

    def generate(self, prompt: str, system_prompt: str = "") -> Tuple[str, int]:
        kwargs = {"model": self.model, "max_tokens": 8192,
                  "messages": [{"role": "user", "content": prompt}]}
        if system_prompt:
            kwargs["system"] = system_prompt
        msg = self.client.messages.create(**kwargs)
        return msg.content[0].text, msg.usage.input_tokens + msg.usage.output_tokens

class OllamaAdapter(LLMAdapter):
    # Local fallback — same interface
    ...

def get_llm_adapter() -> LLMAdapter:
    provider = settings.LLM_PROVIDER.lower()
    if provider == "anthropic":
        return AnthropicAdapter()
    elif provider == "ollama":
        return OllamaAdapter()
    raise ValueError(f"Unknown LLM provider: {provider}")
```

---

## Celery Task Pattern (optional, for async processing)

```python
# tasks/celery_app.py
from celery import Celery
from app.config import settings

celery_app = Celery(
    "myapp",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.my_tasks"],
)
celery_app.conf.update(
    result_expires=86400,
    task_soft_time_limit=600,
    task_time_limit=900,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_default_queue="default",
)
```

```python
# tasks/my_tasks.py — Use SYNC database session in Celery workers
from app.database import SyncSessionLocal
from app.tasks.celery_app import celery_app

@celery_app.task(bind=True, name="app.tasks.my_tasks.process_item")
def process_item(self, item_id: str):
    db = SyncSessionLocal()
    try:
        # ... do work with sync db session ...
        db.commit()
    except Exception as e:
        db.rollback()
        # Use fresh session for error marking (original may be corrupted)
        err_db = SyncSessionLocal()
        try:
            # Mark item as failed
            err_db.commit()
        finally:
            err_db.close()
        return {"error": str(e)}
    finally:
        db.close()
```

**Key: Celery workers use SYNC sessions, not async.**

---

## Railway Variables (Variables Tab)

These must be set in Railway → Service → Variables for every project:

### Required (every project)

| Variable | Example | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Railway Postgres provides this; change prefix to `+asyncpg` |
| `PORT` | `8000` | Belt-and-suspenders (Railway also injects dynamically) |
| `APP_ENV` | `production` | Controls logging, debug mode, etc. |
| `AUTH_USERNAME` | `<strong password>` | Override defaults for production |
| `AUTH_PASSWORD` | `<strong password>` | Override defaults for production |
| `AUTH_SECRET_KEY` | `<random 32+ chars>` | JWT signing — must be unique per deployment |

### Common (most projects)

| Variable | Example | Notes |
|----------|---------|-------|
| `REDIS_URL` | `redis://...` | Railway Redis service provides this |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | If using Claude |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6` | Model selection |
| `LLM_PROVIDER` | `anthropic` | Switch between providers |
| `CORS_ORIGINS` | `https://myapp.up.railway.app` | Production CORS |

### Object Storage (if using MinIO/S3)

| Variable | Example | Notes |
|----------|---------|-------|
| `MINIO_ENDPOINT` | `minio-prod.railway.internal:9000` | Internal Railway networking |
| `MINIO_ACCESS_KEY` | `...` | |
| `MINIO_SECRET_KEY` | `...` | |
| `MINIO_BUCKET` | `uploads` | |
| `MINIO_SECURE` | `false` | `true` if using S3 |

### Email (if sending reports/notifications)

| Variable | Example | Notes |
|----------|---------|-------|
| `SMTP_HOST` | `smtp.gmail.com` | Leave empty to disable |
| `SMTP_PORT` | `587` | |
| `SMTP_USERNAME` | `...` | |
| `SMTP_PASSWORD` | `...` | App password, not real password |
| `SMTP_FROM_EMAIL` | `reports@myapp.com` | |

---

## docker-compose.yml (Local Dev)

```yaml
version: '3.8'

services:
  api:
    build: ./api
    ports:
      - "8000:8000"
    env_file: .env
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER:-app_user}:${POSTGRES_PASSWORD:-app_pass}@db:5432/${POSTGRES_DB:-app_db}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: pgvector/pgvector:pg16
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=${POSTGRES_USER:-app_user}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-app_pass}
      - POSTGRES_DB=${POSTGRES_DB:-app_db}
    volumes:
      - pg_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-app_user}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  pg_data:
  redis_data:
```

---

## .env.example

```bash
# ── PostgreSQL ────────────────────────────────────────────
POSTGRES_USER=app_user
POSTGRES_PASSWORD=app_pass
POSTGRES_DB=app_db

# ── LLM ───────────────────────────────────────────────────
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-6

# ── Authentication ────────────────────────────────────────
AUTH_USERNAME=admin
AUTH_PASSWORD=changeme
AUTH_SECRET_KEY=change-this-to-a-random-string
AUTH_TOKEN_EXPIRE_HOURS=24

# ── Application ───────────────────────────────────────────
APP_NAME=MyApp
APP_ENV=development
LOG_LEVEL=info
CORS_ORIGINS=http://localhost:3000
```

---

## .gitignore

```gitignore
# Secrets
.env

# Python
__pycache__/
*.pyc
venv/
.venv/

# Node
node_modules/
dist/
.vite/

# OS
.DS_Store
*.swp

# Data
*.pdf
*.docx
output/
```

---

## Procfile

```
web: cd api && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2
worker: cd api && celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2 -Q default
```

---

## Core Dependencies (requirements.txt)

```
# Web framework
fastapi==0.115.6
uvicorn[standard]==0.34.0

# Database
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
psycopg2-binary==2.9.10
pgvector==0.3.6
alembic==1.14.1

# Task queue (optional)
celery[redis]==5.4.0
redis==5.2.1

# LLM
anthropic==0.42.0

# Auth
PyJWT==2.9.0

# Validation & serialization
pydantic==2.10.4
pydantic-settings==2.7.1

# HTTP client
httpx==0.28.1

# File handling
python-multipart==0.0.20
boto3==1.36.4

# Utilities
python-dateutil==2.9.0
```

---

## Deployment Checklist

Before pushing to Railway:

- [ ] `railway.json` has correct `dockerfilePath` and `healthcheckPath`
- [ ] Dockerfile CMD uses shell form with `${PORT:-8000}`
- [ ] `/api/health` endpoint exists and returns `{"status": "ok"}`
- [ ] All secrets in Railway Variables tab (not in code or railway.json)
- [ ] `.env` is in `.gitignore`
- [ ] `DATABASE_URL` uses `postgresql+asyncpg://` prefix
- [ ] `AUTH_SECRET_KEY` is a random 32+ char string (not default)
- [ ] `AUTH_PASSWORD` is changed from default
- [ ] Non-root user in Dockerfile
- [ ] CORS configured for production domain

After deploying:

- [ ] Health endpoint returns 200: `curl https://app.up.railway.app/api/health`
- [ ] Deploy logs show "Application startup complete"
- [ ] Auth works: can log in and get JWT
- [ ] No `.env` in git history: `git log --all --oneline -- .env`
