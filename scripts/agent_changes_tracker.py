#!/usr/bin/env python3
"""Agent Skills Change Tracker v2 — includes role summaries and invokable capabilities."""

import json
import hashlib
import os
from pathlib import Path
from datetime import datetime

HOME = Path.home()
STATE_FILE = HOME / ".openclaw/workspace/memory/agent-changes-state.json"
OUTPUT_FILE = HOME / ".openclaw/workspace/memory/agent-changes-latest.md"

WORKSPACES = {
    "main": HOME / ".openclaw/workspace",
    "researcher": HOME / ".openclaw/workspace-researcher",
    "planner": HOME / ".openclaw/workspace-planner",
    "coder": HOME / ".openclaw/workspace-coder",
    "quality": HOME / ".openclaw/workspace-quality",
    "monitor": HOME / ".openclaw/workspace-monitor",
    "auditor": HOME / ".openclaw/workspace-auditor",
    "conductor": HOME / ".openclaw/workspace-conductor",
}

TRACK_FILES = ["AGENTS.md", "IDENTITY.md", "SKILL.md", "SKILLS.md"]

# Agent role descriptions and what they do
AGENT_ROLES = {
    "main": {
        "name": "Jarvis",
        "emoji": "🤖",
        "role": "Primary orchestrator & personal assistant",
        "does": "Handles all direct requests, delegates to specialized agents, manages daily briefings, email, calendar, web research, file management, and conversation"
    },
    "researcher": {
        "name": "Researcher",
        "emoji": "🔍",
        "role": "Deep research & financial analysis",
        "does": "Financial earnings analysis (Rubrik, Commvault, Veeam), competitive intelligence, market research, fact-checking, delivers Word doc reports"
    },
    "planner": {
        "name": "Planner",
        "emoji": "📐",
        "role": "Architecture & project planning",
        "does": "Designs new projects, creates PLAN.md files, defines tech stacks, writes architecture docs. Uses GPT 5.4 + cross-review loop"
    },
    "coder": {
        "name": "Coder",
        "emoji": "💻",
        "role": "Code implementation",
        "does": "Writes code from PLAN.md specs, builds scripts, generates reports, creates Dockerfiles. Reads PLAN.md before writing any code"
    },
    "quality": {
        "name": "Quality",
        "emoji": "🛡️",
        "role": "Security audit & error diagnosis",
        "does": "Part A: Diagnoses errors/crashes. Part B: Security audits (secret scanning, git history, .gitignore, dependencies, Tailscale config). Prepares BFG commands for Jarvis"
    },
    "monitor": {
        "name": "Monitor",
        "emoji": "📊",
        "role": "Stock watch & price monitoring",
        "does": "Tracks Rubrik/Commvault/Veeam stock prices, MicroCenter Santa Clara deals (Apple Studio, Alienware), system health alerts"
    },
    "auditor": {
        "name": "External Auditor",
        "emoji": "📋",
        "role": "Final code review & packaging",
        "does": "Verifies code is clean post-Quality audit, asks Eric about Grok review, packages code with repomix for external review"
    },
    "conductor": {
        "name": "Conductor",
        "emoji": "🚂",
        "role": "DevOps & Railway deployment",
        "does": "Docker builds, Railway deployments, smoke tests, Celery worker setup, MinIO deployment, infrastructure verification. Follows Railway Deployment Skill (13 sections)"
    },
}

