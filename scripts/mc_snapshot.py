#!/usr/bin/env python3
"""
mc_snapshot.py — Mission Control Snapshot Generator

Generates a rich, self-contained HTML snapshot of the Mission Control dashboard.
Pulls live data from all MC API endpoints, produces a single HTML file with
inline CSS/JS (no external dependencies), and optionally delivers via Telegram + email.

Usage:
    python3 mc_snapshot.py                    # generate + deliver
    python3 mc_snapshot.py --output-only      # generate file only, no send
    python3 mc_snapshot.py --output /path/    # custom output dir
"""

import argparse
import html
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime

# ─── Configuration ────────────────────────────────────────────────────────────

GATEWAY_API = "http://localhost:3000/api/gateway"
TASKS_API = "http://localhost:3001/tasks"
COMMS_API = "http://localhost:3001/comms"
HEALTH_API = "http://localhost:3000/api/system/health"
CIC_GRAPH_API = "http://localhost:3001/api/cic-graph"

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
MEMORY_DIR = os.path.join(WORKSPACE, "memory")
TASKS_JSON = os.path.join(WORKSPACE, "tasks.json")

TELEGRAM_SEND_API = "http://localhost:18789/api/send"
OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
SEND_EMAIL_SCRIPT = os.path.join(WORKSPACE, "scripts", "send_file_email.py")

DEFAULT_OUTPUT_DIR = os.path.expanduser("~/Documents")


# ─── Data Fetching ────────────────────────────────────────────────────────────

def fetch_json(url: str, timeout: int = 10) -> dict | None:
    """Fetch JSON from a URL, returning None on failure."""
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ⚠ Failed to fetch {url}: {e}", file=sys.stderr)
        return None


