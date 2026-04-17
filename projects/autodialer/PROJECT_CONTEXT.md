# AutoDialer — Voice-Commanded Automated Telephone Call System

## Owner
Eric Brown — CFO & COO, Cohesity

## Goal
Build a system where Eric can voice-prompt Jarvis to:
1. Schedule automated phone calls to any number at any recurring schedule (e.g. "call 571-215-3060 every weekday at 7:30am")
2. Specify a message to deliver when the person picks up (TTS via Twilio)
3. Manage schedules (list, cancel, modify) via voice

## Stack
- **Twilio:** Voice calls + TTS (already configured — from number +18333027822)
- **Python + FastAPI:** API backend
- **APScheduler or OpenClaw cron:** Scheduling
- **Docker:** Containerized, Railway-ready
- **Deployment:** MacBook-local first (no Railway needed for personal use), or Railway for persistence

## Twilio Config (already in workspace)
- From number: +18333027822
- Credentials: in 1Password / openclaw auth profiles

## Test Target
- Eric's cell: +1 571-215-3060
- Test message: "Good morning Eric, this is Jarvis. Your automated call system is working."

## Success Criteria
1. Can schedule "call +15712153060 every weekday at 7:30am with message X" via voice/Telegram
2. Call goes out at scheduled time, TTS message plays when answered
3. Can list and cancel schedules
4. Persists across restarts
5. Test call to Eric's cell succeeds within this session

## Created
2026-04-16