# Invokable skills/capabilities Eric can request
INVOKABLE_SKILLS = [
    {
        "category": "📊 Financial & Business",
        "skills": [
            ("Financial Earnings Analysis", "\"Run financial analysis on [company] quarterly results\" — Full sell-side analyst report with ARR, revenue, margins, valuation. Delivered as Word doc + email"),
            ("Competitive Intelligence", "\"Research [company]\" — Deep competitive analysis using web research + Project Scraper data"),
            ("Contract Analysis", "\"Run Contract Analyzer on [files]\" — AI-powered legal contract review with 17-section report, risk flags, entity attribution (Cohesity/Arctera)"),
        ]
    },
    {
        "category": "💻 Code & Deployment",
        "skills": [
            ("Build a Project", "\"Build [description]\" — Full pipeline: Planner → GPT review → Coder → Tester → Quality audit → Conductor deploys to Railway"),
            ("Railway Deployment", "\"Deploy [project] to Railway\" — Docker build, Railway config, Celery workers, MinIO, smoke tests"),
            ("Security Audit", "\"Run security audit on [repo]\" — Secret scanning, git history check, dependency vulnerabilities, BFG cleanup"),
            ("Code Review", "\"Review [repo/PR]\" — Quality + External Auditor pipeline, optional Grok cross-review via repomix"),
        ]
    },
    {
        "category": "📧 Communication & Productivity",
        "skills": [
            ("Send Email", "\"Email [person] about [topic]\" — Via gog CLI or Zapier MCP, with attachments, CC rules applied"),
            ("Search Email", "\"Find emails about [topic]\" — Gmail search via gog or Zapier MCP"),
            ("Calendar Check", "\"What's on my calendar?\" — Google Calendar via gog CLI"),
            ("Google Sheets", "\"Update/read [spreadsheet]\" — Read/write rows via Zapier MCP or gog CLI"),
            ("Dropbox Search", "\"Find [file] in Dropbox\" — Search Eric's personal Dropbox via Zapier MCP"),
        ]
    },
    {
        "category": "🔍 Research & Information",
        "skills": [
            ("Web Research", "\"Research [topic]\" — Web search + fetch, synthesized summary"),
            ("YouTube/Podcast Summary", "\"Summarize [URL]\" — Transcript extraction + AI summary"),
            ("Weather", "\"What's the weather in [location]?\" — Current conditions + forecast"),
            ("Place Search", "\"Find [type of place] near [location]\" — Google Places API"),
        ]
    },
    {
        "category": "🔧 System & Automation",
        "skills": [
            ("System Status", "\"Status\" — Full MacBook health: gateway, disk, Tailscale, Gmail, self-heal, errors"),
            ("Health Check", "\"Run healthcheck\" — Deep security scan of the MacBook"),
            ("Voice Call", "\"Call me\" — Twilio voice call via Tailscale Funnel"),
            ("Cron Jobs", "\"Schedule [task] at [time]\" — Create/manage recurring automation"),
            ("GitHub Operations", "\"Check PR/issues on [repo]\" — PR status, CI, code review, API queries"),
        ]
    },
    {
        "category": "🎯 Daily Automated Tasks",
        "skills": [
            ("6 AM Daily Briefing", "Automatic — Gmail, calendar, AI ideas, competitive news, MicroCenter deals, system health"),
            ("5:30 AM Smoke Test", "Automatic — 24-check system diagnostic with action items"),
            ("5 AM Doctor --fix", "Automatic — Auto-repair config issues"),
            ("Tax Email Scan", "Automatic — Weekly Gmail scan for tax items → Google Sheet"),
            ("Stock Monitor", "Automatic — Rubrik, Commvault, Veeam price tracking"),
            ("Alex Finn YouTube Watch", "Automatic — Daily monitoring for OpenClaw enhancement ideas"),
        ]
    },
]

def file_hash(path):
    return hashlib.md5(path.read_bytes()).hexdigest()

def file_info(path):
    stat = path.stat()
    mod = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
    lines = len(path.read_text(errors='ignore').splitlines())
    return mod, lines

# Load previous state
prev = {}
if STATE_FILE.exists():
    try:
        prev = json.loads(STATE_FILE.read_text())
    except Exception:
        pass

curr = {}
changes = []
new_files = []

for agent, workspace in WORKSPACES.items():
    for fname in TRACK_FILES:
        fpath = workspace / fname
        if fpath.exists():
            h = file_hash(fpath)
            key = f"{agent}/{fname}"
            curr[key] = h
            if key not in prev:
                new_files.append(key)
            elif prev[key] != h:
                mod, lines = file_info(fpath)
                changes.append((key, mod, lines))
    
    skills_dir = workspace / "skills"
    if skills_dir.is_dir():
        for skill_dir in sorted(skills_dir.iterdir()):
            if skill_dir.is_dir():
                for fname in ["SKILL.md", "SKILLS.md"]:
                    fpath = skill_dir / fname
                    if fpath.exists():
                        h = file_hash(fpath)
                        key = f"{agent}/skills/{skill_dir.name}/{fname}"
                        curr[key] = h
                        if key not in prev:
                            new_files.append(key)
                        elif prev[key] != h:
                            mod, lines = file_info(fpath)
                            changes.append((key, mod, lines))

# Save state
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
STATE_FILE.write_text(json.dumps(curr, indent=2))

# Generate output
lines = []
lines.append("### 🤖 Your 8 Agents — What They Do")
lines.append("")
for agent_id, info in AGENT_ROLES.items():
    lines.append(f"**{info['emoji']} {info['name']}** ({agent_id}) — {info['role']}")
    lines.append(f"  {info['does']}")
    lines.append("")

lines.append("---")
lines.append("")
lines.append("### 🎯 Invokable Skills & Capabilities")
lines.append("*Say any of these to Eric's Jarvis:*")
lines.append("")

for cat in INVOKABLE_SKILLS:
    lines.append(f"**{cat['category']}**")
    for name, desc in cat['skills']:
        lines.append(f"- **{name}** — {desc}")
    lines.append("")

lines.append("---")
lines.append("")
lines.append("### 📝 Agent Configuration Changes")
lines.append("")

if not changes and not new_files:
    lines.append("No changes detected since last check. ✅")
else:
    if changes:
        lines.append("**📝 Modified:**")
        for key, mod, lcount in changes:
            lines.append(f"- `{key}` — updated {mod} ({lcount} lines)")
        lines.append("")
    if new_files:
        lines.append("**🆕 Newly tracked:**")
        for nf in new_files:
            lines.append(f"- `{nf}`")
        lines.append("")

output = "\n".join(lines)
OUTPUT_FILE.write_text(output)
print(output)
