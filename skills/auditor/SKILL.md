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
