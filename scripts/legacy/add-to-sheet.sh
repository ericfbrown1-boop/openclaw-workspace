#!/bin/bash

# Google Sheet ID
SHEET_ID="1PwSUPWBT-IJ4rIyJ8TlEPqsq8D2XiO8unStzX0sy-e4"

# Prepare the JSON array for all rows
# Format: Date Received, Sender, Description, Type of Tax Item, Link to Original Gmail, Comments/Questions, Not Tax Related

cat > /tmp/tax_emails_rows.json <<'EOF'
[
  ["2026-02-09","agrivine@charter.net","Re: 2025 Costs","","https://mail.google.com/mail/u/0/#inbox/SJ2P220MB1233CF57D85E6022687864C8A165A@SJ2P220MB1233.NAMP220.PROD.OUTLOOK.COM","",""],
  ["2026-02-09","ericfbrown1@gmail.com","Farm Trip Documentation - Sept/Oct 2025 for Tax Return","","https://mail.google.com/mail/u/0/#inbox/6989fec0.050a0220.1f6997.b5ec@mx.google.com","",""],
  ["2026-02-09","Jarvis <ericfbrown1@gmail.com>","Updated Farm Trip Documentation - Sept/Oct 2025","","https://mail.google.com/mail/u/0/#inbox/698a08e4.050a0220.ceab4.14a0@mx.google.com","",""],
  ["2026-02-09","Jarvis <ericfbrown1@gmail.com>","Final Farm Trip Documentation - Sept/Oct 2025 (Corrected Lodging)","","https://mail.google.com/mail/u/0/#inbox/698a0be2.050a0220.2badcc.53c0@mx.google.com","",""],
  ["2026-02-09","Hyun Ju Park <angie_hjpark@yahoo.com>","Re: 2025 Michigan taxes","","https://mail.google.com/mail/u/0/#inbox/1322139179.549489.1770655254654@mail.yahoo.com","",""],
  ["2026-02-09","Fidelity Investments <Fidelity.Investments@mail.fidelity.com>","Your tax form is available","","https://mail.google.com/mail/u/0/#inbox/d7accb22-9c9a-4de9-abe2-03a025db9ce1@las1s04mta903.xt.local","",""],
  ["2026-02-10","Chad Nardiello <chad@nt-llp.com>","RE: Brown, Eric and Old Mission - Supplemental Briefing for Appeals","","https://mail.google.com/mail/u/0/#inbox/CO1PR05MB79608046E3B278F0514EAD13FC62A@CO1PR05MB7960.namprd05.prod.outlook.com","",""],
  ["2026-02-11","ericfbrown1@gmail.com","IRS 2021 Audit - Duplicate Form F Entry Summary","","https://mail.google.com/mail/u/0/#inbox/698cbc88.050a0220.29ddb7.40eb@mx.google.com","",""],
  ["2026-02-11","ericfbrown1@gmail.com","2021 IRS Audit - Form F Duplicate Entry Explanation","","https://mail.google.com/mail/u/0/#inbox/698cbca9.050a0220.8d1b0.e42a@mx.google.com","",""],
  ["2026-02-11","Lawrence Balanovsky <lbalanovsky@keystone.cpa>","RE: Brown, Eric and Old Mission - Supplemental Briefing for Appeals","","https://mail.google.com/mail/u/0/#inbox/DM3PPF7911AB4DDB56562ACB6608D59BEB6C663A@DM3PPF7911AB4DD.namprd15.prod.outlook.com","",""],
  ["2026-02-12","Chad Nardiello <chad@nt-llp.com>","RE: Brown, Eric and Old Mission - Supplemental Briefing for Appeals","","https://mail.google.com/mail/u/0/#inbox/CO1PR05MB7960218FCAA9EAD05A0D61A4FC60A@CO1PR05MB7960.namprd05.prod.outlook.com","",""],
  ["2026-02-13","Michael Bosma <mbosma@keystone.cpa>","Attorney Client Privileged -","","https://mail.google.com/mail/u/0/#inbox/SA0PR15MB40459BB5E555C45EC671909EAD61A@SA0PR15MB4045.namprd15.prod.outlook.com","",""],
  ["2026-02-14","Chad Nardiello <chad@nt-llp.com>","RE: Attorney Client Privileged -","","https://mail.google.com/mail/u/0/#inbox/PH0PR05MB7962E3F7FAD61C1F7A811FF3FC6EA@PH0PR05MB7962.namprd05.prod.outlook.com","",""],
  ["2026-02-14","Michael Bosma <mbosma@keystone.cpa>","RE: Attorney Client Privileged -","","https://mail.google.com/mail/u/0/#inbox/DM6PR15MB4038CB7BB90470DC1782888AAD6EA@DM6PR15MB4038.namprd15.prod.outlook.com","",""],
  ["2026-02-15","Chad Nardiello <chad@nt-llp.com>","Re: Attorney Client Privileged -","","https://mail.google.com/mail/u/0/#inbox/CCDFDF16-8454-4D23-828D-A8499D7B561F@nt-llp.com","",""]
]
EOF

# Add rows to the sheet
gog sheets append "$SHEET_ID" "Sheet1!A:G" --values-json "$(cat /tmp/tax_emails_rows.json)" --insert INSERT_ROWS

echo "Added 15 tax-related emails to the Income Tax Tracking Items sheet"
