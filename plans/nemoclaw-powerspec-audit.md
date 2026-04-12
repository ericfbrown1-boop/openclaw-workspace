# NemoClaw PowerSpec Prototype — Auditor Report

**Date:** 2026-04-12  
**Auditor:** External Auditor Agent (Jarvis)  
**Plan reviewed:** `plans/nemoclaw-powerspec-prototype.md`  
**Research reviewed:** `plans/nemoclaw-powerspec-research.md`  
**Verdict:** **PASS_WITH_NOTES**

---

## Overall Assessment

The plan is well-structured, thorough, and shippable. Port conflicts, Telegram ownership, Docker coexistence, and rollback are all handled correctly. The architecture diagrams are clear, commands are largely copy-paste ready, and time estimates are realistic. The critical decisions (TUI-only prototype, Google OAuth deferred, Mac keeps Telegram) are sound.

However, there are several factual gaps and minor errors that should be corrected before Eric executes the plan on hardware.

---

## ✅ Correctness Checklist

| Check | Result | Notes |
|-------|:------:|-------|
| Port numbers conflict-free | ✅ PASS | 18790 for NemoClaw avoids 18789 (Mac) and all Docker ports |
| File paths correctly specified | ⚠️ NOTE | Mac paths correct; WSL2 sandbox paths are guesses (acknowledged in plan) |
| All 8 agent names correct | ✅ PASS | Verified: main/Jarvis, researcher/Researcher, planner/Planner, coder/Coder, quality/Quality, monitor/Monitor, auditor/External Auditor, conductor/Conductor |
| WSL2 Ubuntu 22.04 requirement accurate | ✅ PASS | Research confirms Linux kernel features required; WSL2 Ubuntu is the only Windows path |
| Telegram bot conflict handled | ✅ PASS | TUI-only decision is correct and safe |
| Docker service port conflicts accounted | ✅ PASS | All existing ports (8000/8001/3001/5432/5433/6379/6380/9000/9001) listed in port table, no conflicts |

---

## 🔴 Critical Blockers

**None.** The plan is executable as-is without show-stoppers.

---

## 🟡 Important Notes (Should Fix)

### 1. Skills Count Mismatch — `linkedin-carousel` Missing from Migration

**Workspace has 28 skills** (verified via `ls`). The portability matrix lists only **27 entries** — `linkedin-carousel` is missing entirely. The plan says "was in research but not in current workspace — skip if not present," but **it IS present** in the workspace.

The research report correctly identified it as portable (✅ "Content generation"). The tar command in Step 2.1 also omits it.

**Fix:** Add `linkedin-carousel` as item #28 in the portability matrix (✅ Copy as-is) and add `skills/linkedin-carousel/` to the tar command in Step 2.1. Update the summary count from "19 copy as-is" to "20 copy as-is."

### 2. OpenAI API Key Not Listed in Step 2.4

The `openclaw.json` has an `openai:default` auth profile and `gpt-5.1-codex` is configured as a model. Step 2.4 (Configure API Credentials) lists Anthropic, xAI, NVIDIA, Brave, Google Places, and ElevenLabs but **not OpenAI**.

**Fix:** Add OpenAI API key to Step 2.4, or explicitly note it's deferred for prototype (since primary models are Anthropic/xAI).

### 3. Ollama BaseURL Difference — Document the Why

Mac `openclaw.json` configures Ollama at `http://100.81.21.114:11434/v1` (Tailscale IP, since Mac reaches PowerSpec remotely). The plan correctly switches to `http://localhost:11434/v1` for NemoClaw (running locally on PowerSpec). This is correct, but the plan should add a one-line note explaining **why** the URL changes — it avoids confusion when Eric sees a different URL than the Mac config.

### 4. WSL2 Ubuntu Install Failure — No Fallback Step

The plan addresses "If `nvidia-smi` fails" and "If wizard defaulted to 18789" but **does not address what happens if `wsl --install -d Ubuntu-22.04` itself fails.** Common failures include: Windows features not enabled (Virtual Machine Platform, WSL), BIOS virtualization disabled, or distro download failure.

**Fix:** Add a troubleshooting note after Step 0.1:
```
# If install fails, ensure these Windows features are enabled:
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
# Then reboot and retry
```
Note: PowerSpec already runs Docker Desktop with WSL2 backend, so the features are almost certainly enabled. But documenting the fix costs nothing.

### 5. NemoClaw Installer URL Unverified

`curl -fsSL https://nvidia.com/nemoclaw.sh | bash` — this URL comes from the research report. If the actual URL is different (e.g., `nvidia.github.io/nemoclaw/install.sh` or something else), Phase 1 fails immediately.