def read_file(path: str) -> str | None:
    """Read a text file, returning None if missing."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def fetch_all_data() -> dict:
    """Fetch all data sources and return a dict."""
    print("📡 Fetching data from APIs...")
    gateway = fetch_json(GATEWAY_API)
    tasks = fetch_json(TASKS_API)
    comms = fetch_json(COMMS_API)
    health = fetch_json(HEALTH_API)
    cic = fetch_json(CIC_GRAPH_API)

    today = datetime.now().strftime("%Y-%m-%d")
    memory_file = os.path.join(MEMORY_DIR, f"{today}.md")
    activity_log = read_file(memory_file)

    tasks_json_raw = read_file(TASKS_JSON)
    task_board = None
    if tasks_json_raw:
        try:
            task_board = json.loads(tasks_json_raw)
        except json.JSONDecodeError:
            pass

    return {
        "gateway": gateway,
        "tasks": tasks,
        "comms": comms,
        "health": health,
        "cic": cic,
        "activity_log": activity_log,
        "task_board": task_board,
        "memory_file": memory_file,
    }


# ─── HTML Generation Helpers ──────────────────────────────────────────────────

def e(text) -> str:
    """HTML-escape text safely."""
    if text is None:
        return ""
    return html.escape(str(text))


def status_badge(status: str) -> str:
    """Generate a colored status badge."""
    colors = {
        "completed": "#22c55e",
        "running": "#3b82f6",
        "failed": "#ef4444",
        "queued": "#eab308",
        "ok": "#22c55e",
        "error": "#ef4444",
        "info": "#3b82f6",
        "degraded": "#f59e0b",
    }
    color = colors.get(status.lower(), "#6b7280")
    return f'<span class="badge" style="background:{color}">{e(status.upper())}</span>'


def priority_color(priority: str) -> str:
    """Return color for priority level."""
    return {
        "critical": "#ef4444",
        "high": "#f59e0b",
        "medium": "#3b82f6",
        "low": "#6b7280",
    }.get(priority.lower(), "#6b7280")


def format_timestamp(ts) -> str:
    """Format a timestamp (ms epoch or ISO string) to readable."""
    try:
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(ts / 1000)
        elif isinstance(ts, str):
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            dt = dt.astimezone()
        else:
            return str(ts)
        return dt.strftime("%b %d %I:%M %p")
    except Exception:
        return str(ts) if ts else "—"


def markdown_to_html(md: str) -> str:
    """Very basic markdown→HTML for the activity log."""
    if not md:
        return '<p class="muted">No activity log available for today.</p>'
    lines = md.split("\n")
    out = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("### "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h4>{e(stripped[4:])}</h4>")
        elif stripped.startswith("## "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h3>{e(stripped[3:])}</h3>")
        elif stripped.startswith("# "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h2>{e(stripped[2:])}</h2>")
        elif stripped.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            # Handle bold **text** and inline code `text`
            content = e(stripped[2:])
            content = _inline_format(content)
            out.append(f"<li>{content}</li>")
        elif stripped == "":
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("<br>")
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            content = _inline_format(e(stripped))
            out.append(f"<p>{content}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def _inline_format(text: str) -> str:
    """Handle bold and code in already-escaped text."""
    import re
    # Bold: **text** (escaped as **text**)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Inline code: `text`
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    # Emoji spans for checkmarks / crosses
    text = text.replace("✅", '<span class="emoji-ok">✅</span>')
    text = text.replace("❌", '<span class="emoji-err">❌</span>')
    text = text.replace("⭐", '<span class="emoji-star">⭐</span>')
    return text


# ─── Section Builders ─────────────────────────────────────────────────────────

def build_system_status(health: dict | None, gateway: dict | None) -> str:
    """Section 1: System Status."""
    if not health:
        return '<p class="muted">System health data unavailable.</p>'

    gw_ok = health.get("gatewayOnline", False)
    gw_badge = status_badge("ok" if gw_ok else "error")
    gw_status = "ONLINE" if gw_ok else "OFFLINE"
    latency = health.get("gatewayLatencyMs", "—")
    oc_version = health.get("openclawVersion", "Unknown")
    node_version = health.get("nodeVersion", "Unknown")
    platform = health.get("platform", "Unknown")
    host = health.get("host", "Unknown")

    return f'''
    <div class="status-grid">
        <div class="status-card">
            <div class="status-label">Gateway</div>
            <div class="status-value">{gw_badge} {e(gw_status)}</div>
        </div>
        <div class="status-card">
            <div class="status-label">Latency</div>
            <div class="status-value">{e(str(latency))} ms</div>
        </div>
        <div class="status-card">
            <div class="status-label">OpenClaw</div>
            <div class="status-value">{e(oc_version)}</div>
        </div>
        <div class="status-card">
            <div class="status-label">Node.js</div>
            <div class="status-value">{e(node_version)}</div>
        </div>
        <div class="status-card">
            <div class="status-label">Platform</div>
            <div class="status-value">{e(platform)}</div>
        </div>
        <div class="status-card">
            <div class="status-label">Host</div>
            <div class="status-value">{e(host)}</div>
        </div>
    </div>
    '''


def build_agents_section(gateway: dict | None) -> str:
    """Section 2: Agent Cards."""
    if not gateway or "agents" not in gateway:
        return '<p class="muted">Agent data unavailable.</p>'

    agents = gateway["agents"]
    cards = []
    for agent in agents:
        name = agent.get("name", agent.get("id", "Unknown"))
        aid = agent.get("id", "")
        model = agent.get("model", {})
        primary = model.get("primary", "Unknown") if isinstance(model, dict) else str(model)
        fallbacks = model.get("fallbacks", []) if isinstance(model, dict) else []
        workspace = agent.get("workspace", "—")

        tools = agent.get("tools", {})
        if isinstance(tools, dict):
            tool_list = tools.get("allow", [])
            if not tool_list:
                tool_list = ["(all)"]
            denied = tools.get("deny", [])
        else:
            tool_list = ["(all)"]
            denied = []

        tools_html = ", ".join(f'<span class="tool-tag">{e(t)}</span>' for t in tool_list[:8])
        if len(tool_list) > 8:
            tools_html += f' <span class="muted">+{len(tool_list)-8} more</span>'

        denied_html = ""
        if denied:
            denied_html = f'<div class="denied-tools">Denied: {", ".join(e(d) for d in denied)}</div>'

        fallback_html = ""
        if fallbacks:
            fallback_html = f'<div class="fallbacks">Fallbacks: {", ".join(e(f) for f in fallbacks)}</div>'

        cards.append(f'''
        <div class="agent-card">
            <div class="agent-header">
                <span class="agent-name">{e(name)}</span>
                <span class="agent-id">{e(aid)}</span>
            </div>
            <div class="agent-model">🧠 {e(primary)}</div>
            {fallback_html}
            <div class="agent-tools">{tools_html}</div>
            {denied_html}
            <div class="agent-workspace">📁 {e(workspace)}</div>
        </div>
        ''')

    return f'<div class="agents-grid">{"".join(cards)}</div>'


def build_task_board(tasks_api: dict | None, task_board: dict | None) -> str:
    """Section 3: Task Board — active + recent archive."""
    sections = []

    # Active tasks from tasks API
    active = []
    if tasks_api and tasks_api.get("tasks"):
        active = tasks_api["tasks"]

    # Also check task_board (tasks.json) for running/queued
    if task_board and isinstance(task_board, dict):
        tb_tasks = task_board.get("tasks", task_board)
        if isinstance(tb_tasks, dict):
            for tid, t in tb_tasks.items():
                if isinstance(t, dict) and t.get("status") in ("running", "queued", "blocked"):
                    # Avoid duplicates
                    if not any(a.get("id") == tid for a in active):
                        active.append(t)

    # Archive
    archive = []
    if tasks_api and tasks_api.get("archive"):
        archive = tasks_api["archive"][:10]

    if not active and not archive:
        return '<p class="muted">No tasks found.</p>'

    # Active tasks
    if active:
        sections.append('<h4 class="subsection">🟢 Active Tasks</h4>')
        for task in active:
            sections.append(_task_card(task))
    else:
        sections.append('<p class="muted">No active tasks.</p>')

    # Archive
    if archive:
        sections.append('<h4 class="subsection">📋 Recently Completed (last 10)</h4>')
        for task in archive:
            sections.append(_task_card(task))

    return "\n".join(sections)


def _task_card(task: dict) -> str:
    """Render a single task card."""
    title = task.get("title", task.get("id", "Unknown"))
    status = task.get("status", "unknown")
    progress = task.get("progress", 0)
    priority = task.get("priority", "medium")
    owner = task.get("owner", "—")
    summary = task.get("summary", "")
    pc = priority_color(priority)

    progress_bar = ""
    if isinstance(progress, (int, float)):
        progress_bar = f'''
        <div class="progress-bar">
            <div class="progress-fill" style="width:{progress}%;background:{
                "#22c55e" if progress == 100 else "#3b82f6"
            }"></div>
            <span class="progress-text">{progress}%</span>
        </div>
        '''

    completed = task.get("completedAt", "")
    time_info = f"Completed: {format_timestamp(completed)}" if completed else ""
    started = task.get("startedAt", "")
    if started and not completed:
        time_info = f"Started: {format_timestamp(started)}"

    return f'''
    <div class="task-card" style="border-left: 3px solid {pc}">
        <div class="task-header">
            <span class="task-title">{e(title)}</span>
            {status_badge(status)}
        </div>
        <div class="task-meta">
            <span class="priority-tag" style="color:{pc}">●{e(priority.upper())}</span>
            <span>Owner: {e(owner)}</span>
            {f'<span class="time-info">{e(time_info)}</span>' if time_info else ''}
        </div>
        {progress_bar}
        {f'<p class="task-summary">{e(summary[:200])}</p>' if summary else ''}
    </div>
    '''


def build_cron_section(gateway: dict | None) -> str:
    """Section 4: Cron Jobs table."""
    if not gateway or "cronJobs" not in gateway:
        return '<p class="muted">Cron job data unavailable.</p>'

    crons = gateway["cronJobs"]
    rows = []
    for cj in crons:
        name = cj.get("name", "Unknown")
        enabled = cj.get("enabled", False)
        schedule = cj.get("schedule", {})
        sched_str = ""
        if schedule.get("kind") == "cron":
            sched_str = schedule.get("expr", "—")
        elif schedule.get("kind") == "every":
            ms = schedule.get("everyMs", 0)
            if ms >= 3600000:
                sched_str = f"every {ms // 3600000}h"
            elif ms >= 60000:
                sched_str = f"every {ms // 60000}m"
            else:
                sched_str = f"every {ms // 1000}s"

        state = cj.get("state", {})
        next_run = state.get("nextRunAtMs")
        last_status = state.get("lastRunStatus", "—")
        agent = cj.get("agentId", "—")

        status_dot = "🟢" if enabled else "⚫"
        last_badge = status_badge(last_status) if last_status != "—" else "—"

        rows.append(f'''
        <tr>
            <td>{status_dot} {e(name)}</td>
            <td>{e(agent)}</td>
            <td><code>{e(sched_str)}</code></td>
            <td>{last_badge}</td>
            <td>{format_timestamp(next_run) if next_run else '—'}</td>
        </tr>
        ''')

    return f'''
    <div class="table-wrap">
    <table>
        <thead>
            <tr>
                <th>Name</th>
                <th>Agent</th>
                <th>Schedule</th>
                <th>Last Status</th>
                <th>Next Run</th>
            </tr>
        </thead>
        <tbody>
            {"".join(rows)}
        </tbody>
    </table>
    </div>
    '''


def build_comms_section(comms: dict | None) -> str:
    """Section 5: Communications — last 20 entries."""
    if not comms:
        return '<p class="muted">Communications data unavailable.</p>'

    messages = comms.get("telegram", [])[:20]
    stats = comms.get("stats", {})

    if not messages:
        return '<p class="muted">No recent communications.</p>'

    # Stats summary
    stats_html = ""
    if stats:
        total = stats.get("totalMessages", 0)
        errors = stats.get("errors24h", 0)
        sent = stats.get("sent24h", 0)
        status = stats.get("status", "unknown")
        stats_html = f'''
        <div class="comms-stats">
            <span>Total: {total}</span>
            <span>Sent (24h): {sent}</span>
            <span>Errors (24h): <span style="color:#ef4444">{errors}</span></span>
            <span>Status: {status_badge(status)}</span>
        </div>
        '''

    entries = []
    for msg in messages:
        level = msg.get("level", "INFO").upper()
        text = msg.get("text", "")
        ts = msg.get("ts")
        from_who = msg.get("from", "")
        _ = msg.get("type", "")

        level_color = {
            "ERROR": "#ef4444",
            "INFO": "#3b82f6",
            "OK": "#22c55e",
        }.get(level, "#6b7280")

        # Truncate long messages
        if len(text) > 120:
            text = text[:117] + "..."

        entries.append(f'''
        <div class="comm-entry" style="border-left: 3px solid {level_color}">
            <div class="comm-header">
                <span class="comm-level" style="color:{level_color}">{e(level)}</span>
                <span class="comm-from">{e(from_who)}</span>
                <span class="comm-time">{format_timestamp(ts)}</span>
            </div>
            <div class="comm-text">{e(text)}</div>
        </div>
        ''')

    return stats_html + "\n".join(entries)


def build_cic_section(cic: dict | None) -> str:
    """Section 6: CIC Graph Stats."""
    if not cic:
        return '<p class="muted">CIC graph data unavailable.</p>'

    meta = cic.get("meta", {})
    node_count = meta.get("node_count", 0)
    edge_count = meta.get("edge_count", 0)
    generated = meta.get("generated_at", "—")

    # Count node types
    elements = cic.get("elements", {})
    nodes = elements.get("nodes", [])
    type_counts = Counter()
    for node in nodes:
        ntype = node.get("data", {}).get("type", "unknown")
        type_counts[ntype] += 1

    type_rows = "".join(
        f'<tr><td>{e(t)}</td><td>{c}</td></tr>'
        for t, c in type_counts.most_common()
    )

    return f'''
    <div class="status-grid">
        <div class="status-card">
            <div class="status-label">Total Nodes</div>
            <div class="status-value big">{node_count}</div>
        </div>
        <div class="status-card">
            <div class="status-label">Total Edges</div>
            <div class="status-value big">{edge_count}</div>
        </div>
        <div class="status-card">
            <div class="status-label">Generated</div>
            <div class="status-value">{e(str(generated))}</div>
        </div>
    </div>
    <h4 class="subsection">Node Breakdown by Type</h4>
    <div class="table-wrap">
    <table>
        <thead><tr><th>Type</th><th>Count</th></tr></thead>
        <tbody>{type_rows}</tbody>
    </table>
    </div>
    '''


def build_activity_log(activity_log: str | None, memory_file: str) -> str:
    """Section 7: Today's activity log."""
    if not activity_log:
        return f'<p class="muted">No activity log found at {e(memory_file)}</p>'
    return f'''
    <div class="activity-log">
        {markdown_to_html(activity_log)}
    </div>
    '''


