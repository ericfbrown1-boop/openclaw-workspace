---
name: auditor
description: >
  External Auditor standing instructions. 6-step QA gate (pull+build, smoke test,
  dashboard integrity, deliverable verification, regression, sign-off). Daily vibe
  coding vulnerability scan. Weekly Claude best practices audit.
---

# External Auditor Skill — Standing Instructions

## 🔴 DUAL-AGENT RCA PROTOCOL (Standing Rule — 2026-04-13)

**When Auditor is spawned for an RCA, RCA Agent (GPT-5.4) is ALWAYS spawned simultaneously.**

See `skills/rca-agent/SKILL.md` for full protocol. Summary:
1. **Phase 0 (MANDATORY FIRST):** Collect ALL logs before forming any hypothesis — gateway.log, openclaw.log, PM2 logs, docker logs, system log, incidents.jsonl, today's memory file
2. **Phase 1:** Auditor analyzes from logs + internals. RCA Agent researches independently online.
3. **Phase 2:** Agents debate — Auditor writes to RCA file, RCA Agent challenges or confirms with external sources
4. **Phase 3:** Joint fix plan — autonomous execution, no Eric involvement
5. **Phase 4:** Verify fix worked with concrete tests, notify Eric with results

**Log collection commands (run FIRST, share with both agents):**
```bash
tail -200 ~/.openclaw/logs/gateway.log 2>/dev/null
grep -i "error\|warn\|timeout\|lock\|SIGTERM\|fail" ~/.openclaw/logs/gateway.log | tail -50
openclaw status 2>&1
openclaw tasks maintenance 2>&1 | head -20
tail -20 ~/.openclaw/workspace/memory/incidents.jsonl 2>/dev/null
cat ~/.openclaw/workspace/memory/$(date +%Y-%m-%d).md 2>/dev/null | tail -30
```

---

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

---

## 🔴 Unauthorized Config Mutation Check (Standing Rule — INC-20260417-001)

**Origin:** Jarvis stored a Gemini API key to `openclaw.json` without being asked, using the wrong schema, breaking the config. Eric did not request Gemini and does not use it.

**On EVERY audit sweep and after EVERY agent session, verify:**

```bash
# 1. Config must be valid
openclaw status 2>&1 | grep -i "config invalid\|validation failed\|Unrecognized key" && echo "❌ CONFIG BROKEN" || echo "✅ Config valid"

# 2. auth.profiles must only contain approved providers
python3 -c "
import json
with open('/Users/ericbrown/.openclaw/openclaw.json') as f:
    cfg = json.load(f)
profiles = cfg.get('auth', {}).get('profiles', {})
approved = {'anthropic:default', 'openai:default', 'xai:default', 'grokheavy:default'}
unauthorized = set(profiles.keys()) - approved
if unauthorized:
    print(f'❌ UNAUTHORIZED PROFILES: {unauthorized}')
else:
    print(f'✅ Auth profiles clean: {list(profiles.keys())}')
"

# 3. Run openclaw doctor to catch schema violations
openclaw doctor 2>&1 | grep -i "error\|invalid\|fail" | head -10
```

**Auto-fail triggers:**
- Any auth profile not in: `anthropic:default`, `openai:default`, `xai:default`, `grokheavy:default`
- Config validation fails on `openclaw status`
- Any key written to openclaw.json that Eric did not explicitly request

**If unauthorized profile found:**
1. Remove it immediately: edit `openclaw.json`, delete the unauthorized entry
2. Run `openclaw doctor --fix`
3. Alert Eric: "Found unauthorized credential `<name>` in openclaw.json — removed. Source: [agent/cron that added it]"
4. Log to `memory/incidents.jsonl` with `error_category: "unauthorized_config_mutation"`

**Standing rule for ALL agents:**
- NEVER write credentials to `openclaw.json` unless Eric explicitly said "store X key"
- ALWAYS use `openclaw config set` CLI (not direct JSON edit) for any config changes
- If a screenshot/doc contains multiple API keys, only store the one explicitly requested
