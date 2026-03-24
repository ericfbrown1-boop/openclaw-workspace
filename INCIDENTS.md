# INCIDENTS.md — Recursive Self-Improvement Protocol (MANDATORY)

**Every failure triggers this loop. Every project completion triggers this loop. This is not optional.**

## The Loop: Fail → RCA → Fix → Prevent → Learn

### Step 1 — Detect
Any agent encounters a failure, timeout, stall, or unexpected behavior.

### Step 2 — Root Cause Analysis (immediate)
- Document in `memory/incidents.jsonl` (schema below)
- Ask "Why?" at least 3 times (5-Whys method) to get past symptoms
- Example: "Cron failed" → Why? "Token expired" → Why? "No auto-refresh" → Why? "Auth check wasn't automated" → **Root cause: monitoring was rules on paper, not running code**

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

**Priorities:** Stability > Security > Efficiency > Automation
