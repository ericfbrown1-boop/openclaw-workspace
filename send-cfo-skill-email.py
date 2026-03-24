#!/usr/bin/env python3
"""Send CFO CoWork Skill document via email with attachment."""
import smtplib
from email.message import EmailMessage
from pathlib import Path

msg = EmailMessage()
msg['From'] = 'ericfbrown1@gmail.com'
msg['To'] = 'ericfbrown1@gmail.com'
msg['Cc'] = 'ericfbrown1@gmail.com'
msg['Subject'] = 'Claude CoWork Skill: CFO Executive Document Review'

body = """Eric,

Here's the Claude CoWork custom skill for CFO-level document review. This skill teaches Claude to analyze email attachments (PowerPoint, Excel, Word) from your perspective as CFO & COO of Cohesity.

What's included in the attached document:

1. SKILL.md — The main skill file with review frameworks for each document type (PPT decks, Excel models, Word docs). This is the part you paste into the Skill Creator.

2. cohesity-context.md — Reference file with Cohesity-specific metrics, strategic priorities, and financial standards.

3. review-checklist.md — Quick-reference checklists for board decks, financial models, vendor proposals, QBRs, and M&A materials.

4. industry-benchmarks.md — Data protection market benchmarks and peer comps (Rubrik, Commvault, Veeam) for evaluating financial claims.

5. Usage examples — Sample prompts that activate the skill.

6. Installation instructions — Two options: via /skill-creator (recommended) or manual file creation.

How to install:
• Open Claude Desktop → Cowork tab
• Type /skill-creator
• Paste the SKILL.md content from Section 1 of the document
• Claude will guide you through the rest

Once installed, just drop any PPT/Excel/Word file into your Cowork folder and ask Claude to "review this deck" or "analyze this model" — it will automatically apply the CFO review framework.

---
Sent by Jarvis - AI assistant to Eric Brown"""

msg.set_content(body)

# Attach the Word document
attachment_path = Path('/Users/ericbrown/.openclaw/workspace/CFO_CoWork_Skill_Document_Review.docx')
with open(attachment_path, 'rb') as f:
    file_data = f.read()
    msg.add_attachment(
        file_data,
        maintype='application',
        subtype='vnd.openxmlformats-officedocument.wordprocessingml.document',
        filename='CFO_CoWork_Skill_Document_Review.docx'
    )

try:
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login('ericfbrown1@gmail.com', 'jplmfcfecipqwkgi')
        smtp.send_message(msg)
    print("Email sent successfully with attachment!")
except Exception as e:
    print(f"Error: {e}")
