# Anthropic Alignment Audit — 2026-03-25

**Auditor:** Inspector (Quality Agent)
**Sources:** Anthropic multi-agent research system (Mar 2026), Claude Code best practices (Mar 2026), Claude Code subagent patterns (Mar 24, 2026)
**Scope:** All workspace governance files vs. Anthropic principles, mapped to 9 real-world failures from this session

---

## Executive Summary

Our multi-agent system has **strong documentation** (incident tracking, pipeline stages, monitor sweeps) but suffers from **six structural gaps** that Anthropic's latest guidance directly addresses. The root pattern: **we document rules but lack enforcement mechanisms, verification loops, and cost awareness.** Eric had to intervene 9 times because agents had no way to self-verify, no way to unblock auth-gated workflows, and no budget guardrails to prevent runaway token usage on low-value tasks.

**Findings:** 4 CRITICAL, 7 HIGH, 5 MEDIUM

---

## GAP 1: No Verification Criteria in Task Dispatches

**Anthropic principle violated:** "Give agents verification criteria (tests, screenshots, expected outputs) — single highest-leverage practice" (Source 2)

**Our specific problem:** DELEGATION.md's "Global Dispatch Rule" requires file paths, example patterns, and success criteria — but there's no **template or schema** enforcing this at dispatch time. The rule is advisory. When Jarvis spawns a subagent, nothing validates that the dispatch message contains verification criteria.

**Session failure it caused:** #3 (Dashboard showed false 100% completion), #8 (Terminal nav link was a dead placeholder that shipped without QA). Both shipped because no agent had a concrete "verify by clicking/curling this" instruction attached to the task.

**Concrete fix:**
- Add a `DISPATCH_TEMPLATE.md` to the workspace with required fields: `objective`, `output_format`, `verification_command`, `success_criteria`, `failure_criteria`
- DELEGATION.md should mandate: "Any dispatch without a `verification_command` field is invalid — Jarvis must add one before spawning"
- Monitor should check that every running task in tasks.json has a `verificationCmd` field; missing = flag

**Priority:** CRITICAL

---

## GAP 2: No Auth Fallback Automation — Browser-Gated Workflows Block Agents

**Anthropic principle violated:** "Subagents need restricted tool access and independent permissions to prevent side effects when running concurrently" / "Each subagent should have restricted tool access" (Sources 1, 3)

**Our specific problem:** Railway CLI requires `railway login --browserless` with interactive browser confirmation. The railway-deployment skill documents this (Section 16: "This requires an interactive terminal. It will NOT work in SSH sessions or automated scripts") but provides **no automated alternative.** Similarly, `gog auth add --force-consent` requires a browser. When auth expires, agents stall until Eric manually opens a browser.

**Session failures it caused:** #1 (Railway deployment needed Eric to open browser for CLI auth, set variables, check deploy logs, change port), #5 (gog auth expired silently, breaking cron jobs)

**Concrete fix:**
- Railway skill: Replace CLI workflow entirely with GitHub-push-only workflow. Remove all `railway` CLI references from agent dispatches. The skill already documents this in Section 16 but agents still attempt CLI auth. Add to DELEGATION.md: "NEVER use `railway` CLI in automated workflows. Deployment is GitHub push → Railway auto-deploy → verify via public URL curl."
- gog auth: Add to Monitor skill Step 0: "If gog auth fails AND browser is unavailable, immediately (a) switch all email to Zapier MCP fallback, (b) alert Eric with exact re-auth steps, (c) set `auth_degraded: true` in cron-state.json so no cron job silently fails"
- Add an `AUTH_FALLBACKS.md` documenting every credential, its expiry behavior, its automated renewal path, and its manual-only renewal path

**Priority:** CRITICAL

---

## GAP 3: No Token/Cost Budget or Tracking

**Anthropic principle violated:** "Multi-agent systems use ~15x more tokens than chat — only use for high-value parallelizable tasks" / "Token usage explains 80% of performance variance — manage it actively" / "Cost tracking is essential — multi-agent workflows generate unpredictable token costs" (Sources 1, 3)

**Our specific problem:** PIPELINE.md has a Model Tiering Strategy table but **zero mention of token budgets, cost tracking, or deciding when NOT to use multi-agent.** There is no mechanism to measure how many tokens a task consumed, no per-task budget, and no rule for "this task is too small for multi-agent — just do it in the main session."

