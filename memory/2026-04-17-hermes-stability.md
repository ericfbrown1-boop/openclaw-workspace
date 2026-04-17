# Session: 2026-04-17 15:53:07 UTC

- **Session Key**: agent:main:telegram:direct:5387843769
- **Session ID**: cd4c5d78-c85b-41bd-9b8f-06498f1509e2
- **Source**: telegram

## Conversation Summary

user: Conversation info (untrusted metadata):
```json
{
  "chat_id": "telegram:5387843769",
  "message_id": "6024",
  "sender_id": "5387843769",
  "sender": "Eric Brown",
  "timestamp": "Fri 2026-04-17 08:48 PDT"
}
```

Sender (untrusted metadata):
```json
{
  "label": "Eric Brown (5387843769)",
  "id": "5387843769",
  "name": "Eric Brown",
  "username": "eric_1252"
}
```

I want you to Research best practices from highly rated sources to figure out best practices for using Hermes with OpenClaw to provide maximum stability and reliability

[Bootstrap truncation warning]
Some workspace bootstrap files were truncated before injection.
Treat Project Context as partial and read the relevant files directly if details seem missing.
- AGENTS.md: 16838 raw -> 10909 injected (~35% removed; max/file).
- MEMORY.md: 13609 raw -> 10909 injected (~20% removed; max/file).
- If unintentional, raise agents.defaults.bootstrapMaxChars and/or agents.defaults.bootstrapTotalMaxChars.
assistant: 

I'll research Hermes + OpenClaw best practices. Let me start by checking local docs and then searching for high-quality sources.
assistant: Good finds. Let me dig deeper into the most relevant sources — especially the Hongkiat setup guide and the comparison articles.
assistant: Good — the Hongkiat guide had great content. Let me get more sources.
assistant: Excellent data. Let me get the key practical article and the official Hermes docs on supervisor setup.
assistant: Now let me check the official Hermes docs and the Hermes GitHub for the latest features:
assistant: I now have comprehensive data from multiple high-quality sources. Let me compile this into a thorough briefing for you.

Eric, here's what I found from the best sources — official Hermes docs, Hongkiat, NxCode, ChatGPT.ca's supervisor guide, and a detailed practitioner blog (mejba.me). This is actionable, not theory.

---

## Hermes + OpenClaw: Best Practices for Maximum Stability & Reliability

### The Core Concept

The pairing works because of complementary architectures:
- **OpenClaw** = gateway-first (execution, scheduling, multi-channel messaging, skill orchestration)
- **Hermes** = agent-first (learning loop, persistent memory, self-improving skills, supervision)

The ideal split: **OpenClaw does the work. Hermes watches, reviews, learns, and heals.**

---

### 🏗️ Architecture Pattern: Three Proven Approaches

**1. Chat-Based Supervision (Simplest)**
Both agents in a shared Telegram/Discord channel. Hermes monitors OpenClaw's outputs using an intent marker protocol:
- `[STATUS_REQUEST]` → Hermes asks OpenClaw for status
- `[REVIEW_REQUEST]` → OpenClaw submits output for review
- `[ESCALATION_NOTICE]` → Hermes alerts human
- `[ACK]` → Terminal, loop closed

**Critical rule:** Max 3 messages per exchange. `[ACK]` is always terminal. This prevents infinite ping-pong loops.

**2. Programmatic Control via MCP/API (Tightest integration)**
Hermes runs with `--mcp` enabled and calls OpenClaw directly via its API/gateway. Better for automation-heavy setups.

**3. Mutual Health Monitor (Highest reliability)**
Both agents monitor each other's health. If OpenClaw crashes, Hermes restarts it. If Hermes crashes, OpenClaw recovers it. **Zero single points of failure.**

---

### 🔄 The Self-Healing Workflow (Your Biggest Win)

This is the killer feature for us. One practitioner reported going from 15-minute manual recovery to **11-second automatic recovery**:

1. Hermes pings OpenClaw's process every **30 seconds** (lighter than you'd think — barely any token cost)
2. **3 consecutive failures** before escalation (avoids false alarms)
3. On failure: read error logs → classify failure type → apply fix from learned repair patterns → restart → notify via Telegram
4. **Hermes's learning loop means recovery gets faster over time** — first fix took 40 seconds, third time took 11 seconds because it had cataloged the pattern

We already have a self-heal infrastructure — Hermes would add an **intelligent** layer on top that learns from each incident.

