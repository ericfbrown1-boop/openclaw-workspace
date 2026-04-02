# Token Optimization Plan — Based on "18 Claude Code Token Hacks"
> Source: https://www.youtube.com/watch?v=49V-5Ock8LU (Apr 1, 2026)
> Analysis applied to: Jarvis agent system (OpenClaw + Claude Code agents)

## Key Insight from the Video

Claude Code's token usage is **compounding, not additive**. Message 30 costs 31x more than message 1 because the entire conversation is re-read every turn. One developer tracked 98.5% of tokens going to just re-reading history. On top of that, CLAUDE.md, MCP servers, system prompts, and skills reload every single turn.

---

## 🔴 HIGH IMPACT — Changes to Implement Immediately

### 1. Trim AGENTS.md / CLAUDE.md Files (Video: "Keep under 200 lines")
**Current state:** Our workspace loads AGENTS.md, SOUL.md, TOOLS.md, IDENTITY.md, USER.md, HEARTBEAT.md, BOOTSTRAP.md, MEMORY.md — ALL on every message. These are loaded as "Project Context" on every turn.

**Problem:** MEMORY.md alone is ~150 lines. TOOLS.md is ~115 lines. AGENTS.md is ~100 lines. USER.md is ~80 lines. That's ~500+ lines reloaded on EVERY message, including simple "yes" responses.

**Fix:**
- [ ] **MEMORY.md → convert to index file.** Replace detailed entries with one-line pointers to files in `memory/`. Example: `PowerSpec: see memory/powerspec-rebuild-guide.md` instead of 20 lines about the rebuild.
- [ ] **USER.md → trim daily tasks section.** The "Daily Tasks" section (15+ lines about cron jobs, MicroCenter checks, etc.) should move to a `memory/daily-tasks.md` file and just be referenced.
- [ ] **TOOLS.md → trim PowerSpec section.** The detailed SSH notes, network topology, and Docker services list (40+ lines) should move to `memory/powerspec-config.md`.
- [ ] **Target: <200 lines total across all project context files** that load on every turn.

**Estimated savings: 30-40% reduction in baseline per-message cost**

### 2. Disconnect Unused MCP Servers (Video: "18,000 tokens per message per server")
**Current state:** mcporter configured with 20 Zapier tools. These tool definitions load on every turn.

**Fix:**
- [ ] Audit which MCP tools are used daily vs rarely
- [ ] Disable rarely-used tools (e.g., Dropbox tools, conditional_formatting, create_column)
- [ ] Keep only: `gmail_send_email`, `find_email`, `create_draft`, `lookup_rows`, `create_row`
- [ ] Disable others and re-enable on demand

**Estimated savings: 5,000-10,000 tokens per message**

### 3. Model Tiering — Push More to Sonnet/Haiku (Video: "80% cheaper model")
**Current state (PIPELINE.md):**
- Jarvis main: Opus 4.6 ($15/$75 per M tokens)
- Planner: Opus 4.6
- All others: Sonnet 4.6 ($3/$15 per M tokens)

**Problem:** Jarvis (main) runs on Opus for ALL conversations, including simple status checks, weather queries, and emoji reactions.

**Fix:**
- [ ] **Route simple queries to Sonnet** — status checks, file reads, simple questions don't need Opus reasoning
- [ ] **Reserve Opus for:** orchestration decisions, complex planning, financial analysis, multi-step debugging
- [ ] **Add Haiku for sub-agents** — formatting, simple file operations, status summaries
- [ ] Update model tiering in PIPELINE.md to include Haiku tier

**Estimated savings: 40-60% cost reduction on routine work**

### 4. Batch Instructions (Video: "One message, multiple tasks")
**Current state:** Eric often sends multiple short messages in sequence. Each one causes full context re-read.

**Fix:**
- [ ] Jarvis should proactively say "Send me everything in one message" when multiple related requests arrive in quick succession
- [ ] When dispatching to sub-agents, batch all instructions into a single spawn message rather than multiple send() calls
- [ ] Template: instead of 5 separate tool calls, compose one comprehensive dispatch

**Estimated savings: 5-15x reduction on multi-step requests**

---

## 🟡 MEDIUM IMPACT — Structural Improvements

### 5. Aggressive Compaction Strategy (Video: "Compact at 60%, not 95%")
**Current state:** OpenClaw uses `compaction.mode: "safeguard"` — waits until context is nearly full.