**Session failure it caused:** #2 (Tasks stalled for 12+ hours). Without cost awareness, agents were likely spawned for trivial tasks, consuming context and budget without completing high-value work. No prioritization mechanism exists.

**Concrete fix:**
- Add to PIPELINE.md a "Task Complexity Gate" section:
  ```
  SIMPLE (< 5 min, single file edit): Main session only. No subagent.
  MODERATE (5-30 min, multi-file): Single subagent with budget cap.
  COMPLEX (> 30 min, multi-step): Multi-agent with plan file. Max 3 concurrent subagents.
  ```
- Add to Monitor skill: track estimated vs actual token usage per task in tasks.json (`tokenEstimate`, `tokenActual`). Flag tasks that exceed 3x estimate.
- Add to AGENTS.md: "Before spawning any subagent, ask: could I do this in 2 minutes myself? If yes, just do it."

**Priority:** CRITICAL

---

## GAP 4: AGENTS.md Size — Already Fixed but Incomplete

**Anthropic principle violated:** "CLAUDE.md files should be SHORT and human-readable" (Source 2)

**Our specific problem:** AGENTS.md was already split after the 37KB/52% truncation incident. Current sizes:
- AGENTS.md: 4.5KB ✅ (under 5KB limit)
- DELEGATION.md: 10KB ⚠️ (over the 10KB flag threshold in Monitor)
- Monitor SKILL.md: 9.9KB ⚠️ (borderline)

The split helped, but DELEGATION.md is now bloating with the External Auditor's daily/weekly standing instructions (vibe coding scan, Claude best practices audit). These are **operational cron definitions, not routing rules.** They don't belong in a delegation file.

**Session failure it caused:** #6 (AGENTS.md grew to 37KB causing 52% truncation). The fix was applied but the pattern is repeating in DELEGATION.md.

**Concrete fix:**
- Extract External Auditor's daily/weekly standing instructions into `skills/auditor/SKILL.md`
- Extract Conductor's deployment rules into `skills/conductor/SKILL.md`
- DELEGATION.md should be ONLY: trigger → agent → brief description → pointer to skill file
- Target: DELEGATION.md under 4KB (currently 10KB — 60% reduction needed)
- Monitor should enforce: no workspace .md file >8KB, no AGENTS.md/DELEGATION.md >5KB

**Priority:** HIGH

---

## GAP 5: No Proactive Status Push — Eric Had to Pull

**Anthropic principle violated:** "Save plans to memory/files because context windows get truncated above 200K tokens" (Source 1) / Context management as first-class concern (Source 2)

**Our specific problem:** PIPELINE.md says "Eric should never have to ask 'status?'" and Monitor SKILL.md has a sweep every 5 minutes — but the status report goes to... where? There's no defined **push channel** for proactive updates. The Monitor sweep checklist ends with a status format template but doesn't specify: send to Eric via Telegram at what frequency? Only on failure? On milestones?

**Session failure it caused:** #9 (Eric had to manually ask "status?" repeatedly), #7 (Monitor cron delivered nothing — Telegram message too long)

**Concrete fix:**
- Add to Monitor SKILL.md Step 11: "Push status to Eric via Telegram at these triggers:
  - Every task milestone change (25→50→75→100) — one line: `📊 TaskName: 50% (tests passing)`
  - Every 2 hours if ANY task is running — brief summary
  - Immediately on any failure or stall
  - NEVER send the full sweep output — max 280 chars per message"
- Add to Monitor: "If Telegram message exceeds 4096 chars, split into multiple messages or link to a file. NEVER silently fail to deliver because message is too long."
- Add a `status` command in AGENTS.md that Jarvis can run without spawning Monitor: just read tasks.json and report

**Priority:** HIGH

---

## GAP 6: No Subagent Type Restrictions (Explore / Plan / General)

**Anthropic principle violated:** "Subagent types: Explore (read-only), Plan (research), General (multi-step)" / "Each subagent should have restricted tool access" (Source 3)

**Our specific problem:** All agents use the same permission model. Quality Agent's AGENTS.md says "Never write, edit, or apply_patch — you are read-only" but this is an **honor system rule in a markdown file**, not an enforced permission restriction. Nothing prevents a "read-only" agent from writing files. Similarly, Researcher has no tool restrictions preventing it from modifying code.

