#!/bin/bash
# shellcheck disable=SC1037
#
# Quick script to send the lease email via Mail.app
# Run this with: bash SEND_LEASE_EMAIL.sh
#

osascript <<EOF
set theSubject to "DRAFT: New Lease Agreement for 3469 Old Mission Road - Noah Kolassa (April 2026)"
set theBody to "Hi Eric,

Please find attached the DRAFT lease agreement for 3469 Old Mission Road for the new tenant Noah Kolassa.

Key Changes (All marked with track changes):

• Tenant: Noah Kolassa (replacing Kirk and Connie Josvai)
• Tenant Phone: 231-357-6247
• Lease Term: April 1, 2026 - March 31, 2027 (12 months)
• Monthly Rent: \\$2,800 (reduced from \\$2,900)
• Security Deposit: \\$3,300 (increased from \\$2,900)
• Payment Method: Zelle or bank transfer preferred
• Cleaning: Changed from \\$500 non-refundable fee to tenant responsibility clause
• Auto-renewal: Month-to-month after initial term (unchanged)

Track Changes Legend:
- Red strikethrough text = deletions
- Yellow highlighted green bold text = additions

Please review all changes carefully. The document is ready for your review and any additional modifications you'd like to make.

Best regards,
Your OpenClaw Assistant"

set theAttachment to POSIX file "$HOME/.openclaw/workspace/3469_Old_Mission_Lease_Noah_Kolassa_2026_DRAFT_REDLINED.docx"

tell application "Mail"
    set newMessage to make new outgoing message with properties {subject:theSubject, content:theBody, visible:true}
    
    tell newMessage
        make new to recipient at end of to recipients with properties {address:"ericfbrown1@gmail.com"}
        make new to recipient at end of to recipients with properties {address:"Eric.brown@cohesity.com"}
        
        make new attachment with properties {file name:theAttachment} at after the last paragraph
    end tell
    
    activate
end tell
EOF

echo ""
echo "✅ Email draft created in Mail.app"
echo "   Review and click Send when ready!"