# ─── Full HTML Assembly ───────────────────────────────────────────────────────

def generate_html(data: dict) -> str:
    """Assemble the full self-contained HTML snapshot."""
    now = datetime.now()
    timestamp = now.strftime("%A %B %d, %Y %I:%M %p %Z")
    if not timestamp.endswith(("PDT", "PST", "UTC")):
        # Fallback timezone
        import time
        tz_name = time.tzname[time.daylight] if time.daylight else time.tzname[0]
        timestamp = now.strftime("%A %B %d, %Y %I:%M %p") + f" {tz_name}"

    oc_version = "Unknown"
    if data["health"]:
        oc_version = data["health"].get("openclawVersion", "Unknown")

    # Build sections
    s1 = build_system_status(data["health"], data["gateway"])
    s2 = build_agents_section(data["gateway"])
    s3 = build_task_board(data["tasks"], data["task_board"])
    s4 = build_cron_section(data["gateway"])
    s5 = build_comms_section(data["comms"])
    s6 = build_cic_section(data["cic"])
    s7 = build_activity_log(data["activity_log"], data["memory_file"])

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mission Control Snapshot — {e(timestamp)}</title>
<style>
/* ─── CSS Variables & Reset ─────────────────────────────────────────── */
:root {{
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-card: rgba(255, 255, 255, 0.05);
    --border-card: rgba(255, 255, 255, 0.1);
    --accent: #3b82f6;
    --accent-glow: rgba(59, 130, 246, 0.15);
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --success: #22c55e;
    --error: #ef4444;
    --warning: #f59e0b;
}}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    min-height: 100vh;
}}

