# AUTH_FALLBACKS.md — Credential Expiry Handling
> **L1:** What to do when auth breaks. gog→Zapier MCP, gh→pause+alert, Railway CLI banned (git push only), Dropbox auto-refresh. Model fallback chain: Opus→Grok 4.20 Beta→Sonnet.

**No agent may stall because of expired credentials. Every auth has an automated fallback.**

## Credentials & Fallback Paths

| Credential | Expiry | Auto-Renew | Manual Renew | Fallback When Down |
|-----------|--------|------------|--------------|-------------------|
| gog (Google OAuth) | **NEVER** (fixed 2026-03-26) | `gog auth add --force-consent` (needs browser) | Eric runs in Terminal | Switch to Zapier MCP (`mcporter call zapier.gmail_send_email`) for email; skip calendar/drive tasks |

> **PERMANENT FIX APPLIED:** Google Cloud project `672907822296` (EFB Calendar Clawdbot) changed from Testing → **In Production** on 2026-03-26. Refresh tokens now never expire (only if unused 6 months or password change). The 7-day expiry was caused by Google's Testing mode policy, NOT a gog bug.
| gh (GitHub) | Token-based | `gh auth refresh` | Eric runs `gh auth login` | Alert Eric; pause git-dependent tasks only |
| Railway | Project token | N/A (GitHub-push deploys) | Eric logs in once at railway.app | **NEVER use `railway` CLI.** Deploy via `git push` only. |
| Dropbox | Auto-refresh | `dropbox-cli.py` handles it | Eric refreshes at dropbox.com/developers | Save files locally; upload later |
| Anthropic API | API key | N/A | Rotate at console.anthropic.com | Model fallback chain handles it |

## Model Fallback Chain

When an LLM provider is unavailable (rate limit, outage, API key issue):

| Primary | Fallback 1 | Fallback 2 | Notes |
|---------|-----------|-----------|-------|
| Claude Opus 4.6 | Grok 4.20 Beta | Claude Sonnet 4.6 | Grok 4.20 Beta has 2M context at lower cost; cross-provider resilience |
| Grok 4.20 Beta | Claude Opus 4.6 | Claude Sonnet 4.6 | Cross-provider resilience |
| Claude Sonnet 4.6 | Grok 4 Fast | Claude Haiku 4.5 | Cheapest tier for simple tasks |

Managed by `auth-profiles.json` cooldown/error tracking. Self-heal script clears cooldowns automatically.

## Rules
1. **Railway CLI is BANNED.** All Railway deployment is GitHub-push → auto-deploy → curl verify. No `railway login`, no `railway up`, no `railway init`. Section 16 of railway SKILL.md is the only workflow.
2. **gog failure = switch to Zapier immediately.** Don't wait. Don't retry more than once. Switch, deliver, then fix auth.
3. **gh failure = pause and alert.** Git operations are critical path — alert Eric within 1 minute.
4. **Log every auth event** to `memory/incidents.jsonl` with `error_category: "auth"`.
5. **Monitor pre-flight catches expiry BEFORE cron jobs fail.** If pre-flight fails, ALL credential-dependent crons are paused, not silently attempted.
