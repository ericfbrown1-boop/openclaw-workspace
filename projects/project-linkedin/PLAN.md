# Project LinkedIn — PLAN.md

## Decision: Skill-based (no separate script)

**Why:** Jarvis already has access to Claude (text polish), HTTP tools (DALL-E API), Telegram delivery, and file I/O. A skill file gives Jarvis standing instructions to execute the full workflow using existing tools — no Python script maintenance, no dependency management, no virtual env setup. The carousel skill already follows this pattern successfully.

A standalone script would only be justified if we needed cron/batch execution without Jarvis. We don't — Eric always triggers this conversationally.

---

## Architecture

```
Eric sends draft (Telegram/direct) 
  → Jarvis detects trigger phrase
  → Step 1: Polish text (Claude Opus 4.6 self-prompt)
  → Step 2: Generate image prompt from polished text
  → Step 3: Call DALL-E 3 API (1792x1024 → crop to 1200x627)
  → Step 4: Save image to ~/Documents/linkedin-graphics/
  → Step 5: Deliver polished text + image via Telegram
```

## Implementation Steps

### 1. Create SKILL.md ✅
`~/.openclaw/workspace/skills/project-linkedin/SKILL.md`
- Trigger phrases
- Text polish prompt template (preserves Eric's voice)
- DALL-E 3 API call spec (model, size, prompt engineering)
- Image post-processing (resize to 1200x627)
- Delivery instructions (Telegram text + image attachment)

### 2. Create output directory
```bash
mkdir -p ~/Documents/linkedin-graphics
```

### 3. Validate OpenAI key works
Test DALL-E 3 endpoint with a simple prompt to confirm key + quota.

### 4. Test end-to-end
Run with a sample draft post, verify:
- Text polish quality
- Image generation + correct dimensions
- Telegram delivery (text + image)
- Turnaround < 3 min

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Implementation | Skill (no script) | Jarvis has all needed tools; less maintenance |
| Text polish | Claude Opus 4.6 | Already available, best quality |
| Image gen | DALL-E 3 API | Simpler than SD on PowerSpec, good quality |
| Image size | Request 1792x1024, crop to 1200x627 | DALL-E doesn't support exact 1200x627; closest landscape is 1792x1024 |
| Image crop | Python one-liner via exec | `PIL` center-crop, no script file needed |
| Fallback | Stable Diffusion on PowerSpec | Only if DALL-E quota/key fails |
| Delivery | Telegram text + image attachment | Eric's preferred channel |

## Risk Mitigations

- **DALL-E rate limit:** Cache the prompt; retry once after 30s. If still failing, fall back to a stock gradient with text overlay via PIL.
- **Image dimensions:** DALL-E 3 only supports 1024x1024, 1024x1792, 1792x1024. We request 1792x1024 and center-crop to 1200x627.
- **Voice drift:** The polish prompt explicitly instructs "preserve Eric's voice" with examples of his actual style markers.

## Timeline
- SKILL.md: now (this session)
- Directory setup + validation: next Jarvis session
- First live run: when Eric sends next LinkedIn draft

## Created
2026-04-15
