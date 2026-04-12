# mc-snapshot

> Generate and send a full Mission Control snapshot as a self-contained HTML file.

## Triggers

Use when Eric says:
- "snapshot Mission Control"
- "take an MC snapshot"
- "send me Mission Control status"
- "MC snapshot"
- "dashboard snapshot"

## What It Does

Pulls live data from all Mission Control API endpoints (gateway, tasks, comms, system health, CIC graph, today's memory file, task board), generates a rich self-contained HTML file with dark glassmorphism design, and delivers it via Telegram + email.

## Sections Included

1. **System Status** — Gateway health, latency, OpenClaw version, Node version
2. **Agents** — All 8 agents with models, tools, workspaces
3. **Task Board** — Active + recently completed tasks with progress bars
4. **Cron Jobs** — All cron jobs with schedules and status
5. **Communications** — Last 20 Telegram/system log entries
6. **CIC Graph Stats** — Node/edge counts, type breakdown
7. **Today's Activity Log** — Full memory file rendered as HTML

## Usage

```bash
# Generate + deliver (Telegram + email)
python3 ~/.openclaw/workspace/scripts/mc_snapshot.py

# Generate file only, no delivery
python3 ~/.openclaw/workspace/scripts/mc_snapshot.py --output-only

# Custom output directory
python3 ~/.openclaw/workspace/scripts/mc_snapshot.py --output /path/to/dir
```

## Output

- File: `~/Documents/MC_Snapshot_{YYYY-MM-DD_HHMM}.html`
- Self-contained (no external CSS/JS/fonts) — works offline on iPhone/iPad
- Typically 50-80KB depending on data volume

## Dependencies

- Python 3 stdlib only (no pip packages)
- Local APIs: `localhost:3000` (gateway), `localhost:3001` (MC backend)
- Delivery: `scripts/send_file_email.py`, Telegram gateway API

## Execution

Just run the script — it handles everything:

```bash
python3 ~/.openclaw/workspace/scripts/mc_snapshot.py
```
