---
name: railway-deployment
description: >
  Deploy, debug, and fix Python/FastAPI applications on Railway. Use this skill
  whenever the user is deploying to Railway, getting healthcheck failures, build
  errors, container startup crashes, 502 errors, port binding issues, database
  connection failures at startup, or environment variable problems on Railway.
  Also trigger when the user mentions "Railway Agent" causing problems, broken
  Dockerfiles, uvicorn startup errors, SQLAlchemy/asyncpg errors on deploy, or
  pgvector extension failures. Covers the full deployment lifecycle: Dockerfile
  authoring, GitHub push workflow, Railway variable configuration, and runtime
  log diagnosis. Always read deploy logs AND runtime logs separately — they are
  different tabs in Railway and cover different failure modes.
---

# Railway Deployment Skill

## Philosophy: Build Logs vs Runtime Logs Are Different Problems

Railway has two completely separate log streams. Most debugging mistakes happen
because the wrong log is being read.

- **Build Logs** — Docker image construction. Failures here mean the image
  never built. Fix: Dockerfile syntax, missing packages, pip errors.
- **Deploy/Runtime Logs** — What happens after the container starts. Failures
  here mean the image built fine but the app crashed or didn't respond.
  Fix: wrong CMD, bad env vars, app startup errors.

**Always check Runtime Logs first for 502 / healthcheck failures.** Build
success does not mean deploy success.

---

## Step 0: Triage — What Category Is This?

| Symptom | Category | Jump to |
|---------|----------|---------|
| Healthcheck failed, build succeeded | Runtime startup crash | Section 1 |
| `Invalid value for '--port'` | Wrong CMD / PORT variable | Section 2 |
| `Could not import module "X"` | Wrong uvicorn module path | Section 3 |
| `InFailedSQLTransactionError` at startup | DB transaction poisoning | Section 4 |
| `Application failed to respond` 502 | Port mismatch or crash | Section 5 |
| Missing env vars / auth not working | Railway Variables tab | Section 6 |
| Railway Agent breaking things | Agent interference | Section 7 |
| Windows PowerShell CMD errors | Running Dockerfile commands in terminal | Section 8 |

---

## Critical Rule: Never Use the Railway Agent

The Railway Agent (chat panel on the right side of the Railway UI) actively
interferes with deployments. It creates malformed `railway.json` files, triggers
bad redeploys, and overwrites working configurations. **Close it and ignore it
entirely.** All configuration should be done via the Variables tab and
Dockerfile in GitHub.

---

## Section 1: Healthcheck Failed After Successful Build

### What it looks like
```
Build time: 95.73 seconds
==================== Starting Healthcheck ====================
Path: /api/health
Retry window: 30s
Attempt #1 failed with service unavailable.
1/1 replicas never became healthy!
Healthcheck failed!
```

### Diagnosis
The build succeeded but the container is crashing at runtime. Switch to the
**Deploy Logs** tab (not Build Logs) to see the actual error.