**Fix:**
- [ ] Change compaction mode to trigger earlier (around 60% context)
- [ ] After 3-4 compactions in a session, save state to memory file and start fresh
- [ ] For multi-step tasks, write progress to files between steps so a fresh session can pick up

### 6. Cron Payload Trim (Video: "Shell output enters context")
**Current state:** PIPELINE.md already says "No cron job message payload should exceed 500 tokens" — but is this enforced?

**Fix:**
- [ ] Audit all cron jobs — verify payloads are under 500 tokens
- [ ] Daily briefing cron: ensure it's a trigger message, not a full instruction set
- [ ] Heartbeat: already uses HEARTBEAT_OK pattern ✅

### 7. Sub-Agent Efficiency (Video: "7-10x more tokens than single agent")
**Current state:** 9-agent system with complex delegation. Each sub-agent loads its own full context.

**Fix:**
- [ ] Apply the Task Complexity Gate more strictly — SIMPLE tasks should NEVER spawn a sub-agent
- [ ] For MODERATE tasks, use a single sub-agent with Sonnet (not Opus)
- [ ] Sub-agents should use Haiku where possible (formatting, file operations)
- [ ] Capture summarized outputs only — don't have sub-agents return full file contents
- [ ] Consider: do we really need 9 agents? Could Planner + Coder + Quality handle 90% of work?

### 8. Session Scheduling (Video: "Peak hours drain faster")
**Current state:** Work happens whenever Eric asks, plus scheduled cron jobs.

**Fix:**
- [ ] Schedule heavy sub-agent work (Docker builds, multi-file refactors) for off-peak hours (evenings/weekends)
- [ ] Keep daytime sessions for interactive work with Eric
- [ ] This maximizes the 5-hour session window utilization

---

## 🟢 LOWER IMPACT — Good Habits

### 9. Prompt Caching Awareness (Video: "5-minute cache timeout")
**Insight:** Anthropic caches unchanged context, but the cache expires after 5 minutes of inactivity. Returning after a break costs full re-processing.

**Fix:**
- [ ] Note in AGENTS.md: if a task will take >5 min of thinking (no API calls), consider breaking it into smaller pieces
- [ ] For long research tasks, keep the session warm with periodic small tool calls

### 10. Precision in File References (Video: "Send only the relevant function")
**Current state:** Agents sometimes read entire files when they only need one function.

**Fix:**
- [ ] When dispatching to sub-agents, specify exact file + line range
- [ ] Use `read --offset --limit` instead of full file reads
- [ ] In plans, reference specific functions/classes, not "look at config.py"

### 11. Use CLI Over MCP Where Possible (Video: "CLI is faster and cheaper")
**Current state:** We already use `gog` CLI for Gmail instead of MCP. Good.

**Fix:**
- [ ] Continue preferring CLI tools (gog, gh, summarize, etc.) over MCP integrations
- [ ] MCP should only be used when no CLI alternative exists

---

## 📊 Implementation Priority

| Change | Impact | Effort | Priority |
|--------|--------|--------|----------|
| Trim project context files (<200 lines) | 🔴 Very High | Low | **Do first** |
| Disconnect unused MCP tools | 🔴 High | Low | **Do first** |
| Model tiering (more Sonnet/Haiku) | 🔴 Very High | Medium | **Week 1** |
| Batch instructions | 🔴 High | Low | **Ongoing habit** |
| Earlier compaction (60%) | 🟡 Medium | Low | **Week 1** |
| Sub-agent efficiency audit | 🟡 Medium | Medium | **Week 2** |
| Cron payload audit | 🟡 Medium | Low | **Week 1** |
| Session scheduling | 🟢 Low | Low | **Ongoing** |
| Prompt cache awareness | 🟢 Low | Low | **Ongoing** |
| Precise file references | 🟢 Low | Low | **Ongoing** |

---

## 🎯 Expected Overall Savings

Conservative estimate: **40-60% reduction in token usage** from implementing the top 4 changes alone.

The biggest wins:
1. **Trimming project context** — saves tokens on EVERY single message
2. **Model tiering** — Sonnet is 5x cheaper than Opus for input, 5x cheaper for output
3. **Batching** — prevents the compounding re-read problem
4. **MCP cleanup** — eliminates invisible per-message overhead
