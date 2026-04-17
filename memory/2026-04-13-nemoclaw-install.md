# Session: 2026-04-13 13:33:43 UTC

- **Session Key**: agent:main:main
- **Session ID**: b70e4c71-6acd-4fcc-a353-c4751904adac
- **Source**: webchat

## Conversation Summary

assistant: This is exactly what I needed. Critical finding: NemoClaw is **alpha software** (released March 16, 2026) with a known WSL2/GPU bug on Windows. I have the workaround. Let me write the complete installation guide:
assistant: Committed (`69ca4f5`). Here's your battle plan for today:

---

## 🚀 NemoClaw Prototype — What To Do Right Now

**Good news and a heads-up:**

NemoClaw is **free to download** — no paid license needed for the prototype. It's an open-source reference stack from NVIDIA (alpha since March 16, 2026). You just need a free NVIDIA API key from `build.nvidia.com`. The corporate enterprise license is only needed for the production Ajax deployment with SOC 2 features.

**One critical gotcha on Windows/WSL2:** The standard `nemoclaw onboard` command **silently fails** with NVIDIA GPUs in WSL2 due to a k3s GPU passthrough bug. We have the exact workaround — skip that command entirely and use the manual path instead. Takes the same amount of time but actually works.

### Your 35-45 minute sequence today on PowerSpec:

1. **Browser** → `build.nvidia.com/nemoclaw` → sign in → get `nvapi-...` key *(5 min)*
2. **Open WSL2 Ubuntu** on PowerSpec (via RDP or I can do it via SSH)
3. **Run Steps 3-10** from the guide at `plans/project-ajax-install-guide.md` — I'll paste each command as you go if you want to work through it together
4. **Smoke test:** ask NemoClaw "what files can you see?" — if it only sees sandbox files, OpenShell isolation is confirmed working
5. **Message me** "NemoClaw is running" → I immediately migrate the Jarvis config in, wire up Claude + CIC, and you have Jarvis NemoClaw V0.1

**Want me to walk you through it step by step as you go, or do you prefer to follow the guide and ping me when you hit a step?**

The full guide is saved at:
`~/.openclaw/workspace/plans/project-ajax-install-guide.md`
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Sun 2026-04-12 07:24 PDT] Ajax will also have access to Grok and Open AI ia API keys so for example, in my coding system I use different LLM models for different agents; all that strucutre has to be preserved. Assume I will have all the API keys needed for this.
assistant: Good — that's actually the right call. The multi-model architecture we already have (Opus for planning, Grok for adversarial review, Sonnet for execution) transfers directly to Ajax. I just need to make sure the model tiering config survives the migration intact.
assistant: Now update the install guide and Ajax plan with the multi-model architecture, and add the NemoClaw provider config for all three:
assistant: Committed (`dce213a`). Here's the important clarification on how the multi-model stack works with NemoClaw:

---

## 🧠 Multi-Model Stack on Ajax — Nothing Changes

NemoClaw is the **security sandbox layer only** — it wraps OpenClaw in OpenShell isolation. The LLM routing, agent-to-model assignments, and fallback chains all carry over exactly as-is.

The one thing that changes is **where the API keys live** — they move from shell environment variables into OpenShell's provider registry (so they're managed inside the sandbox security boundary rather than exposed in your shell):

```
OpenShell providers on Ajax:
  anthropic  →  Claude Opus/Sonnet (Jarvis, Planner, Coder...)
  xai        →  Grok 4 (adversarial review, Quality, Auditor)
  openai     →  OpenAI (fallback, specific tasks)
  nvidia-nim →  Nemotron 3 Super (local GPU inference, fast tasks)
```

Same tiering as today — Opus for orchestration, Grok for adversarial review, Sonnet for execution agents, Nemotron as the new fast/cheap local option that costs nothing per-call since it runs on Ajax's own GPUs.

### What you have on Ajax that you don't have today:
- **Nemotron 3 Super on local GPU** — effectively free inference for high-volume tasks (monitoring sweeps, log analysis, PII checks) that currently burn API budget
- **1M token context on Grok** runs even better when you're not routing through Tailscale
- **OpenShell security boundary** — even if one agent gets a bad prompt injection, it can't escape the sandbox to touch your Cohesity systems

---

