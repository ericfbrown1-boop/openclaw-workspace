# Claude Code Best Practices Audit — 2026-03-24

**Auditor:** External Auditor Agent
**Sources:** Anthropic official docs (code.claude.com/docs/en/best-practices), Anthropic blog (claude.com/blog/code-review, Mar 2026), CLAUDE.md best practices guide (TurboDocx, Mar 2026)
**Status:** AWAITING ERIC'S APPROVAL — no changes applied yet

---

## Key Anthropic Recommendations (current as of March 2026)

### 1. Context Window Management Is #1 Priority
> "Most best practices are based on one constraint: Claude's context window fills up fast, and performance degrades as it fills."

**Our alignment:** ✅ GOOD — We just split AGENTS.md from 37KB into 5 focused files. But some agent prompts (Monitor cron message, daily briefing cron) are still very long and may consume unnecessary context.

**Suggested changes:**
- Trim cron job prompt messages to essentials; have agents read SKILL.md files for details instead of embedding full instructions in the cron message
- Add a standing rule: no cron message payload >500 tokens

### 2. "Give Claude a Way to Verify Its Work" — Anthropic's #1 Recommendation
> "This is the single highest-leverage thing you can do. Include tests, screenshots, or expected outputs so Claude can check itself."

**Our alignment:** ⚠️ GAP — Our pipeline has a Tester agent but:
- No test suites exist yet (Step 6 is still queued)
- Coder agent doesn't have explicit "run tests after every change" in its instructions
- External Auditor's smoke test is manual (click through UI) rather than automated

**Suggested changes:**
- **DELEGATION.md → Coder:** Add: "After every code change, run the project's test suite. If no tests exist, write at least one smoke test before creating HANDOFF.md."
- **DELEGATION.md → Tester:** Add: "Every project must have at least a basic test suite (health endpoint check, lint pass) before it can proceed to Quality."
- **PIPELINE.md:** Add verification criteria to the pipeline: "Every task dispatch must include success criteria that the agent can verify programmatically."

### 3. "Explore First, Then Plan, Then Code" — 4-Phase Workflow
> Anthropic recommends: Explore → Plan → Implement → Commit

**Our alignment:** ✅ MOSTLY GOOD — Our pipeline is: Planner → Coder → Tester → Quality → Auditor → Conductor. But:
- Planner doesn't have an explicit "Explore" phase where it reads files before planning
- Coder sometimes jumps to implementation without reading existing code patterns

**Suggested changes:**
- **DELEGATION.md → Planner:** Add Phase 0: "Before creating PLAN.md, Planner must read the existing codebase structure (`find . -type f | head -50`, key files) and understand current patterns. Do not plan in a vacuum."
- **DELEGATION.md → Coder:** Add: "Before writing any new code, read at least 3 existing files in the project to understand patterns, conventions, and style. Reference existing patterns in your implementation."

### 4. "Provide Specific Context in Prompts"
> "Reference specific files, mention constraints, and point to example patterns."

**Our alignment:** ⚠️ GAP — When Jarvis spawns agents, the task descriptions are sometimes vague ("implement Docker config") instead of specific ("update `/JarvisMissionControl/Dockerfile` to add backend service using the pattern in `docker-compose.yml`").

**Suggested changes:**
- **DELEGATION.md → Jarvis (global rule):** Add: "When dispatching work to any agent, always include: (a) specific file paths, (b) example patterns to follow, (c) explicit success criteria the agent can verify."

### 5. "Write an Effective CLAUDE.md" — Keep It Short
> "Run /init to generate a starter CLAUDE.md. Keep it short and human-readable."

**Our alignment:** ⚠️ GAP — We use AGENTS.md as the equivalent of CLAUDE.md, but:
- We don't have project-specific CLAUDE.md files in JarvisMissionControl, ProjectScraper, or ContractAnalyzer
- The Dropbox docs reference separate workspace-*/AGENTS.md files per agent, but our current setup has everything in the main workspace

**Suggested changes:**
- Create a `CLAUDE.md` in each project repo (JarvisMissionControl, ProjectScraper, ContractAnalyzer) with project-specific build commands, test commands, and code style rules
- Keep these under 2KB each — just the essentials

### 6. Code Review — Anthropic's New Feature (Mar 2026)
> "Today we're introducing Code Review, which dispatches a team of agents on every PR to catch the bugs that skims miss, built for depth, not speed."

**Our alignment:** ❌ NOT USING — Anthropic now offers automated multi-agent code review on PRs. Our Quality agent does security audits but we're not using Anthropic's built-in Code Review.

**Suggested changes:**
- Investigate enabling Anthropic's Code Review on our GitHub repos
- This could replace or supplement our Quality Part B security audit
- Add to External Auditor's weekly check: "Is Anthropic Code Review enabled on all active repos?"

### 7. Context Management: Reduce Token Usage
> "Use subagents for parallel tasks. Start new sessions for unrelated tasks."

**Our alignment:** ⚠️ PARTIAL — We use subagents but often keep everything in the main session, which bloats context. The main session conversation regularly exceeds 100K tokens.

**Suggested changes:**
- **PIPELINE.md:** Add: "Each pipeline stage should run in an isolated session (already enforced by OpenClaw's agent spawning). Main session should orchestrate, not execute."
- **AGENTS.md:** Add: "When context gets heavy (compaction warnings), proactively save state to files and start fresh rather than dragging a massive conversation forward."

---

## Summary: Priority-Ranked Changes

### Critical (alignment gaps that cause real failures)
1. **Coder must run tests after every change** — Anthropic's #1 recommendation, we're not doing it
2. **Task dispatches need specific file paths + success criteria** — vague prompts waste context and produce wrong results
3. **Create project-specific CLAUDE.md files** — each repo needs its own build/test/style reference

### High (significant improvements)
4. **Planner needs an Explore phase** before planning — read existing code first
5. **Trim cron message payloads** — long prompts waste context; have agents read SKILL.md instead
6. **Investigate Anthropic Code Review** for PR automation

### Medium (nice-to-haves)
7. **Coder should read existing patterns** before writing new code
8. **Context hygiene rule** — save state to files when context gets heavy
9. **Every project needs at least a basic test suite** before proceeding to Quality

---

**AWAITING APPROVAL:** Eric, review the above and let me know which changes to implement. I will not modify any files until you approve.
