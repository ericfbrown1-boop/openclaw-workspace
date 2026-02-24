#!/usr/bin/env python3
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

# Gmail credentials
FROM_EMAIL = "ericfbrown1@gmail.com"
APP_PASSWORD = "sxugqgnxpfgvxcik"
TO_EMAIL = "ericfbrown1@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_redlined_memo():
    """Send the redlined NARR memo via email"""
    
    print("Preparing email...")
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL
    msg['Subject'] = "Redlined: NARR Memo Feb 2026 - Review Complete"
    
    # Email body
    body = """Hi Eric,

I've completed a comprehensive editorial review of your NARR Memo (Feb 2026). Please find the redlined version attached.

SUMMARY OF REVIEW:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Grade: A- (Excellent with minor improvements needed)

Key Findings:
✓ All major data points verified (AWS, Microsoft, OpenAI, Anthropic)
✓ Strong analytical framework and compelling thesis
✓ The 75% NARR concentration in 5 companies is a powerful insight

WHAT'S IN THE REDLINED VERSION:

1. Grammar & Style Suggestions (12 items)
   - Number spelling, verb tense consistency, word choice refinements

2. Structural & Clarity Improvements (7 items)
   - Recommendation to add executive summary
   - Better subheading structure
   - Earlier NARR definition

3. Fact-Checking & Accuracy Verification
   - ✓ AWS $35.58B - VERIFIED
   - ✓ Microsoft $32.9B - VERIFIED  
   - ✓ OpenAI $20B+ - VERIFIED
   - ✓ Anthropic $9B+ - VERIFIED
   - ⚠ Google Cloud $17.66B - needs source (Alphabet Q4 earnings may not be public yet)
   - ⚠ Amazon $200B capex - needs verification

4. Questions for You (8 questions)
   - Intended audience?
   - Sources for unverified figures?
   - How to handle the two concluding questions?

5. Suggested Additions (6 items)
   - Historical NARR comparison
   - Expanded conclusion section
   - Forward outlook table

6. Strengths Identified
   - Comprehensive data coverage
   - Clear methodology
   - Excellent sourcing
   - Timely analysis

7. Primary Recommendations
   - Add executive summary
   - Expand conclusion (currently ends abruptly)
   - Define NARR upfront
   - Verify Google/Amazon figures
   - Minor grammar edits

BOTTOM LINE:
This is strong analytical work with a compelling thesis. With the suggested structural improvements and an expanded conclusion, this will be highly effective for executive/board-level audiences.

All editorial comments and questions are compiled at the END of the document in a dedicated "Editorial Review: Questions & Comments" section for easy review.

Best regards,
AI Editorial Assistant
{date}

---
Review Date: {date}
Original Email: NARR memo Feb 2026 (received {date})
Turnaround Time: Same day
""".format(date=datetime.now().strftime("%B %d, %Y at %I:%M %p"))
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach the redlined Word document
    filename = "NARR memo Feb 2026 - REDLINED.docx"
    
    try:
        with open(filename, 'rb') as attachment:
            part = MIMEBase('application', 'vnd.openxmlformats-officedocument.wordprocessingml.document')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename= {filename}')
            msg.attach(part)
        
        print(f"✓ Attached: {filename}")
    
    except FileNotFoundError:
        print(f"❌ Error: {filename} not found")
        return False
    
    # Send email
    print(f"\nConnecting to {SMTP_SERVER}...")
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(FROM_EMAIL, APP_PASSWORD)
        
        print("✓ Connected and authenticated")
        print(f"Sending to: {TO_EMAIL}")
        
        text = msg.as_string()
        server.sendmail(FROM_EMAIL, TO_EMAIL, text)
        server.quit()
        
        print("\n" + "="*80)
        print("✓ SUCCESS: Email sent!")
        print("="*80)
        print(f"To: {TO_EMAIL}")
        print(f"Subject: {msg['Subject']}")
        print(f"Attachment: {filename}")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error sending email: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = send_redlined_memo()
    sys.exit(0 if success else 1)
