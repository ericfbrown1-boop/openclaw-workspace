# PIPELINE.md — Code Pipeline, Completion Gates & Dashboard Rules
> **L1:** 4-phase workflow (Understand→Plan→Implement→Verify), task complexity gate, model tiering with costs, API budget gate, dual-write dashboard rule, test oracle references, E2E verification checklist.

## 🎯 Guiding Principle: CORRECTNESS OF OUTPUT (Standing Change 2026-03-28)

**Output correctness is the north star for the entire SDLC.** Every decision — planning, coding, testing, debugging — optimizes for one thing: the output the user receives must be correct, complete, and verifiable.

This means:
- **Testing proves output correctness**, not just "no errors." A pipeline that completes without errors but produces empty/wrong output has FAILED.
- **RCA is the core of all debugging.** When something breaks, don't fix the symptom — find the root cause, fix it permanently, document it so it never recurs.
- **Quality gates block bad output.** Gates log AND raise — never just log. A bad report must fail, not silently email garbage.
- **Retry only transient failures.** Rate limits and timeouts retry. Content quality failures do NOT retry — same input produces same bad output.
- **Silent fallbacks are bugs.** Every fallback to a default/placeholder is a logged WARNING. More than 3 fallbacks = pipeline FAILURE.

| Priority | Principle |
|----------|-----------|
| 1 | **Output is correct** (content matches what was requested) |
| 2 | **Output is complete** (no missing sections, no placeholders) |
| 3 | **Failures are visible** (never silently succeed with bad output) |
| 4 | **Root causes are fixed** (not symptoms, not workarounds) |
| 5 | **Speed** (only after 1-4 are satisfied) |

## 4-Phase Workflow (MANDATORY for ALL task types)

Every task — code, research, audit, monitoring — follows these 4 phases:

```
Phase 1: UNDERSTAND → Phase 2: PLAN → Phase 3: IMPLEMENT → Phase 4: VERIFY
```

| Phase | What Happens | Who | Gate to Next Phase |
|-------|-------------|-----|-------------------|
| **1. UNDERSTAND** | Read codebase, gather requirements, identify constraints. "Explore First" rule. | Planner + Researcher | PROJECT_CONTEXT.md exists |
| **2. PLAN** | Design approach, decompose tasks, identify risks, set verification criteria. | Planner (+ Grok 4.20 Beta adversarial review) | PLAN.md approved by Jarvis |
| **3. IMPLEMENT** | Execute the plan. Write code, send reports, run analysis. Verify at each CHECKPOINT. | Coder / Researcher / Conductor | HANDOFF.md + git push |
| **4. VERIFY** | Test, review, audit, deploy. Multi-gate: Tester → Quality → Auditor → Conductor. | Tester + Quality + Auditor + Conductor | Completion gate passes (SHA or email ID in tasks.json) |

**Apply to ALL task types:**
- **Code tasks:** Understand codebase → Plan architecture → Implement code → Verify (tests + deploy)
- **Research tasks:** Understand question → Plan search strategy → Implement research → Verify findings (cross-check sources)
- **Error diagnosis:** Understand error context → Plan investigation → Implement fix → Verify fix works
- **Monitoring tasks:** Understand alert condition → Plan check → Implement sweep → Verify system healthy
- **Report tasks:** Understand requirements → Plan outline → Implement writing → Verify deliverable sent

## Hybrid Build Routing — macbook vs powerspec (Standing Change 2026-04-11)

`jarvis_pipeline.py` supports routing the Coder stage to PowerSpec via the `task.execution.coderHost` field. Use `"powerspec"` when:
- Build >15 min (frees Mac for interactive work)
- GPU required (RTX 5080)
- Windows-specific testing
- Large file IO (PowerSpec has faster NVMe)

Use `"local"` (default) when:
- Task is <5 min
- Depends on Mac-specific paths / tools (homebrew, launchd, Tailscale Serve)
- PowerSpec node is offline / unreachable

**Task schema extension:**
```json
{
  "id": "...",
  "execution": {
    "coderHost": "local" | "powerspec",
    "remoteWorkDir": "C:\\Users\\Eric Brown\\repos\\<task-id>",
    "remoteGitRepo": "https://github.com/..."
  }
}
```

The pipeline-state.json records `stages.coder.host` so audit trail shows which machine ran the work. Mission Control agentChain entries carry a `host` field per stage. See DELEGATION.md "Option C" section for full details and setup.

## Complete Code Pipeline (Detailed)