/* ─── Layout ────────────────────────────────────────────────────────── */
.container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}}

header {{
    text-align: center;
    padding: 40px 20px 30px;
    border-bottom: 1px solid var(--border-card);
    margin-bottom: 30px;
}}

header h1 {{
    font-size: 28px;
    font-weight: 700;
    background: linear-gradient(135deg, var(--accent), #8b5cf6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 8px;
}}

header .timestamp {{
    color: var(--text-secondary);
    font-size: 14px;
}}

/* ─── Section Cards (Glass) ─────────────────────────────────────────── */
.section {{
    background: var(--bg-card);
    border: 1px solid var(--border-card);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}}

.section-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;
    user-select: none;
    padding: 4px 0;
    margin-bottom: 16px;
}}

.section-header h2 {{
    font-size: 18px;
    font-weight: 600;
    color: var(--text-primary);
}}

.section-header .toggle {{
    color: var(--text-muted);
    font-size: 18px;
    transition: transform 0.2s;
}}

.section-header .toggle.collapsed {{
    transform: rotate(-90deg);
}}

.section-body.hidden {{
    display: none;
}}

/* ─── Status Grid ───────────────────────────────────────────────────── */
.status-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 12px;
}}

.status-card {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-card);
    border-radius: 8px;
    padding: 14px;
    text-align: center;
}}