### Common causes (in order of likelihood)
1. Missing `CMD` in Dockerfile — container has nothing to run
2. Wrong PORT (uvicorn not listening on Railway's injected port)
3. Wrong module path in uvicorn command
4. App crash on startup (database connection, missing env var)

---

## Section 2: PORT Variable Problems

### Symptom
```
Error: Invalid value for '--port': '$PORT' is not a valid integer.
Error: Invalid value for '--port': '--workers' is not a valid integer.
```

### Root Cause
Two distinct bugs with the same symptom:

**Bug A — Argument order wrong:** `--port` has no value immediately after it,
so uvicorn grabs the next token (`--workers`) as the port number.
```dockerfile
# WRONG
CMD ["uvicorn", "app.main:app", "--port", "--workers", "4"]
#                                         ^^^^^^^^^^^ grabbed as port value
```

**Bug B — `$PORT` not expanding:** JSON array `CMD` does not expand environment
variables. Railway injects `$PORT` dynamically; array form passes it as a
literal string `"$PORT"`.
```dockerfile
# WRONG — $PORT never expands in array form
CMD ["uvicorn", "app.main:app", "--port", "$PORT"]
```

### Fix
Use shell form with `/bin/sh -c` to force variable expansion, with a fallback:
```dockerfile
CMD ["/bin/sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4"]
```

`${PORT:-8000}` means: use Railway's `$PORT` if set, otherwise default to 8000.
This works both on Railway and locally.

### Also add PORT to Railway Variables tab
Even with shell form, add `PORT = 8000` in Railway → ContractAnalyzer →
Variables as a belt-and-suspenders measure.

---

## Section 3: Wrong Uvicorn Module Path

### Symptom
```
ERROR: Error loading ASGI app. Could not import module "main".
```

### Root Cause
The module path in the `CMD` doesn't match the actual file structure inside
the container.

### Diagnosis
Check the actual directory structure of the project:
```powershell
dir C:\path\to\project /s /b | findstr ".py"
```

Map the file path to the uvicorn module string:

| File location in repo | Dockerfile COPY | Module path |
|----------------------|-----------------|-------------|
| `api/main.py` | `COPY api/ .` | `main:app` |
| `api/app/main.py` | `COPY api/ .` | `app.main:app` |
| `src/main.py` | `COPY src/ .` | `main:app` |

**Key rule:** The Dockerfile `COPY api/ .` copies the *contents* of `api/`
to `/app`. So `api/app/main.py` becomes `/app/app/main.py` inside the
container, which is module `app.main`.

### Fix
```dockerfile
# If your file is at api/app/main.py:
CMD ["/bin/sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4"]
```

---

## Section 4: Database Transaction Poisoning at Startup

### Symptom
```
sqlalchemy.dialects.postgresql.asyncpg.AsyncAdapt_asyncpg_dbapi.Error:
<class 'asyncpg.exceptions.InFailedSQLTransactionError'>:
current transaction is aborted, commands ignored until end of transaction block
```

Appearing at: `await conn.run_sync(Base.metadata.create_all)`

### Root Cause
A `CREATE EXTENSION IF NOT EXISTS vector` call silently raises an exception
(e.g., extension already exists, or permission denied) inside the same
transaction as `create_all`. PostgreSQL marks the entire transaction as aborted
after any error, so every subsequent query in that transaction fails — including
`create_all`.

The `except Exception: pass` pattern suppresses the Python error but does NOT
roll back or close the PostgreSQL transaction.

### Fix
Split `CREATE EXTENSION` and `create_all` into two completely separate
`async_engine.begin()` context managers (separate transactions):

```python
async def init_db():
    """Create all tables and enable pgvector extension."""
    # Transaction 1: extension (failure here won't affect table creation)
    async with async_engine.begin() as conn:
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except Exception:
            pass  # Extension already exists — safe to ignore

    # Transaction 2: table creation (clean transaction, no poison)
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

### Why the naive fix doesn't work
Using a single `async_engine.begin()` block with try/except around the
extension call does NOT fix this. The transaction is still aborted at the
PostgreSQL level even though Python swallowed the exception. The fix MUST
use two separate `begin()` calls.

---

## Section 5: 502 Application Failed to Respond

### Symptom
```json
{"status":"error","code":502,"message":"Application failed to respond"}
```

### This is Railway's proxy error, not your app's error
502 means Railway's load balancer successfully reached your container but got
no HTTP response. The container is running but not serving traffic.

### Diagnosis sequence
1. Check Deploy Logs — is uvicorn actually starting?
2. Check if `Application startup complete.` appears in logs
3. If uvicorn starts but 502 persists, check the port Railway is probing vs
   what uvicorn is binding to
4. Check Railway Variables tab — is `PORT` set?

### Healthy startup looks like
```
INFO: Started parent process [2]
INFO: Started server process [4]
INFO: Waiting for application startup.
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

If you see workers starting and then dying repeatedly, the app is crashing
during the lifespan startup event (usually database initialization).

---

## Section 6: Environment Variables and Authentication

### Railway does NOT read your local .env file
Variables must be set explicitly in Railway → Service → Variables tab.
The `.env` file is only for local development.

### Required variables for a typical FastAPI app on Railway

| Variable | Notes |
|----------|-------|
| `DATABASE_URL` | Must use `postgresql+asyncpg://` prefix for async SQLAlchemy |
| `PORT` | Set to `8000` as fallback |
| `APP_ENV` | Set to `production` |
| `AUTH_USERNAME` | If using hardcoded auth |
| `AUTH_PASSWORD` | If using hardcoded auth |
| `AUTH_SECRET_KEY` | JWT signing key |
| `ANTHROPIC_API_KEY` | If using Claude API |

### DATABASE_URL format for Railway Postgres
Railway's Postgres service provides a `DATABASE_URL` in `postgresql://` format.
For async SQLAlchemy (asyncpg), you must change the prefix:
```
# What Railway gives you:
postgresql://user:pass@host:port/db

# What you need for asyncpg:
postgresql+asyncpg://user:pass@host:port/db
```

### Auth not working after deploy
If login returns "Invalid credentials" even with correct username/password,
the app is using default values from `config.py` instead of env vars. Add
`AUTH_USERNAME` and `AUTH_PASSWORD` explicitly to Railway's Variables tab and
redeploy.

---

## Section 7: Railway Agent Interference

### Problem
The Railway Agent (right-side chat panel) creates `railway.json` files,
modifies start commands, and triggers redeployments — often breaking working
configurations.

### Signs of Agent interference
- Deployments triggering without a GitHub push
- `railway.json` appearing in your repo unexpectedly
- `Failed to parse JSON file railway.json: invalid character` errors
- Start command being overridden with a malformed uvicorn command

### Fix
1. **Delete railway.json** if it was created by the Agent:
   ```powershell
   del railway.json
   git rm railway.json
   git commit -m "remove bad railway.json"
   git push origin main
   ```
2. **Close the Agent panel** and do not interact with it
3. All configuration belongs in: the **Dockerfile** (CMD) and the Railway
   **Variables tab** — not in `railway.json`

---

## Section 8: Windows PowerShell Mistakes

### Problem
Instructions meant for Notepad or as explanatory text get pasted into
PowerShell/CMD, causing errors like:
```
'```' is not recognized as an internal or external command
'##' is not recognized as an internal or external command
CMD ["/bin/sh"...] — opens a new cmd.exe window
```

### Key rules for Windows users
- **Dockerfile CMD lines go in the Dockerfile file, not the terminal**
- Use `notepad Dockerfile` to edit the Dockerfile
- Use `type Dockerfile` to verify contents before committing
- Only `git add`, `git commit`, `git push` commands go in the terminal
- Never paste markdown formatting (` ``` `, `##`, etc.) into PowerShell