**Session failure it caused:** Indirect — contributes to unpredictable side effects when agents run concurrently. No specific incident yet, but Anthropic calls this out as a key reliability pattern.

**Concrete fix:**
- Document subagent permission tiers in DELEGATION.md:
  ```
  EXPLORE (read-only): Quality, Researcher, Monitor — tools: read, exec(grep/cat/curl only), web_search, web_fetch
  PLAN (research + write plans): Planner — tools: above + write to plans/ directory only
  GENERAL (full): Coder, Conductor — tools: all
  ```
- Until OpenClaw supports enforced tool restrictions per agent, add to each agent's AGENTS.md: "YOUR PERMISSION TIER: EXPLORE. If you find yourself writing files, STOP and report to Jarvis."
- Track this as a feature request for OpenClaw: per-agent tool allowlists

**Priority:** HIGH

---

## GAP 7: No Isolated Git Worktrees for Parallel Work

**Anthropic principle violated:** "Agent Teams coordinate parallel workflows in isolated Git worktrees" (Source 3)

**Our specific problem:** POWERSPEC.md and remote-coder SKILL.md describe file transfer via git pull/push and rsync, but there's **no guidance on preventing git conflicts when multiple agents work on the same repo concurrently.** If Coder is pushing to main while Conductor is deploying from main, race conditions are inevitable.

**Session failure it caused:** Indirect — contributes to stalls and requires manual intervention when agents step on each other's work.

**Concrete fix:**
- Add to DELEGATION.md: "When multiple agents work on the same repo simultaneously, each must use a separate branch: `agent/<agentId>/<task>`. Only Conductor merges to main."
- Add to Coder's workflow: "Create branch `agent/coder/<task-id>` before starting work. Push to branch. Create PR. Quality reviews PR. Conductor merges and deploys."
- For PowerSpec: each agent clones into a separate directory (`/projects/<repo>-<agent>/`)

**Priority:** HIGH

---

## GAP 8: Explore-First Not Enforced for Coder

**Anthropic principle violated:** "Explore first, then plan, then code — 4-phase workflow" (Source 2)

**Our specific problem:** DELEGATION.md's Coder section says "Read Before Write: Before writing any new code, read at least 3 existing files" — good. But the Planner section's "Explore First" rule only applies to Planner creating PLAN.md. **There's no enforcement that Coder actually reads those files before writing.** No verification step, no HANDOFF.md field for "files I read before starting."

**Session failure it caused:** #8 (Terminal nav link was a dead placeholder) — Coder likely didn't explore existing nav patterns before adding a new link.

**Concrete fix:**
- Add to Coder's HANDOFF.md template: `files_explored: [list of files read before coding]` — mandatory field
- Quality Agent should verify this field exists and contains ≥3 entries
- If missing, flag as 🟡 WARNING in code quality review

**Priority:** HIGH

---

## GAP 9: PowerSpec Utilization Is "Alert and Wait" Not "Auto-Route"

**Anthropic principle violated:** "Subagents need... independent permissions to prevent side effects when running concurrently" (Source 1) — applied to compute routing