**Fix:** Add a note: "Verify the current installer URL at [NVIDIA NemoClaw GitHub](https://github.com/NVIDIA/NemoClaw) before running. The URL may have changed since this plan was written."

### 6. Step 2.7 Uses `rm -rf` — Should Default to Option B

Step 2.7 "Disable Mac-Only Skills" presents Option A (`rm -rf`) and Option B (rename to `.disabled`). For a prototype where we might want to re-enable skills later, **Option B should be the default recommendation**, not Option A. The `rm -rf` inside a sandbox is low-risk, but the plan should lead with the safer option.

**Fix:** Swap Option A and B ordering, or just remove Option A and only show the rename approach.

---

## 🟢 Minor Suggestions (Nice to Have)

### 7. Mermaid Diagram Syntax — Valid

Both Mermaid diagrams (`graph TB` and `flowchart TD`) are syntactically correct and will render in GitHub/Obsidian. The arrow styles, subgraph nesting, and labels are all valid. No changes needed.

### 8. Time Estimates — Realistic

- Phase 0 (30–45 min): Reasonable. WSL2 distro install can take 10-15 min alone.
- Phase 1 (20–30 min): Reasonable if the installer works smoothly. Could take longer if GPU detection needs debugging.
- Phase 2 (45–90 min): Wide range reflects uncertainty about NemoClaw's config interface. Realistic.
- Phase 3 (30–60 min): Validation is thorough; 60 min is more likely than 30.
- Total (2.5–4 hours): Honest range. I'd plan for the upper end (4 hours).

### 9. Smoke Test Script — Add `set -o pipefail`

The smoke test script uses `set -e` but not `set -o pipefail`. Since it pipes through `grep`, a failing `curl` could be masked.

**Suggestion:** Change `set -e` to `set -euo pipefail`.

### 10. `.wslconfig` Memory Cap — Consider 48GB Instead of 64GB

The plan caps WSL2 at 64GB. With existing Docker services (~7-11 GB), Ollama (~4-8 GB), and Windows overhead, 64GB for WSL2 might lead to total memory pressure under heavy NemoClaw + GPU inference loads. 48GB would be safer while still being generous.

**Suggestion:** Optional — 64GB will work for prototype; 48GB just adds more margin for Windows services.

### 11. Cron Jobs Matrix — Matches Decisions Well

The decision to replicate only 4 crons (Task Stall Respawner, Daily Doctor, Stock Monitor, Weekly Competitor Analysis) is sound. No email-sending or Telegram-notifying crons on PowerSpec. Good.

### 12. Standard Skills Note Could Be Clearer

The plan says NemoClaw's embedded OpenClaw will include standard skills (1password, apple-notes, etc.) so no manual migration is needed. This is correct but worth noting that some standard skills are Mac-only too (e.g., `apple-notes`, `apple-reminders`, `peekaboo`, `blucli`, `imsg`). They'll be present but non-functional on WSL2.

### 13. Research Report Says 30 Skills, Workspace Has 28

The research report header says "30 Skills Found in Workspace" but lists only 28 actual entries (and the real workspace count is 28). This is a research report inaccuracy, not a plan issue. No action needed.

---

## Safety Review

| Check | Result | Notes |
|-------|:------:|-------|
| Risk to Mac OpenClaw instance | ✅ SAFE | All operations are on PowerSpec. Mac is read-only (SCP source). No Mac config changes. |
| Rollback plan sufficient | ✅ GOOD | `wsl --unregister Ubuntu-22.04` is clean nuclear option. Existing Docker services confirmed safe (different WSL distro). |
| Destructive operations warned | ⚠️ NOTE | Step 2.7 Option A uses `rm -rf` without a warning banner. Recommend leading with Option B. |
| Mac Telegram unaffected | ✅ SAFE | NemoClaw skips Telegram entirely — no token conflict possible. |
| Existing Docker containers safe | ✅ SAFE | Run in `docker-desktop` distro, not `Ubuntu-22.04`. Unregistering Ubuntu-22.04 won't touch them. |

---

## Summary

| Category | Count |
|----------|-------|
| 🔴 Critical Blockers | 0 |
| 🟡 Important Notes | 6 |
| 🟢 Minor Suggestions | 7 |

**Verdict: PASS_WITH_NOTES** — The plan is shippable as-is. Eric can execute it safely. The 6 important notes should ideally be incorporated before execution (especially #1 and #4), but none are blockers. The plan demonstrates solid engineering judgment on port allocation, Telegram conflict avoidance, rollback safety, and phased validation.

---

*Audit complete. Plan is approved for execution with noted items.*