.status-label {{
    font-size: 12px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}}

.status-value {{
    font-size: 14px;
    font-weight: 600;
    word-break: break-all;
}}

.status-value.big {{
    font-size: 28px;
    color: var(--accent);
}}

/* ─── Badge ─────────────────────────────────────────────────────────── */
.badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 700;
    color: #fff;
    letter-spacing: 0.5px;
}}

/* ─── Agents Grid ───────────────────────────────────────────────────── */
.agents-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 14px;
}}

.agent-card {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-card);
    border-radius: 8px;
    padding: 16px;
}}

.agent-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}}

.agent-name {{
    font-weight: 700;
    font-size: 16px;
    color: var(--accent);
}}

.agent-id {{
    font-size: 12px;
    color: var(--text-muted);
    font-family: monospace;
}}

.agent-model {{
    font-size: 13px;
    color: var(--text-secondary);
    margin-bottom: 4px;
}}

.fallbacks {{
    font-size: 11px;
    color: var(--text-muted);
    margin-bottom: 6px;
}}

.agent-tools {{
    margin: 8px 0;
}}

.tool-tag {{
    display: inline-block;
    background: rgba(59, 130, 246, 0.15);
    color: var(--accent);
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 11px;
    margin: 2px 2px 2px 0;
    font-family: monospace;
}}

.denied-tools {{
    font-size: 11px;
    color: var(--error);
    margin-top: 4px;
}}

.agent-workspace {{
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 6px;
    word-break: break-all;
}}

/* ─── Task Cards ────────────────────────────────────────────────────── */
.task-card {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-card);
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 10px;
}}

.task-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
    gap: 10px;
}}

