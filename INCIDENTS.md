# INCIDENTS.md — Recursive Self-Improvement Protocol (MANDATORY)
> **L1:** Every failure triggers 5-Whys RCA → immediate fix → update SKILL.md/companion file → add monitoring check. Schema for incidents.jsonl. Lessons learned table.

**Every failure triggers this loop. Every project completion triggers this loop. This is not optional.**

## The Loop: Fail → RCA → Fix → Prevent → Learn

### Step 1 — Detect
Any agent encounters a failure, timeout, stall, or unexpected behavior.

### Step 2 — Root Cause Analysis + Research (immediate)
- Document in `memory/incidents.jsonl` (schema below)
- Ask "Why?" at least 3 times (5-Whys method) to get past symptoms
- **MANDATORY: Before building ANY workaround, search trusted sources** for the exact error + "root cause" + "permanent fix":
  - Official docs (Google, Anthropic, Railway, Dropbox, etc.)
  - Stack Overflow (top-voted answers)
  - GitHub issues on the relevant repo
  - Recent articles (last 3 months) from trusted tech publications
- Example of WRONG approach: "Token expires → build a cron to refresh it every 6 days"
- Example of RIGHT approach: "Token expires → search WHY → find Google Testing mode is the cause → change to Production → problem eliminated permanently"
- **The rule: a 10-minute search beats a 10-hour workaround. Every time.**

### Step 3 — Implement Fix
- Fix the immediate problem
- Update the relevant AGENTS.md/DELEGATION.md/SKILL.md so the failure class is prevented
- If the fix needs a cron job, script, or check → create it, don't just document it

### Step 4 — Verify Prevention
- Confirm fix is live (cron running, skill updated, rule enforced)
- Add a Monitor check that would catch recurrence
- Update `memory/incidents.jsonl` with resolution

### Step 5 — Learn & Propagate
- If fix applies to multiple agents → update ALL affected profiles
- Update `memory/skill-suggestions.md` for Librarian's weekly review
- Same error >2 times → escalate to Eric with structural fix proposal

## Triggers
- **Every failure** — cron error, auth timeout, stalled task, dashboard mismatch, broken link, missing deliverable
- **Every project completion** — what went well? what was slow? what should be automated?
- **Every Eric complaint** — if Eric has to ask "why isn't this done?", that's a trigger
- **Weekly Librarian review** — scan incidents.jsonl for patterns

## Incident Schema
```json
{
  "timestamp": "<ISO8601>",
  "agent": "<agent_name>",
  "project": "<project_name>",
  "error_category": "<auth|dashboard|git|powerspec|cron|deliverable|ui|stall|other>",
  "error_summary": "<one sentence>",
  "root_cause": "<5-Whys result>",
  "fix_applied": "<what was done>",
  "prevention": "<what was changed to prevent recurrence>",
  "resolved": true
}
```

## Lessons Learned (2026-03-22 to 2026-03-24)
| Incident | Root Cause | Prevention |
|----------|-----------|------------|
| Dashboard showed 100% without commits | Progress from elapsed time | Milestone-based progress; Conductor gate requires commit SHA |
| PowerSpec idle while tasks queued | Usage was optional | PowerSpec-First policy; Monitor alerts on idle GPU |
| Terminal nav link dead | Placeholder shipped without QA | External Auditor clicks every nav item; dead links = auto-fail |
| gog token expired, cron jobs failed | No automated auth refresh | 4h auth health check cron; Monitor pre-flight auth check |
| Steps 1-2 stalled 12+ hours | Context-switching, no enforcement | 5-min Monitor sweep; stale task alerting |
| No GitHub repo for Mission Control | Git init not in process | Planner must include repo setup in every PLAN.md |
| Report marked complete without email | No deliverable gate | Conductor/Quality verify email before 100% |

## Proactive Improvement (after EVERY project)
1. What took longer than expected? → Can it be automated?
2. What required manual intervention? → Can an agent handle it?
3. What knowledge was gained? → Should it become a Skill?
4. Was PowerSpec fully utilized? → If not, why?

**Priorities:** Correctness > Stability > Security > Efficiency > Automation

## 🔬 RCA as Core of All Testing & Debugging (Standing Change 2026-03-28)

**Root Cause Analysis is not a post-mortem activity. It is the FIRST step in debugging, not the last.**

When ANY failure occurs:
1. **STOP** — Do not apply the first fix that comes to mind
2. **RESEARCH** — Search the exact error message in official docs, Stack Overflow, GitHub issues
3. **TRACE** — Follow the data flow from input to output. Where does correct data become incorrect?
4. **VERIFY** — Before applying ANY fix, explain WHY it will work. "This should fix it" is not acceptable. "This fixes it because X was causing Y which led to Z" is.
5. **TEST THE OUTPUT** — After fixing, verify the OUTPUT is correct, not just that the error is gone
6. **DOCUMENT** — Add to incidents.jsonl so future sessions don't repeat the investigation

**Every failure must trace to an output correctness gap:**
- "The report was empty" → WHY was it empty? → synthesis dict nested wrong → test that output content is non-empty
- "The API key was truncated" → WHY was it truncated? → .env inline comment → validate key length on startup
- "The parser returned defaults" → WHY did it return defaults? → shared parser with wrong schema → separate parsers per schema

**The anti-pattern we're eliminating:** Fix symptom → ship → same class of bug recurs → fix next symptom → ship → repeat forever. This wastes 10x more time than finding the root cause once.

## Lessons Learned (2026-03-27): FinancialReportApp Silent Failures

| Incident | Root Cause | Prevention |
|----------|-----------|------------|
| Reports emailed with "done" status but empty content | No output quality validation — checked status, not content | Output Quality Gate: open deliverable, verify >100 chars real analysis, <3 placeholders |
| Anthropic API key truncated inside Docker container | `.env` inline comment (`# Required...`) treated as value by Docker Compose | .env file rules: NO inline comments ever; validate env var length on container startup |
| Synthesis data nested under wrong key | `company_data["synthesis"] = {...}` instead of `company_data.update(synthesis)` | Integration test that reads output .docx and asserts content quality |
| JSON parser returned tagger schema for synthesis output | Shared `_parse_llm_response()` with tagger-shaped fallback dict | Separate parsers per schema; use Anthropic structured outputs (`output_format`) |
| 90+ minutes of symptom-by-symptom debugging | No upfront RCA — fixed each bug reactively | Research first, understand the failure class, then fix all related issues at once |
| "Works on Mac, breaks in Docker" pattern | No environment parity testing; dev on Mac, deploy on Windows Docker | E2E smoke test inside container; env validation on startup; test parsers with known input |