```
Phase 1: UNDERSTAND
  → Planner reads existing codebase ("Explore First" rule)
  → Researcher gathers requirements if needed
  → Output: PROJECT_CONTEXT.md

Phase 2: PLAN
  → Researcher gathers latest info on task domain (key success factors, pitfalls)
  → Planner (Opus 4.6) drafts PLAN.md informed by Research Brief
  → Grok 4.20 Beta adversarial review (challenges assumptions, finds gaps)
  → Jarvis merges Grok feedback into final PLAN.md
  → Output: Final PLAN.md (research-backed, dual-model reviewed)

Phase 3: IMPLEMENT
  → Coder implements (writes CHECKPOINT.md at each phase)
  → Coder verifies at each checkpoint (tests, Docker build, health check)
  → Output: HANDOFF.md + git push (DO NOT commit to GitHub yet)

Phase 4: VERIFY (includes Recursive Adversarial Code Review Loop)
  → Tester (import verification + test suite)
    → If FAIL: returns to Coder (Phase 3)
    → If PASS: HANDOFF.md for Quality
  → Quality (Security Audit + Code Review)
    → If CRITICAL: BFG cleanup, loop back to Phase 3
    → If CLEAN: proceed
  ┌─── ADVERSARIAL CODE REVIEW LOOP (MANDATORY) ──────────────────┐
  │                                                                │
  │  LOOP ITERATION 1:                                             │
  │  → Auditor (Grok 4.20+) performs adversarial code review       │
  │    → Reviews ALL code for: bugs, security, edge cases,         │
  │      performance, architecture, missing tests, race conditions │
  │    → Produces structured findings: CRITICAL / HIGH / MEDIUM    │
  │    → If CRITICAL or HIGH findings exist:                       │
  │      → Findings fed back to Jarvis                             │
  │      → Jarvis updates PLAN.md with Auditor feedback            │
  │      → Coder re-implements fixes                               │
  │      → Code pushed again (still not to GitHub main)            │
  │      → LOOP BACK to Auditor for re-review                     │
  │                                                                │
  │  LOOP ITERATION 2+:                                            │
  │  → Auditor re-reviews ALL changes + verifies fixes             │
  │    → Confirms each CRITICAL/HIGH finding is resolved           │
  │    → May find NEW issues introduced by fixes                   │
  │    → If new CRITICAL/HIGH: loop again (max 3 iterations)       │
  │    → If all CRITICAL/HIGH resolved: APPROVE                   │
  │                                                                │
  │  EXIT CONDITIONS:                                              │
  │  → All CRITICAL and HIGH findings resolved (APPROVED)          │
  │  → Max 3 loop iterations reached (escalate to Eric)            │
  │  → MEDIUM findings logged but do NOT block                     │
  │                                                                │
  └────────────────────────────────────────────────────────────────┘
  → Auditor APPROVED → git push to GitHub (NOW safe to commit)
  → Conductor (Docker build + deploy + smoke tests)
  → Librarian (post-audit review, suggests improvements)
  → Code shipped ✅
```

## 🔁 Recursive Adversarial Code Review (Standing Change 2026-04-17)

**MANDATORY for ALL code projects. No code reaches GitHub without passing this loop.**

### The Rule

Before ANY `git push` to GitHub, the Auditor Agent (Grok 4.20 or higher) MUST perform a full adversarial code review. If the Auditor finds CRITICAL or HIGH severity issues:

1. **Auditor findings → Jarvis** — Jarvis receives the structured review
2. **Jarvis → Plan update** — Jarvis incorporates findings into the plan
3. **Plan → Coder** — Coder re-implements based on updated plan + Auditor feedback
4. **Coder → Auditor** — Fixed code goes back to Auditor for re-review
5. **Repeat** until Auditor approves OR max 3 iterations reached

This is a **recursive loop** — not a single-pass gate. The Auditor reviews the FIXES too, catching regressions and new bugs introduced by the remediation.

### Auditor Review Scope (EVERY iteration)

The Auditor MUST check ALL of the following on EVERY review pass:

| Category | What to Check |
|----------|---------------|
| **Correctness** | Logic bugs, wrong model names, incorrect API calls, broken integrations |
| **Security** | Leaked secrets, injection vectors, auth bypasses, unsafe defaults |
| **Edge Cases** | Empty inputs, timeouts, race conditions, concurrent access, error paths |
| **Performance** | Unbounded loops, missing pagination, log file growth, resource leaks |
| **Architecture** | Wrong abstractions, tight coupling, missing error handling layers |
| **Testing** | Missing test coverage, untested error paths, no integration tests |
| **Operations** | Log rotation, alerting gaps, missing health checks, config drift |
| **Dependencies** | Wrong versions, deprecated APIs, missing fallbacks |