.task-title {{
    font-weight: 600;
    font-size: 14px;
}}

.task-meta {{
    display: flex;
    gap: 12px;
    font-size: 12px;
    color: var(--text-secondary);
    flex-wrap: wrap;
    margin-bottom: 8px;
}}

.priority-tag {{
    font-weight: 700;
    font-size: 11px;
}}

.time-info {{
    color: var(--text-muted);
}}

.task-summary {{
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.4;
}}

.progress-bar {{
    position: relative;
    height: 6px;
    background: rgba(255,255,255,0.1);
    border-radius: 3px;
    margin: 8px 0;
    overflow: visible;
}}

.progress-fill {{
    height: 100%;
    border-radius: 3px;
    transition: width 0.3s;
}}

.progress-text {{
    position: absolute;
    right: 0;
    top: -16px;
    font-size: 10px;
    color: var(--text-muted);
}}

.subsection {{
    font-size: 14px;
    color: var(--text-secondary);
    margin: 16px 0 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border-card);
}}

/* ─── Table ─────────────────────────────────────────────────────────── */
.table-wrap {{
    overflow-x: auto;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}}

th {{
    text-align: left;
    padding: 10px 12px;
    background: var(--bg-secondary);
    color: var(--text-secondary);
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid var(--border-card);
}}

td {{
    padding: 8px 12px;
    border-bottom: 1px solid rgba(255,255,255,0.03);
    color: var(--text-primary);
}}

td code {{
    background: rgba(59, 130, 246, 0.1);
    padding: 2px 4px;
    border-radius: 3px;
    font-size: 12px;
    color: var(--accent);
}}

tr:hover td {{
    background: rgba(255,255,255,0.02);
}}

/* ─── Communications ────────────────────────────────────────────────── */
.comms-stats {{
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    font-size: 13px;
    color: var(--text-secondary);
    margin-bottom: 14px;
    padding: 10px;
    background: var(--bg-secondary);
    border-radius: 8px;
}}

.comm-entry {{
    padding: 8px 12px;
    margin-bottom: 6px;
    background: var(--bg-secondary);
    border-radius: 6px;
}}

.comm-header {{
    display: flex;
    gap: 12px;
    align-items: center;
    margin-bottom: 4px;
}}

.comm-level {{
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    min-width: 45px;
}}

.comm-from {{
    font-size: 12px;
    color: var(--text-muted);
}}

.comm-time {{
    font-size: 11px;
    color: var(--text-muted);
    margin-left: auto;
}}

.comm-text {{
    font-size: 12px;
    color: var(--text-secondary);
    line-height: 1.4;
    word-break: break-word;
}}

/* ─── Activity Log ──────────────────────────────────────────────────── */
.activity-log {{
    font-size: 13px;
    line-height: 1.7;
}}

.activity-log h2 {{ font-size: 18px; color: var(--accent); margin: 16px 0 8px; }}
.activity-log h3 {{ font-size: 15px; color: var(--text-primary); margin: 14px 0 6px; }}
.activity-log h4 {{ font-size: 13px; color: var(--text-secondary); margin: 10px 0 4px; }}
.activity-log ul {{ padding-left: 20px; margin: 4px 0; }}
.activity-log li {{ color: var(--text-secondary); margin: 3px 0; }}
.activity-log code {{
    background: rgba(59, 130, 246, 0.1);
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 12px;
    color: var(--accent);
}}
.activity-log strong {{ color: var(--text-primary); }}
.activity-log p {{ margin: 4px 0; color: var(--text-secondary); }}
.activity-log br {{ display: block; margin: 2px 0; content: ""; }}

.emoji-ok {{ filter: none; }}
.emoji-err {{ filter: none; }}
.emoji-star {{ filter: none; }}

/* ─── Footer ────────────────────────────────────────────────────────── */
footer {{
    text-align: center;
    padding: 30px 20px;
    color: var(--text-muted);
    font-size: 12px;
    border-top: 1px solid var(--border-card);
    margin-top: 20px;
}}

/* ─── Utility ───────────────────────────────────────────────────────── */
.muted {{ color: var(--text-muted); font-size: 13px; }}

/* ─── Responsive ────────────────────────────────────────────────────── */
@media (max-width: 600px) {{
    .container {{ padding: 12px; }}
    header h1 {{ font-size: 22px; }}
    .agents-grid {{ grid-template-columns: 1fr; }}
    .status-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .comms-stats {{ flex-direction: column; gap: 6px; }}
}}
</style>
</head>
<body>