**Ready whenever you want to start the install.** Just open WSL2 on PowerSpec and go to `build.nvidia.com/nemoclaw` to grab the API key — that's the first step. I'll be right here to walk you through each command.
user: Pre-compaction memory flush. Store durable memories only in memory/2026-04-12.md (create memory/ if needed). Treat workspace bootstrap/reference files such as MEMORY.md, DREAMS.md, SOUL.md, TOOLS.md, and AGENTS.md as read-only during this flush; never overwrite, replace, or edit them. If memory/2026-04-12.md already exists, APPEND new content only and do not overwrite existing entries. Do NOT create timestamped variant files (e.g., 2026-04-12-HHMM.md); always use the canonical 2026-04-12.md filename. If nothing to store, reply with NO_REPLY.
Current time: Sunday, April 12th, 2026 - 7:26 AM (America/Los_Angeles) / 2026-04-12 14:26 UTC
user: Pre-compaction memory flush. Store durable memories only in memory/2026-04-12.md (create memory/ if needed). Treat workspace bootstrap/reference files such as MEMORY.md, DREAMS.md, SOUL.md, TOOLS.md, and AGENTS.md as read-only during this flush; never overwrite, replace, or edit them. If memory/2026-04-12.md already exists, APPEND new content only and do not overwrite existing entries. Do NOT create timestamped variant files (e.g., 2026-04-12-HHMM.md); always use the canonical 2026-04-12.md filename. If nothing to store, reply with NO_REPLY.
Current time: Sunday, April 12th, 2026 - 7:26 AM (America/Los_Angeles) / 2026-04-12 14:26 UTC
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Sun 2026-04-12 07:26 PDT] why is this context window only 200 K tokens? can we switch to Opus 4.6 or should we compact our discussion ?
user: Pre-compaction memory flush. Store durable memories only in memory/2026-04-12.md (create memory/ if needed). Treat workspace bootstrap/reference files such as MEMORY.md, DREAMS.md, SOUL.md, TOOLS.md, and AGENTS.md as read-only during this flush; never overwrite, replace, or edit them. If memory/2026-04-12.md already exists, APPEND new content only and do not overwrite existing entries. Do NOT create timestamped variant files (e.g., 2026-04-12-HHMM.md); always use the canonical 2026-04-12.md filename. If nothing to store, reply with NO_REPLY.
Current time: Sunday, April 12th, 2026 - 8:03 AM (America/Los_Angeles) / 2026-04-12 15:03 UTC
user: Pre-compaction memory flush. Store durable memories only in memory/2026-04-12.md (create memory/ if needed). Treat workspace bootstrap/reference files such as MEMORY.md, DREAMS.md, SOUL.md, TOOLS.md, and AGENTS.md as read-only during this flush; never overwrite, replace, or edit them. If memory/2026-04-12.md already exists, APPEND new content only and do not overwrite existing entries. Do NOT create timestamped variant files (e.g., 2026-04-12-HHMM.md); always use the canonical 2026-04-12.md filename. If nothing to store, reply with NO_REPLY.
Current time: Sunday, April 12th, 2026 - 8:03 AM (America/Los_Angeles) / 2026-04-12 15:03 UTC
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Sun 2026-04-12 08:03 PDT] did you stall; what are next steps?
user: Pre-compaction memory flush. Store durable memories only in memory/2026-04-12.md (create memory/ if needed). Treat workspace bootstrap/reference files such as MEMORY.md, DREAMS.md, SOUL.md, TOOLS.md, and AGENTS.md as read-only during this flush; never overwrite, replace, or edit them. If memory/2026-04-12.md already exists, APPEND new content only and do not overwrite existing entries. Do NOT create timestamped variant files (e.g., 2026-04-12-HHMM.md); always use the canonical 2026-04-12.md filename. If nothing to store, reply with NO_REPLY.
Current time: Sunday, April 12th, 2026 - 8:39 AM (America/Los_Angeles) / 2026-04-12 15:39 UTC
user: Pre-compaction memory flush. Store durable memories only in memory/2026-04-12.md (create memory/ if needed). Treat workspace bootstrap/reference files such as MEMORY.md, DREAMS.md, SOUL.md, TOOLS.md, and AGENTS.md as read-only during this flush; never overwrite, replace, or edit them. If memory/2026-04-12.md already exists, APPEND new content only and do not overwrite existing entries. Do NOT create timestamped variant files (e.g., 2026-04-12-HHMM.md); always use the canonical 2026-04-12.md filename. If nothing to store, reply with NO_REPLY.
Current time: Sunday, April 12th, 2026 - 8:39 AM (America/Los_Angeles) / 2026-04-12 15:39 UTC
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Sun 2026-04-12 08:39 PDT] status?