### Severity Classification

| Severity | Definition | Action |
|----------|-----------|--------|
| **CRITICAL** | System will break, security vulnerability, data loss risk | MUST fix — blocks approval |
| **HIGH** | Significant bug, incorrect behavior, missing functionality | MUST fix — blocks approval |
| **MEDIUM** | Code quality, minor edge case, improvement opportunity | Logged, does NOT block |
| **LOW** | Style, naming, documentation | Noted for future |

### Loop Control

- **Max iterations:** 3 (prevents infinite loops)
- **If max reached:** Escalate remaining issues to Eric with full context
- **Each iteration:** Auditor must confirm PREVIOUS findings are resolved AND check for NEW issues
- **Auditor model:** Grok 4.20 Beta minimum (`xai/grok-4.20`). Using a lower model invalidates the review.
- **No self-review:** Jarvis/Coder cannot approve their own code. Only the Auditor agent can approve.

### What This Replaces

This replaces the old single-pass "External Auditor (6-step QA gate)" as the final code quality gate. The 6-step checklist is still used BY the Auditor within each iteration, but the recursive loop is the new enforcement mechanism.

**Origin:** Eric directive 2026-04-17 — "At the end of every project before you commit code to GitHub, the Auditor agent using Grok 4.20 or higher has to perform an adversarial code review. Feed it back into Plan, redo Coding, loop back to Auditor. This establishes a recursive loop with adversarial code review each time."

## Global Completion Gate

No task may reach 100% / `completed` without BOTH:
1. **Code tasks:** `git push` succeeded + commit SHA in `tasks.json`
2. **Report tasks:** deliverable emailed + Gmail message ID in `tasks.json`

Enforced by Conductor, verified by External Auditor, monitored by Monitor.

## Task Complexity Gate (Anthropic: "only use multi-agent for high-value parallelizable tasks")

Before spawning ANY subagent, classify the task:

| Complexity | Time Est | Scope | Action |
|-----------|----------|-------|--------|
| **SIMPLE** | < 5 min | Single file edit, quick fix | Jarvis does it directly. NO subagent. |
| **MODERATE** | 5-30 min | Multi-file, one concern | Single subagent with verification command |
| **COMPLEX** | > 30 min | Multi-step, parallelizable | Up to 3 concurrent subagents, each with plan |

**Ask before spawning:** "Could I do this in 2 minutes myself?" If yes → do it. Don't waste tokens on agent overhead.

**Token budget awareness:** Multi-agent uses ~15x more tokens than chat (per Anthropic). Only COMPLEX tasks justify the cost.

## Context Management Rules (Anthropic Best Practice)

**Cron payload limit:** No cron job message payload should exceed 500 tokens. Instead of embedding full instructions, have agents read their SKILL.md file for details. The cron message should be a brief trigger with a pointer to the skill.

**Isolated sessions:** Each pipeline stage runs in an isolated session (enforced by OpenClaw agent spawning). The main session orchestrates but does NOT execute heavy work. This prevents context bloat.

**Context hygiene:** When compaction warnings appear or context gets heavy, proactively save state to memory files and start fresh rather than dragging a massive conversation forward. Files survive sessions; context doesn't.

**Verification criteria:** Every task dispatch must include success criteria that the agent can verify programmatically (e.g., "tests pass", "curl /health returns 200", "lint clean"). Tasks without verification criteria are incomplete.

## Dashboard-as-Source-of-Truth Rule (DUAL WRITE)

**Two tasks.json files must stay in sync:**
1. `~/.openclaw/workspace/tasks.json` — OpenClaw agents read/write (source of truth)
2. `~/JarvisMissionControl/backend/data/tasks.json` — Mission Control dashboard reads

**Every agent** must update **BOTH** `tasks.json` files when:
- Task starts → `status: "running"` + `progress: 25`
- Milestone hit → increment `progress` (25 → 50 → 75)
- Task completes → `status: "completed"` + `progress: 100` (only after gate passes)
- Task fails/cancelled → `status: "failed"` + `error` field
- New task created → add immediately with `status: "queued"`

**New projects** appear on Task Board the moment they are requested.
**Monitor** verifies every 5 minutes; stale entries (>2h no update) trigger alert.
**Eric should never have to ask "status?"**