<header>
    <h1>🎯 Mission Control Snapshot</h1>
    <div class="timestamp">{e(timestamp)}</div>
</header>

<div class="container">

<!-- Section 1: System Status -->
<div class="section">
    <div class="section-header" onclick="toggleSection(this)">
        <h2>⚡ System Status</h2>
        <span class="toggle">▼</span>
    </div>
    <div class="section-body">
        {s1}
    </div>
</div>

<!-- Section 2: Agents -->
<div class="section">
    <div class="section-header" onclick="toggleSection(this)">
        <h2>🤖 Agents ({len(data["gateway"].get("agents", [])) if data["gateway"] else 0})</h2>
        <span class="toggle">▼</span>
    </div>
    <div class="section-body">
        {s2}
    </div>
</div>

<!-- Section 3: Task Board -->
<div class="section">
    <div class="section-header" onclick="toggleSection(this)">
        <h2>📋 Task Board</h2>
        <span class="toggle">▼</span>
    </div>
    <div class="section-body">
        {s3}
    </div>
</div>

<!-- Section 4: Cron Jobs -->
<div class="section">
    <div class="section-header" onclick="toggleSection(this)">
        <h2>⏰ Cron Jobs ({len(data["gateway"].get("cronJobs", [])) if data["gateway"] else 0})</h2>
        <span class="toggle">▼</span>
    </div>
    <div class="section-body">
        {s4}
    </div>
</div>

<!-- Section 5: Communications -->
<div class="section">
    <div class="section-header" onclick="toggleSection(this)">
        <h2>💬 Communications</h2>
        <span class="toggle">▼</span>
    </div>
    <div class="section-body">
        {s5}
    </div>
</div>

<!-- Section 6: CIC Graph Stats -->
<div class="section">
    <div class="section-header" onclick="toggleSection(this)">
        <h2>🕸️ CIC Graph Stats</h2>
        <span class="toggle">▼</span>
    </div>
    <div class="section-body">
        {s6}
    </div>
</div>

<!-- Section 7: Today's Activity Log -->
<div class="section">
    <div class="section-header" onclick="toggleSection(this)">
        <h2>📝 Today's Activity Log</h2>
        <span class="toggle">▼</span>
    </div>
    <div class="section-body">
        {s7}
    </div>
</div>

</div>

<footer>
    Generated by Jarvis at {e(timestamp)} | {e(oc_version)}
</footer>

<script>
function toggleSection(header) {{
    var body = header.nextElementSibling;
    var toggle = header.querySelector('.toggle');
    if (body.classList.contains('hidden')) {{
        body.classList.remove('hidden');
        toggle.classList.remove('collapsed');
    }} else {{
        body.classList.add('hidden');
        toggle.classList.add('collapsed');
    }}
}}
</script>