### Correct workflow for editing Dockerfile on Windows
```powershell
# 1. Open in editor
notepad Dockerfile

# 2. Make changes, save, close Notepad

# 3. Verify the change
type Dockerfile

# 4. Commit and push
git add Dockerfile
git commit -m "describe the change"
git push origin main
```

---

## Section 9: Forcing a Fresh Railway Build (Cache Busting)

### Problem
Railway caches Docker layers. After fixing a Python file, Railway may redeploy
the old cached image and not pick up your changes.

### Signs of a cached deploy
- Deploy logs show all steps as "cached"
- Runtime error is the same as before despite a fix being pushed
- Build time is under 15 seconds (normal build is 60-100 seconds)

### Fix: Cache-busting commit
```powershell
echo "# cache bust" >> api/app/database.py
git add api/app/database.py
git commit -m "fix: force fresh Railway build"
git push origin main
```

This touches a file in the `api/` directory, which invalidates Railway's
layer cache for `COPY api/ .` and everything after it.

---

## Section 10: Security Checklist Before Going Live

| Item | Action |
|------|--------|
| `.env` in `.gitignore` | `echo ".env" >> .gitignore` then commit |
| API keys in `.env` exposed on GitHub | Rotate at provider (Anthropic, etc.) |
| Default `AUTH_PASSWORD` | Change to strong password in Railway Variables |
| Default `AUTH_SECRET_KEY` | Set a random 32+ char string in Railway Variables |
| `railway.json` with secrets | Delete it — secrets belong in Variables tab only |

### Check if .env was committed to GitHub
```powershell
git log --all --oneline -- .env
```
If any commits appear, your secrets may be in GitHub history. Rotate all
keys immediately and use `git filter-branch` or BFG Repo Cleaner to purge.

---

## Complete Dockerfile Template (FastAPI + Railway)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ .

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Shell form required for $PORT variable expansion
# app.main:app = file at api/app/main.py with app = FastAPI()
CMD ["/bin/sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4"]
```

**Adjust the module path** based on your file structure:
- `api/main.py` → `main:app`
- `api/app/main.py` → `app.main:app`
- `api/src/main.py` → `src.main:app`

---

## Verification Checklist (Run After Every Deploy)

```powershell
# 1. Test health endpoint
curl https://YOUR-APP.up.railway.app/api/health

# 2. Test API docs load
# Open in browser: https://YOUR-APP.up.railway.app/docs

# 3. Confirm correct commit is deployed
git log --oneline -3
```

**Healthy health check response:**
```json
{"status": "ok"}
```

**Healthy startup logs:**
```
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

---

## Quick Reference: Error → Fix Mapping

| Error | Fix |
|-------|-----|
| `'--workers' is not a valid integer` | Argument order wrong in CMD; `--port` has no value |
| `'$PORT' is not a valid integer` | Use shell form `["/bin/sh", "-c", "..."]` not array form |
| `Could not import module "main"` | Wrong module path; check actual file location |
| `InFailedSQLTransactionError` on startup | Split pgvector extension + create_all into two transactions |
| `Application failed to respond` 502 | Check Deploy Logs; app crashing before binding to port |
| Login returns "Invalid credentials" | Add AUTH_USERNAME/AUTH_PASSWORD to Railway Variables tab |
| Build succeeds but deploy fails | Read Runtime/Deploy Logs tab, not Build Logs tab |
| Railway keeps redeploying on its own | Railway Agent is active; close it and delete railway.json |