## API Budget Cost Gate (MANDATORY)

Before any Opus 4.6 task, check `memory/api-usage-state.json`:

| Budget Used | Action |
|-------------|--------|
| < 75% | Normal operations — use Model Tiering below |
| 75–90% | **Downgrade**: All non-critical tasks use Sonnet 4.6 (only Jarvis orchestration stays on Opus) |
| > 90% | **Pause**: Non-essential work stops. Alert Eric. Only critical fixes proceed (on Sonnet) |

Agents read `alert_level` from the state file:
- `"none"` or `"info"` → normal
- `"warning"` → downgrade to Sonnet
- `"critical"` → pause + alert

## Model Tiering Strategy

| Agent | Model | Context | Cost (in/out per M) | Rationale |
|-------|-------|---------|---------------------|-----------|
| Jarvis (main) | Opus 4.6 | 200K | $15 / $75 | Orchestration needs best reasoning |
| Planner (draft) | Opus 4.6 | 200K | $15 / $75 | Architecture needs depth; drafts PLAN.md from Research Brief |
| Researcher | Opus 4.6 | 200K | $15 / $75 | Depth + source-weighting for research briefs (updated 2026-04-11) |
| Planner (adversarial review) | Grok 4.20 Beta | 2M | ~$2 / $6 | Challenges plan assumptions, finds gaps, stress-tests for production readiness |
| Coder | Opus 4.6 | 200K | $15 / $75 | Correctness-first code synthesis; over-engineering caught by Quality (updated 2026-04-11) |
| Tester | Sonnet 4.6 | 200K | $3 / $15 | Test execution is deterministic |
| Quality | Grok 4.20 Beta | 2M | ~$2 / $6 | Adversarial output-correctness judgment — same reason Auditor uses Grok. Updated 2026-04-11. |
| Conductor | Sonnet 4.6 | 200K | $3 / $15 | Infrastructure tasks well-defined |
| External Auditor | Grok 4.20 Beta | 2M | ~$2 / $6 | Adversarial final-gate review; same model as Quality for consistency (updated 2026-04-13) |
| Librarian | Sonnet 4.6 | 200K | $3 / $15 | Analysis can use cheaper model |
| Monitor | Sonnet 4.6 | 200K | $3 / $15 | Simple monitoring tasks |

### Model Fallback Chain
If a primary model is unavailable (rate limit, outage, cooldown):
1. **Opus 4.6** → Grok 4.20 Beta → Sonnet 4.6 (used by main/researcher/planner/coder)
2. **Grok 4.20 Beta** → Opus 4.6 → Sonnet 4.6 (used by auditor/quality)
3. **Sonnet 4.6** → Grok 4.20 Beta → Opus 4.6 (used by tester/conductor/monitor fallback)
4. **Sonnet 4.6** → Grok 4.20 Beta (used by monitor/conductor — upgraded 2026-04-11 from grok-4)

## Test Oracle Schemas

Every task type has a formal verification schema in `skills/auditor/TEST_ORACLES.md`. Agents MUST:
1. **Planner**: Include the relevant oracle in PLAN.md `successCriteria`
2. **Coder/Researcher**: Self-check against oracle BEFORE writing HANDOFF.md
3. **Tester**: Validate oracle checks programmatically
4. **Monitor**: Verify completed tasks satisfy their oracle (Step 11: 4-Phase Compliance)

Available oracles: `task_completion`, `code_task`, `research_task`, `report_task`, `error_diagnosis`, `monitoring_sweep`, `earnings_analysis`, `competitive_intel`.

## E2E Verification Checklist

Before marking any pipeline run complete, verify:
1. **Agent health:** Each agent responds to a test prompt
2. **Delegation:** Keyword triggers route to correct agent (test each trigger)
3. **Pipeline flow:** Task flows Planner → Coder → Tester → Quality → Auditor → Conductor without stalling
4. **Completion gate:** tasks.json shows commit SHA and/or email ID
5. **Cron jobs:** All scheduled jobs show `lastStatus: "ok"` in `memory/cron-state.json`
6. **Fallbacks:** Simulate auth failure → verify fallback path activates

## Pre-Commit Quality Gate (MANDATORY)

**No code may be committed without passing ALL of these checks first.** This is a standing process change (2026-03-27).

### Checklist (run in order):

