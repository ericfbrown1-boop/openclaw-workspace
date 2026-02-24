#!/usr/bin/env python3
"""Add tax-related emails to Google Sheet."""

import json
import subprocess

# Key tax-related emails to add (filtering out false positives like boat shows, etc.)
key_tax_emails = [
    {
        "date": "2026-02-09",
        "sender": "agrivine@charter.net",
        "subject": "Re: 2025 Costs",
        "message_id": "SJ2P220MB1233CF57D85E6022687864C8A165A@SJ2P220MB1233.NAMP220.PROD.OUTLOOK.COM"
    },
    {
        "date": "2026-02-09",
        "sender": "ericfbrown1@gmail.com",
        "subject": "Farm Trip Documentation - Sept/Oct 2025 for Tax Return",
        "message_id": "6989fec0.050a0220.1f6997.b5ec@mx.google.com"
    },
    {
        "date": "2026-02-09",
        "sender": "Jarvis <ericfbrown1@gmail.com>",
        "subject": "Updated Farm Trip Documentation - Sept/Oct 2025",
        "message_id": "698a08e4.050a0220.ceab4.14a0@mx.google.com"
    },
    {
        "date": "2026-02-09",
        "sender": "Jarvis <ericfbrown1@gmail.com>",
        "subject": "Final Farm Trip Documentation - Sept/Oct 2025 (Corrected Lodging)",
        "message_id": "698a0be2.050a0220.2badcc.53c0@mx.google.com"
    },
    {
        "date": "2026-02-09",
        "sender": "Hyun Ju Park <angie_hjpark@yahoo.com>",
        "subject": "Re: 2025 Michigan taxes",
        "message_id": "1322139179.549489.1770655254654@mail.yahoo.com"
    },
    {
        "date": "2026-02-09",
        "sender": "Fidelity Investments <Fidelity.Investments@mail.fidelity.com>",
        "subject": "Your tax form is available",
        "message_id": "d7accb22-9c9a-4de9-abe2-03a025db9ce1@las1s04mta903.xt.local"
    },
    {
        "date": "2026-02-10",
        "sender": "Chad Nardiello <chad@nt-llp.com>",
        "subject": "RE: Brown, Eric and Old Mission - Supplemental Briefing for Appeals",
        "message_id": "CO1PR05MB79608046E3B278F0514EAD13FC62A@CO1PR05MB7960.namprd05.prod.outlook.com"
    },
    {
        "date": "2026-02-11",
        "sender": "ericfbrown1@gmail.com",
        "subject": "IRS 2021 Audit - Duplicate Form F Entry Summary",
        "message_id": "698cbc88.050a0220.29ddb7.40eb@mx.google.com"
    },
    {
        "date": "2026-02-11",
        "sender": "ericfbrown1@gmail.com",
        "subject": "2021 IRS Audit - Form F Duplicate Entry Explanation",
        "message_id": "698cbca9.050a0220.8d1b0.e42a@mx.google.com"
    },
    {
        "date": "2026-02-11",
        "sender": "Lawrence Balanovsky <lbalanovsky@keystone.cpa>",
        "subject": "RE: Brown, Eric and Old Mission - Supplemental Briefing for Appeals",
        "message_id": "DM3PPF7911AB4DDB56562ACB6608D59BEB6C663A@DM3PPF7911AB4DD.namprd15.prod.outlook.com"
    },
    {
        "date": "2026-02-12",
        "sender": "Chad Nardiello <chad@nt-llp.com>",
        "subject": "RE: Brown, Eric and Old Mission - Supplemental Briefing for Appeals",
        "message_id": "CO1PR05MB7960218FCAA9EAD05A0D61A4FC60A@CO1PR05MB7960.namprd05.prod.outlook.com"
    },
    {
        "date": "2026-02-13",
        "sender": "Michael Bosma <mbosma@keystone.cpa>",
        "subject": "Attorney Client Privileged -",
        "message_id": "SA0PR15MB40459BB5E555C45EC671909EAD61A@SA0PR15MB4045.namprd15.prod.outlook.com"
    },
    {
        "date": "2026-02-14",
        "sender": "Chad Nardiello <chad@nt-llp.com>",
        "subject": "RE: Attorney Client Privileged -",
        "message_id": "PH0PR05MB7962E3F7FAD61C1F7A811FF3FC6EA@PH0PR05MB7962.namprd05.prod.outlook.com"
    },
    {
        "date": "2026-02-14",
        "sender": "Michael Bosma <mbosma@keystone.cpa>",
        "subject": "RE: Attorney Client Privileged -",
        "message_id": "DM6PR15MB4038CB7BB90470DC1782888AAD6EA@DM6PR15MB4038.namprd15.prod.outlook.com"
    },
    {
        "date": "2026-02-15",
        "sender": "Chad Nardiello <chad@nt-llp.com>",
        "subject": "Re: Attorney Client Privileged -",
        "message_id": "CCDFDF16-8454-4D23-828D-A8499D7B561F@nt-llp.com"
    }
]

# Prepare rows for addition
rows_to_add = []
for email in key_tax_emails:
    gmail_link = f"https://mail.google.com/mail/u/0/#inbox/{email['message_id']}"
    rows_to_add.append({
        "Date Received": email["date"],
        "Sender": email["sender"],
        "Description": email["subject"],
        "Type of Tax Item": "",
        "Link to Original Gmail": gmail_link,
        "Comments/Questions": "",
        "Not Tax Related": ""
    })

print(f"Prepared {len(rows_to_add)} rows to add to the sheet")
print(json.dumps(rows_to_add, indent=2))
