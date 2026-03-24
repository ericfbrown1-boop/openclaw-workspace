#!/usr/bin/env python3
"""Send top 15 CoWork skills document via email."""
import smtplib
from email.message import EmailMessage
from pathlib import Path

msg = EmailMessage()
msg['From'] = 'ericfbrown1@gmail.com'
msg['To'] = 'ericfbrown1@gmail.com'
msg['Cc'] = 'ericfbrown1@gmail.com'
msg['Subject'] = 'Top 15 Claude CoWork Skills for CFO/COO — Ready to Install'

body = """Eric,

Here's the comprehensive collection of the top 15 Claude CoWork skills curated for your role as CFO & COO of Cohesity. Each skill includes the full content ready to paste into the CoWork Skill Creator.

PART A — Top 5 Email Triage & Review Skills:

1. GOG Email Triage — From Anthropic's official skills repo (PR #299). Prioritizes inbox with P0-P3 urgency classification using Google Workspace integration. 7,050+ lines of documentation.

2. Inbox Classifier — From LongRacks Labs, recommended on Reddit r/ClaudeAI. Self-learning email classification that improves over time. Custom categories for executives.

3. GOG Email Draft & Send Suite — Companion to #1. Composes executive replies with two tone variants (concise CFO voice vs. warmer relationship-building). Requires explicit "YES, SEND" confirmation.

4. Internal Comms (Anthropic Official) — Write status reports, 3P updates, newsletters, and leadership comms. Ships with Claude.

5. Custom CFO Email Triage — Purpose-built for your role. Understands Cohesity's org structure, prioritizes by business impact, routes attachments to the CFO Document Review skill.

PART B — Top 10 CFO/COO Productivity Skills:

6. Excel/XLSX (Anthropic Official) — Industry-standard financial model formatting
7. PowerPoint/PPTX (Anthropic Official) — Board deck creation and analysis
8. Word/DOCX (Anthropic Official) — Contracts, memos, reports
9. CEO Strategic Advisor (2,300 stars) — Board governance, M&A, strategy
10. Financial Modeling Suite (32,682 stars) — DCF, Monte Carlo, sensitivity analysis
11. Cost-Benefit Analysis — NPV, ROI, IRR with sensitivity testing
12. Competitive Intelligence Monitor — Track Rubrik, Commvault, Veeam
13. Board Deck Review & Preparation — End-to-end board meeting prep
14. Contract & Vendor Review — SaaS agreements, pricing benchmarks, risk flags
15. Executive Meeting Prep & Briefing — Calendar-aware pre-meeting briefs

Sources researched: GitHub (anthropics/skills, VoltAgent/awesome-agent-skills 6.5K stars, alirezarezvani/claude-skills 2.3K stars, K-Dense-AI 8.2K stars), FindSkill.ai (1,236 templates), Snyk, Reddit r/ClaudeAI, Substack.

Quick start: Open CoWork → /skill-creator → paste any skill from the document.

---
Sent by Jarvis - AI assistant to Eric Brown"""

msg.set_content(body)

attachment_path = Path('/Users/ericbrown/.openclaw/workspace/Top_15_CoWork_Skills_CFO.docx')
with open(attachment_path, 'rb') as f:
    msg.add_attachment(
        f.read(),
        maintype='application',
        subtype='vnd.openxmlformats-officedocument.wordprocessingml.document',
        filename='Top_15_CoWork_Skills_CFO.docx'
    )

try:
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login('ericfbrown1@gmail.com', 'jplmfcfecipqwkgi')
        smtp.send_message(msg)
    print("Email sent successfully!")
except Exception as e:
    print(f"Error: {e}")