```
1. SYNTAX CHECK    node --check <file>  (for every new/modified .js/.ts file)
2. TEST SUITE      npm test  (or equivalent — must pass, zero failures)
3. LINT            eslint / ruff / shellcheck if configured (warnings OK, errors block)
4. SECRET SCAN     grep -r "sk-ant\|sk-proj\|ghp_\|API_KEY=" <new files>  (must be clean)
5. DRY RUN         Execute the primary code path once (e.g. --help, --dry-run, or a single-page test)
6. DIFF REVIEW     git diff --staged  — read what you're committing, verify no debug code or temp files
```

### Enforcement:

| Check | Blocks Commit? | Who Runs It |
|-------|---------------|-------------|
| Syntax check | ✅ Yes | Coder / Jarvis |
| Test suite | ✅ Yes | Coder / Quality |
| Lint | ⚠️ Errors only | Coder |
| Secret scan | ✅ Yes | Quality / pre-commit hook |
| Dry run | ✅ Yes | Coder |
| Diff review | ✅ Yes | Jarvis (before `git commit`) |

### Quick Command:

```bash
# Run all checks in one shot (Node.js projects)
for f in $(git diff --cached --name-only --diff-filter=ACM | grep '\.js$'); do node --check "$f" || exit 1; done \
  && npm test \
  && ! grep -r 'sk-ant\|sk-proj\|ghp_\|API_KEY=' $(git diff --cached --name-only) \
  && echo "✅ Quality gate passed — safe to commit"
```

**Origin:** Eric directive 2026-03-27 — "Make sure you apply Quality Agent before committing code"

## Docker Containerization Checklist (Standing Rule 2026-03-27)

**When moving standalone MacBook code into Docker/Railway:**

Before writing the Dockerfile, audit the standalone code for:
1. **CLI tools** — what binaries does it shell out to? (gog, gh, curl, etc.) → install in Dockerfile
2. **Auth tokens** — where are credentials stored? (Keychain, env, config files) → export and inject into container
3. **API keys** — what env vars does it read? → map to docker-compose environment or Railway vars
4. **Python packages** — what's imported? → requirements.txt must match
5. **System libraries** — any C extensions? (libpq, poppler, tesseract) → apt-get install
6. **File paths** — any hardcoded Mac paths? → containerize to /app/data/
7. **Network** — does it call localhost services? → use Docker service names

**Verify INSIDE the container** with `docker exec` before declaring it works.

**8. .env file** — NO inline comments (Docker Compose truncates at `#`). NO trailing whitespace. Validate on startup.
**9. Output quality** — after deploy, run E2E test: submit real request → wait → open output → verify real content (not defaults)
**10. Parser schemas** — if the app parses LLM JSON, each output schema has its own parser with correct fallback shape

**Origin:** Financial Report App — standalone used gog CLI + Keychain OAuth + Anthropic env var, none of which existed in the initial Docker image. Eric directive: "check what was done in the application and what's installed to see if you have the same compatibility inside the Docker container."

## 🔴 Output Quality Gate (Standing Change 2026-03-27)
**Origin:** FinancialReportApp — 3 reports emailed with "done" status but zero content. RCA: `memory/rca-financial-report-app.md`

### The Problem Class: "Silent Success"
A pipeline can complete every step (crawl ✅, API call ✅, save file ✅, send email ✅) while producing garbage output. This happens when:
1. An API key is truncated by env file parsing (Docker Compose `#` comment issue)
2. A data structure is nested wrong (dict inside dict instead of merged)
3. A JSON parser silently falls back to a default schema
4. Error handlers catch exceptions and return empty defaults instead of failing

### Prevention Rules (ALL agents, ALL pipelines):

**Rule 1: Validate Output Content, Not Just Status**
After EVERY deliverable is generated, open it and check:
```python
# For .docx reports:
doc = Document(output_path)
text = " ".join(p.text for p in doc.paragraphs)
assert len(text) > 500, "Report suspiciously short"
assert text.count("not available") < 3, "Report contains too many placeholder defaults"
assert text.count("not found") < 3, "Report contains too many missing-data markers"
```

**Rule 2: Fail Loud, Not Silent**
Every fallback/default MUST log WARNING. >3 defaults in one run = pipeline FAILURE.
```python
# BAD: silently return default
return data.get("executive_summary", "Analysis not available.")

# GOOD: log and count
value = data.get("executive_summary")
if not value:
    logger.warning("MISSING FIELD: executive_summary — using default")
    missing_count += 1
if missing_count > 3:
    raise ValueError(f"Too many missing fields ({missing_count}) — synthesis likely failed")
```

