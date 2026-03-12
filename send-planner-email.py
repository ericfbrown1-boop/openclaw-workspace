#!/usr/bin/env python3
"""Send GPT-5.4 Planning Agent document via email."""
import smtplib
from email.message import EmailMessage
from pathlib import Path

msg = EmailMessage()
msg['From'] = 'ericfbrown1@gmail.com'
msg['To'] = 'ericfbrown1@gmail.com'
msg['Cc'] = 'ericfbrown1@gmail.com'
msg['Subject'] = 'GPT-5.4 Enhanced Planning Agent — Upgrade Scripts & Architecture'

body = """Eric,

GPT-5.4 literally launched yesterday (March 5) — perfect timing for this planner upgrade. Attached is the complete document with scripts and architecture for upgrading your OpenClaw planner agent.

What's inside:

1. BACKGROUND — Why GPT-5.4 is ideal for planning (1M context, record benchmarks on professional tasks, native tool search)

2. REFERENCE ARCHITECTURES — I studied the best planning agents on GitHub:
   • Plandex (12K+ stars) — plan-first architecture, diff sandbox, multi-model orchestration
   • APM (Agentic Project Management) — structured multi-agent workflows, context retention
   • Plandex-Lite — 5-agent system (Planner → Architect → Coder → Reviewer → Summarizer)

3. UPGRADE SCRIPT — Bash script that:
   • Backs up your current config
   • Prompts for your OpenAI API key (if not already configured)
   • Updates the planner to use gpt-5.4-pro with intelligent fallbacks
   • Adds 1M context window model configs
   • Restarts the gateway

4. ENHANCED PLANNER PROMPT — New AGENTS.md inspired by Plandex/APM with:
   • 4-phase workflow: Discovery → Architecture → Task Decomposition → PLAN.md
   • Structured task format with acceptance criteria and risk assessment
   • Delegation rules (always plan before code, route errors through Quality)
   • GPT-5.4-specific context management strategies

5. VALIDATION SCRIPT — Tests API access, model availability, and runs a quick planning test

6. COST ANALYSIS — Side-by-side comparison showing GPT-5.4 standard is 6x cheaper than Claude Opus on input with 5x the context window

API Model Names:
• gpt-5.4 — Standard ($2.50/$15 per M tokens)
• gpt-5.4-pro — Maximum performance ($30/$180 per M tokens)

Quick start: Get your API key from platform.openai.com/api-keys, then run the upgrade script.

---
Sent by Jarvis - AI assistant to Eric Brown"""

msg.set_content(body)

attachment_path = Path('/Users/ericbrown/.openclaw/workspace/GPT54_Enhanced_Planning_Agent.docx')
with open(attachment_path, 'rb') as f:
    msg.add_attachment(
        f.read(),
        maintype='application',
        subtype='vnd.openxmlformats-officedocument.wordprocessingml.document',
        filename='GPT54_Enhanced_Planning_Agent.docx'
    )

try:
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login('ericfbrown1@gmail.com', 'sxugqgnxpfgvxcik')
        smtp.send_message(msg)
    print("Email sent successfully!")
except Exception as e:
    print(f"Error: {e}")