**Our specific problem:** POWERSPEC.md has extensive documentation about what SHOULD run on PowerSpec, but the enforcement model is: Monitor detects idle GPU → alerts Conductor → Conductor offloads. This is a **reactive 3-hop alerting chain**, not automatic routing. Meanwhile, PowerSpec sat idle (#4).

**Session failure it caused:** #4 (PowerSpec sat idle while work happened on MacBook)

**Concrete fix:**
- Add to DELEGATION.md Global Dispatch Rule: "When Jarvis dispatches ANY task matching PowerSpec routing rules (Docker, tests, builds, >15min), the dispatch message MUST include `host: powerspec` and the SSH command prefix. Don't rely on the agent to check POWERSPEC.md — embed the routing in the dispatch."
- Add to Planner: Compute Allocation table is not just documentation — it becomes the routing instructions that Jarvis copies into each dispatch
- Simplify Monitor's role: Monitor VERIFIES routing was correct, doesn't initiate it

**Priority:** HIGH

---

## GAP 10: No Hooks/Guardrails for Lifecycle Events

**Anthropic principle violated:** "Hooks provide lifecycle event interception for guardrails" (Source 3)

**Our specific problem:** No concept of lifecycle hooks exists in our system. When a subagent completes, fails, or times out, the response is ad-hoc. Monitor checks every 5 minutes, but there's no **event-driven** response to: agent spawn, agent completion, agent failure, auth expiry, deploy success/failure.

**Session failure it caused:** #2 (Tasks stalled for 12+ hours), #5 (gog auth expired silently)

**Concrete fix:**
- Define lifecycle events in PIPELINE.md:
  ```
  on_agent_spawn: Log to tasks.json, set timer (max 30min for simple, 2h for complex)
  on_agent_complete: Verify output, update tasks.json, trigger next pipeline stage
  on_agent_timeout: Re-spawn once, then alert Eric
  on_auth_failure: Switch to fallback immediately, alert Eric
  on_deploy_success: Smoke test within 60s
  on_deploy_failure: Log incident, alert Eric with logs
  ```
- Until OpenClaw supports native hooks, implement via Monitor's sweep: check for state transitions rather than just current state

**Priority:** MEDIUM

---

## GAP 11: Railway Skill Doesn't Cover Full Autonomous Deployment

**Anthropic principle violated:** "Specific context in prompts (file paths, patterns, constraints)" (Source 2)

**Our specific problem:** The railway-deployment skill is excellent for **debugging** (16 sections of error→fix mappings) but doesn't provide a **complete autonomous deployment workflow** that avoids CLI auth entirely. Section 16 mentions GitHub integration but the step-by-step requires manual browser interaction ("Go to railway.app → New Project").

**Session failure it caused:** #1 (Railway deployment needed Eric to open browser for CLI auth, set variables, check deploy logs, change port in networking)

**Concrete fix:**
- Add Section 17 to railway skill: "Fully Automated Deployment Workflow (No Browser Required)"
  - Pre-requisite: Railway project already connected to GitHub repo (one-time manual setup)
  - Deployment: `git push origin main` → Railway auto-builds → verify via `curl https://app.up.railway.app/health`
  - Variables: Use Railway API with project token (stored in 1Password): `curl -X POST https://backboard.railway.app/graphql` to set variables programmatically
  - Logs: `curl` Railway API for deploy logs instead of browser
  - Networking: Document that port config is set once in Variables tab and doesn't change per deploy
- Add to DELEGATION.md Conductor section: "Railway deployment is GitHub-push only. If browser interaction is needed, that's a one-time setup task for Eric, not a per-deploy step."

**Priority:** MEDIUM

---

## GAP 12: Monitor Sweep Output Not Size-Bounded

**Anthropic principle violated:** "Context window fills fast and performance degrades — #1 constraint to manage" (Source 2)

**Our specific problem:** Monitor SKILL.md Step 11 defines a detailed status format but has no maximum output size. The sweep runs 11 steps, each producing output. When delivered via Telegram, the message exceeded Telegram's limit and **delivered nothing** (#7).

**Session failure it caused:** #7 (Monitor cron delivered nothing — Telegram message too long)

**Concrete fix:**
- Add to Monitor SKILL.md: "STATUS OUTPUT RULES:
  - Healthy sweep: Single line `✅ All systems healthy [timestamp]` (< 100 chars)
  - Degraded sweep: One line per failing check, max 5 lines, max 500 chars total
  - If detail needed: Write full report to `memory/monitor/sweep-YYYY-MM-DDTHH.md` and link it
  - NEVER exceed 4000 chars in a single Telegram message
  - If message will exceed limit: truncate to summary + `Full report: memory/monitor/sweep-[ts].md`"

**Priority:** MEDIUM

---

## GAP 13: Cron Payload Size Not Enforced

**Anthropic principle violated:** "Context window fills fast and performance degrades" (Source 2)

**Our specific problem:** PIPELINE.md says "No cron job message payload should exceed 500 tokens. Instead of embedding full instructions, have agents read their SKILL.md file for details." This is a good rule but **nothing enforces it.** The cron that triggered Monitor apparently embedded the full sweep instructions, bloating the context.

**Session failure it caused:** #7 (Monitor cron delivered nothing)

**Concrete fix:**
- Audit all existing cron jobs: list them with `openclaw` and verify each payload is under 500 tokens
- Standard cron message template: `"Run [skill_name] sweep. Read skills/[name]/SKILL.md for instructions. Report to [channel]."` (< 30 tokens)
- Monitor should check cron payloads during sweep and flag oversized ones

**Priority:** MEDIUM

---

## GAP 14: No "Start New Session" Guidance for Unrelated Tasks

**Anthropic principle violated:** "Start new sessions for unrelated tasks to avoid context bloat" (Source 2)

**Our specific problem:** AGENTS.md has "Context Hygiene" guidance about saving state when context gets heavy, but doesn't say **when to start a fresh session vs. continue the current one.** The Zero Idle Rule ("never wait, auto-start next task") actively conflicts with this — it encourages piling more work into the current context.

**Session failure it caused:** #2 (Tasks stalled for 12+ hours) — likely compounded by context bloat from multiple unrelated tasks in one session.

**Concrete fix:**
- Add to AGENTS.md Context Hygiene: "After completing any task, if the next queued task is UNRELATED (different project, different type of work), start a fresh session. Do not carry forward context from the previous task."
- Amend Zero Idle Rule: "Auto-start next task in a NEW session. The main session dispatches; subagent sessions execute."

**Priority:** MEDIUM

---

## Summary Table

| # | Gap | Anthropic Principle | Priority | Session Failure |
|---|-----|-------------------|----------|-----------------|
| 1 | No verification criteria enforcement | Verification = #1 leverage | CRITICAL | #3, #8 |
| 2 | Browser-gated auth blocks agents | Independent permissions | CRITICAL | #1, #5 |
| 3 | No token/cost budget or tracking | 15x cost, manage actively | CRITICAL | #2 |
| 4 | DELEGATION.md bloating (10KB) | Short, human-readable | HIGH | #6 (recurring) |
| 5 | No proactive status push channel | Save to files, push updates | HIGH | #7, #9 |
| 6 | No subagent permission tiers | Restricted tool access | HIGH | Preventive |
| 7 | No isolated git worktrees | Parallel in isolation | HIGH | Preventive |
| 8 | Explore-first not verified for Coder | Explore → plan → code | HIGH | #8 |
| 9 | PowerSpec routing is reactive not proactive | Independent execution | HIGH | #4 |
| 10 | No lifecycle hooks/events | Hooks for guardrails | MEDIUM | #2, #5 |
| 11 | Railway skill lacks autonomous workflow | Specific context in prompts | MEDIUM | #1 |
| 12 | Monitor output not size-bounded | Context = #1 constraint | MEDIUM | #7 |
| 13 | Cron payload size not enforced | Context management | MEDIUM | #7 |
| 14 | No fresh-session guidance | New sessions for new tasks | MEDIUM | #2 |

---

## Implementation Order (Recommended)

### Week 1 — Stop the Bleeding (CRITICALs)
1. **GAP 2:** Create AUTH_FALLBACKS.md, ban Railway CLI, add gog degraded-mode logic
2. **GAP 1:** Create DISPATCH_TEMPLATE.md, add verificationCmd to tasks.json schema
3. **GAP 3:** Add task complexity gate to PIPELINE.md, add token tracking fields

### Week 2 — Structural Improvements (HIGHs)
4. **GAP 4:** Extract auditor/conductor skills, slim DELEGATION.md to <5KB
5. **GAP 5:** Define push notification rules in Monitor
6. **GAP 9:** Embed host routing in dispatch messages
7. **GAP 8:** Add files_explored to HANDOFF.md template

### Week 3 — Hardening (HIGHs + MEDIUMs)
8. **GAP 6:** Document permission tiers per agent
9. **GAP 7:** Branch-per-agent workflow
10. **GAP 12 + 13:** Size-bound Monitor output + audit cron payloads
11. **GAP 10 + 11 + 14:** Lifecycle events, Railway autonomous workflow, session hygiene

---

## Meta-Observation

The deepest pattern across all 14 gaps: **our system documents what agents SHOULD do but doesn't verify they DID it.** Anthropic's core insight is that verification is the #1 leverage point. Every rule that exists only as text in a markdown file — without a corresponding programmatic check — is a rule that will be violated under pressure. The fix isn't more documentation. It's more verification loops.