**Rule 3: Env Validation on Startup**
Every containerized app must validate env vars BEFORE processing requests:
```python
def validate_env():
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key.startswith("sk-ant-") or len(key) < 80:
        raise RuntimeError(f"ANTHROPIC_API_KEY invalid (length={len(key)}, prefix={key[:7]})")
    # Test connectivity
    resp = httpx.post("https://api.anthropic.com/v1/messages", ...)
    if resp.status_code == 401:
        raise RuntimeError("ANTHROPIC_API_KEY fails authentication")
```

**Rule 4: Use Structured Outputs When Available**
For Claude API calls that need JSON, use `output_format` with Pydantic models instead of free-text JSON parsing:
```python
from pydantic import BaseModel
from anthropic import Anthropic

class FinancialSynthesis(BaseModel):
    executive_summary: str
    quarterly_results: dict
    guidance: str
    # ... all required fields

response = client.messages.parse(
    model="claude-sonnet-4-6",
    messages=[...],
    output_format=FinancialSynthesis,
)
# Guaranteed to match schema or raise an error — no silent fallbacks
```

**Rule 5: E2E Smoke Test Before Deploy**
No Docker app ships without an automated E2E test that:
1. Submits a real request
2. Waits for completion
3. Downloads the output artifact
4. Asserts content quality (not just existence)

### Output Parity Rule (Standing Change 2026-03-28)

**When an app delivers output through multiple channels (email, download, preview, API), ALL channels MUST serve the exact same content.**

This means:
1. **Generate once, serve many.** One file is generated and stored. Every channel reads from the same file path.
2. **Hash verification.** After generating the output file, compute SHA256 and store it. On download, recompute and verify the hash matches — reject if it doesn't.
3. **No re-generation.** Never re-render or re-generate on download. The download endpoint serves the file as-is.
4. **No caching surprises.** Set `Cache-Control: no-cache, no-store` and `ETag` on download responses to prevent stale cached versions.
5. **Audit trail.** Log the hash at generation time and verify it at download time. If they diverge, log an INTEGRITY VIOLATION.

**Implementation pattern:**
```python
# At generation time:
hash = sha256(file_bytes).hexdigest()
db.store(file_hash=hash)

# At download time:
current_hash = sha256(read_file()).hexdigest()
assert current_hash == db.file_hash, "INTEGRITY VIOLATION"
response.headers["ETag"] = hash
response.headers["Cache-Control"] = "no-cache, no-store"
```

**Origin:** Eric directive 2026-03-28 — emailed report had full content, browser download had different/stale content.

### Docker .env File Rules (Permanent)
- **NEVER** use inline comments in `.env` files (`KEY=value # comment` → KEY gets truncated)
- **NEVER** use quotes around values unless they contain spaces
- Keep `.env` files as `KEY=value` only, one per line
- Validate env vars on container startup (prefix, length, connectivity)
- This is a well-documented Docker Compose issue: docker/compose#9025, #9327, #9509

### LLM Response Parsing Rules (Permanent)
- **Prefer structured outputs** (Anthropic `output_format`, OpenAI JSON mode) over free-text parsing
- If free-text parsing is required, each schema gets its OWN parser with schema-appropriate fallbacks
- Never share a parser between components expecting different JSON shapes
- When a parser fails, preserve the raw response for debugging (`_rawResponse`)
- Add recovery logic that re-parses `_rawResponse` before giving up

---

## 🏆 Coding Quality Standard (Standing Rule — 2026-04-13)

**Always seek the highest quality solution. Complete projects successfully with minimum interruptions to Eric. Never give up.**

### When a coding task hits a blocker:
1. **Try to fix it yourself first** — read docs, check logs, search for the exact error
2. **Spawn the right specialist** — Coder, Auditor, RCA Agent, Researcher. Pipeline exists; use it.
3. **Pivot, don't quit** — if one approach fails, try another. Report the pivot, not the failure.
4. **Only interrupt Eric if:** real money at stake, external comms going out, genuinely ambiguous requirements, or security-critical decision.

### Persistence hierarchy (exhaust in order before asking Eric):
1. Fix it yourself
2. Spawn Coder agent
3. Spawn Auditor for RCA
4. Spawn RCA Agent + Auditor dual-RCA
5. Research via Researcher agent
6. Try alternative implementation approach
7. **Only then:** ask Eric — but include what you tried and what the specific blocker is

**Origin:** Eric directive 2026-04-13
