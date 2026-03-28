---
name: auditor
description: >
  External Auditor standing instructions. 6-step QA gate (pull+build, smoke test,
  dashboard integrity, deliverable verification, regression, sign-off). Daily vibe
  coding vulnerability scan. Weekly Claude best practices audit.
---

# External Auditor Skill — Standing Instructions

## Anthropic Code Review & Best Practices

**Anthropic Code Review Check:** On every audit, verify that Anthropic's Code Review feature (launched Mar 2026 — multi-agent PR review) is enabled on all active GitHub repos. If not enabled, flag it and recommend setup. This supplements our Quality Part B security audit with Anthropic's own PR review agents.

**Daily Vibe Coding Vulnerability Scan (standing instruction):**
Every day at 8AM PT, the External Auditor must:
1. Search for the latest news on vibe coding vulnerabilities, supply chain attacks, and AI-generated code risks:
   - Search: "vibe coding vulnerability 2026", "LiteLLM vulnerability", "AI code generation security risk"
   - Check: CVE databases, Hacker News, security blogs (Snyk, Socket.dev, GitHub Security Blog)
   - Look for: dependency confusion attacks, malicious packages, prompt injection in code gen, backdoors in AI-suggested code
2. Scan ALL project repos for known vulnerable dependencies:
   - `cd ~/JarvisMissionControl && npm audit`
   - `cd ~/ProjectScraper && npm audit`
   - `cd ~/ContractAnalyzer && pip audit` (if pip-audit installed) or `safety check`
   - `cd ~/.openclaw/workspace && gh api repos/ericfbrown1-boop/JarvisMissionControl/vulnerability-alerts --jq '.[].security_advisory.summary'`
   - Check Dependabot alerts on all GitHub repos
3. Scan for hardcoded secrets or suspicious patterns:
   - `grep -r "api_key\|secret\|password\|token" --include="*.js" --include="*.ts" --include="*.py" ~/JarvisMissionControl ~/ProjectScraper ~/ContractAnalyzer | grep -v node_modules | grep -v .git`
4. Produce a brief report:
   - If vulnerabilities found → alert Eric immediately via Telegram with severity + fix instructions
   - If clean → log "✅ Daily security scan clean" in `memory/YYYY-MM-DD.md`
   - If a new vibe coding attack pattern is discovered → update INCIDENTS.md lessons learned table

**Weekly Claude Best Practices Audit (standing instruction):**
Every Monday, the External Auditor must:
1. Fetch the latest Claude/Claude Code best practices from Anthropic's official docs:
   - https://docs.anthropic.com/en/docs/claude-code/overview
   - https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering
   - https://docs.anthropic.com/en/docs/build-with-claude/agentic-tool-use
   - https://docs.anthropic.com/en/docs/claude-code/best-practices
   - Search for any new Anthropic blog posts or changelog entries from the past 7 days
2. Compare findings against ALL current agent configuration files:
   - `AGENTS.md`, `DELEGATION.md`, `PIPELINE.md`, `POWERSPEC.md`, `INCIDENTS.md`
   - `skills/monitor/SKILL.md`, `skills/remote-coder/SKILL.md`
   - Any per-agent workspace AGENTS.md files under `~/.openclaw/agents/*/agent/`
3. Produce a report at `plans/claude-best-practices-audit.md` with:
   - New/changed Anthropic recommendations found
   - Current agent files that conflict with or miss these recommendations
   - Specific suggested changes (with before/after diffs where helpful)
   - Priority ranking (critical alignment gaps vs nice-to-haves)
4. Send the report to Eric via Telegram for review + approval
5. Do NOT apply changes until Eric approves — this is a review gate, not auto-update
6. After Eric approves, implement changes, commit to GitHub, and update the lessons table in Monitor SKILL.md

## 🔴 Silent Failure Audit (Standing Addition 2026-03-27)
**Origin:** FinancialReportApp RCA — 3 reports shipped with "done" status but empty content.

**On EVERY audit, add this 7th step to the QA gate:**

### Step 7: Output Quality Verification
For any pipeline that produces a deliverable (report, email, dashboard):
1. **Open the actual output file** — don't trust status codes alone
2. **Verify content is real** — not placeholder text, not "not available," not empty sections
3. **Check for silent parser failures** — look for `_parseError`, fallback dicts, truncated values in logs
4. **Verify env vars inside containers** — `docker exec <container> env | grep KEY` to confirm values match expected length/format
5. **Test the parser separately** — give it known-good input and verify output shape matches what downstream consumers expect

**Auto-fail triggers:**
- Deliverable contains >3 instances of "not available" or "not found"
- .docx report executive summary is <100 characters
- API key env var inside container is <80 characters
- JSON parser returns a dict with `_parseError: True` and nobody caught it
- Status endpoint says "done" but output is defaults

**Log format for this step:**
```
Step 7 — Output Quality: ✅ PASS / ❌ FAIL
  - Content length: XXX chars
  - Placeholder count: N
  - Env vars verified: KEY1 ✅ (108 chars), KEY2 ✅ (95 chars)
  - Parser health: No _parseError in logs
```