</body>
</html>'''


# ─── Delivery ─────────────────────────────────────────────────────────────────

def send_telegram(filepath: str) -> bool:
    """Send the HTML file via Telegram gateway API."""
    print("📤 Sending via Telegram...")
    try:
        # Read the file
        with open(filepath, "rb") as f:
            file_data = f.read()

        filename = os.path.basename(filepath)

        # Try gateway send API (multipart/form-data)
        import io

        boundary = "----McSnapshotBoundary"
        body = io.BytesIO()

        # chat_id field
        body.write(f"--{boundary}\r\n".encode())
        body.write(b'Content-Disposition: form-data; name="chat_id"\r\n\r\n')
        body.write(b"5387843769\r\n")

        # text field
        body.write(f"--{boundary}\r\n".encode())
        body.write(b'Content-Disposition: form-data; name="text"\r\n\r\n')
        body.write(f"📊 Mission Control Snapshot\n{datetime.now().strftime('%B %d, %Y %I:%M %p')}".encode())
        body.write(b"\r\n")

        # file field
        body.write(f"--{boundary}\r\n".encode())
        body.write(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode())
        body.write(b"Content-Type: text/html\r\n\r\n")
        body.write(file_data)
        body.write(b"\r\n")

        body.write(f"--{boundary}--\r\n".encode())

        req = urllib.request.Request(
            TELEGRAM_SEND_API,
            data=body.getvalue(),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
            print(f"  ✅ Telegram gateway: {resp.status}")
            return True
    except Exception as e1:
        print(f"  ⚠ Gateway send failed: {e1}", file=sys.stderr)

    # Fallback: try Telegram Bot API directly
    try:
        config_raw = read_file(OPENCLAW_CONFIG)
        if config_raw:
            config = json.loads(config_raw)
            # Find telegram token in plugins
            plugins = config.get("plugins", {})
            entries = plugins.get("entries", {})
            # botToken lives at channels.telegram.botToken
            token = config.get("channels", {}).get("telegram", {}).get("botToken", "")
            if not token:
                # fallback: old plugins path
                entries = config.get("plugins", {}).get("entries", {})
                tg_config = entries.get("telegram", {}).get("config", {})
                token = tg_config.get("token", "")
            if token:
                url = f"https://api.telegram.org/bot{token}/sendDocument"
                boundary = "----McSnapFallback"
                body = io.BytesIO()

                body.write(f"--{boundary}\r\n".encode())
                body.write(b'Content-Disposition: form-data; name="chat_id"\r\n\r\n')
                body.write(b"5387843769\r\n")

                body.write(f"--{boundary}\r\n".encode())
                body.write(b'Content-Disposition: form-data; name="caption"\r\n\r\n')
                body.write(f"📊 Mission Control Snapshot — {datetime.now().strftime('%B %d, %Y %I:%M %p')}".encode())
                body.write(b"\r\n")

                body.write(f"--{boundary}\r\n".encode())
                body.write(f'Content-Disposition: form-data; name="document"; filename="{filename}"\r\n'.encode())
                body.write(b"Content-Type: text/html\r\n\r\n")
                body.write(file_data)
                body.write(b"\r\n")

                body.write(f"--{boundary}--\r\n".encode())

                req = urllib.request.Request(
                    url,
                    data=body.getvalue(),
                    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    print(f"  ✅ Telegram Bot API fallback: {resp.status}")
                    return True
    except Exception as e2:
        print(f"  ⚠ Telegram Bot API fallback failed: {e2}", file=sys.stderr)

    return False


def send_email(filepath: str) -> bool:
    """Send the HTML file via email."""
    print("📧 Sending via email...")
    try:
        date_str = datetime.now().strftime("%B %d, %Y")
        result = subprocess.run(
            [
                "python3", SEND_EMAIL_SCRIPT,
                "--file", filepath,
                "--to", "ericfbrown1@gmail.com",
                "--cc", "Eric.brown@cohesity.com",
                "--subject", f"Mission Control Snapshot — {date_str}",
                "--body", "MC snapshot attached. Open on any device.\n\nSent by Jarvis - AI assistant to Eric Brown",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print("  ✅ Email sent successfully")
            return True
        else:
            print(f"  ⚠ Email failed: {result.stderr[:200]}", file=sys.stderr)
            return False
    except Exception as ex:
        print(f"  ⚠ Email error: {ex}", file=sys.stderr)
        return False


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate Mission Control HTML snapshot")
    parser.add_argument("--output-only", action="store_true", help="Generate file only, no send")
    parser.add_argument("--output", type=str, default=None, help="Custom output directory")
    args = parser.parse_args()

    output_dir = args.output or DEFAULT_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    # Fetch all data
    data = fetch_all_data()

    # Generate HTML
    print("🎨 Generating HTML snapshot...")
    html_content = generate_html(data)

    # Write file
    now = datetime.now()
    filename = f"MC_Snapshot_{now.strftime('%Y-%m-%d_%H%M')}.html"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    file_size = os.path.getsize(filepath)
    print(f"✅ Snapshot written: {filepath}")
    print(f"   Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")

    if file_size < 50000:
        print(f"⚠ Warning: File is under 50KB ({file_size:,} bytes) — may lack content", file=sys.stderr)

    if args.output_only:
        print("📦 Output-only mode — skipping delivery")
        return filepath

    # Deliver
    tg_ok = send_telegram(filepath)
    email_ok = send_email(filepath)

    if tg_ok or email_ok:
        print("🎉 Delivery complete!")
    else:
        print("⚠ Both delivery methods failed — file saved locally", file=sys.stderr)

    return filepath


if __name__ == "__main__":
    result = main()
    if result:
        sys.exit(0)
    else:
        sys.exit(1)