---

### 💰 Cost Optimization

**Key insight:** Run Hermes on a cheap model (Haiku or ChatGPT) for supervision/monitoring. Keep OpenClaw on Opus for planning/reasoning.

Typical dual-agent setup costs:
- Hermes supervisor on Haiku: **$0.25-$1/day**
- OpenClaw on Opus: stays the same as now
- The supervision layer pays for itself many times over in avoided downtime

One user reported **40% lower total AI spend** after switching from all-Opus to the supervisor-builder pattern (Opus plans, cheap model executes, Opus reviews).

---

### 🛡️ Security Considerations

**Hermes has a significantly better security posture:**
- Zero agent-specific CVEs (vs OpenClaw's 9 CVEs in March 2026)
- Self-generated skills (no supply chain attack risk from ClawHub marketplace)
- Container hardening + namespace isolation for subagents
- Credential rotation via pluggable memory providers (v0.7.0+)

**For our setup:** Hermes would add a security oversight layer without introducing new attack surface.

---

### 📋 Recommended Implementation for Our Setup

**Phase 1: Install + Supervisor Profile**
```
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
hermes setup
hermes profile create supervisor
```

**Phase 2: Health Monitor (Immediate Value)**
- Hermes monitors OpenClaw gateway health every 30 seconds
- Auto-recovery on crash with log diagnosis
- Telegram notification on every incident + fix

**Phase 3: Quality Review Loop**
- Hermes reviews OpenClaw's daily briefing output before delivery
- Checks for stale data, repetitive content, quality scores
- Escalates only genuine issues

**Phase 4: Skill Synthesis**
- Hermes learns from repeated patterns (like our recurring OAuth issues, gateway restart sequences)
- Auto-generates reusable skills from successful problem resolutions
- Gets measurably better over time

---

### ⚠️ Key Gotchas from the Community

1. **Don't set health checks below 30 seconds** — token cost adds up with no benefit
2. **Migration confusion** — if Hermes behaves like OpenClaw after `hermes claw migrate`, reset the profile
3. **Resource usage** — Hermes can get heavy during active learning; monitor RAM
4. **Run as systemd service** in production for crash recovery of Hermes itself
5. **Separate profiles** — always use `hermes -p supervisor` to keep oversight separate from other Hermes work
6. **Hermes doesn't do multi-agent comms as well as OpenClaw** — keep OpenClaw as the primary for our agent orchestration (Auditor, RCA, etc.)

---

### Bottom Line

This is essentially what we've been building manually with our self-heal infrastructure, Auditor, and RCA agent — but Hermes adds a **learning loop** that gets smarter over time. The mutual health monitoring pattern is the immediate win. The skill synthesis is the long-term compounding value.

Want me to set this up? I'd start with installing Hermes in supervisor mode and wiring it to monitor our gateway health. We'd keep our existing OpenClaw setup exactly as-is — Hermes just adds the oversight layer.
user: Conversation info (untrusted metadata):
```json
{
  "chat_id": "telegram:5387843769",
  "message_id": "6035",
  "sender_id": "5387843769",
  "sender": "Eric Brown",
  "timestamp": "Fri 2026-04-17 08:50 PDT"
}
```

Sender (untrusted metadata):
```json
{
  "label": "Eric Brown (5387843769)",
  "id": "5387843769",
  "name": "Eric Brown",
  "username": "eric_1252"
}
```

Store everything we just learned with Librarian first
assistant: Good — I see how the librarian works. Let me store the Hermes research as a comprehensive win entry plus a pattern file.
assistant: Now let me create a cross-cutting pattern file and update the index:
assistant: Now let me also store this in today's memory file for continuity:
assistant: Let me verify everything is stored properly:
assistant: All stored. Here's what's in the Librarian now:

**Win entry:** `RESEARCH-20260417-hermes-openclaw-best-practices.json` — 10.4KB comprehensive research with all sources, architecture patterns, implementation roadmap, cost analysis, security comparison, gotchas, and command reference.

**Pattern:** `hermes-openclaw-dual-agent-stability.json` — Cross-cutting pattern with the 10 key rules for dual-agent stability.

**Today's memory:** Updated with full summary + pointers to both files.

**Index:** Regenerated with 17 total wins.

Everything's persisted — any future agent session can query the Librarian and get the full Hermes playbook without re-researching. What's next?
