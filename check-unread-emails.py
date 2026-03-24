#!/usr/bin/env python3
"""Find unread tax-related emails from the past 7 days using gog CLI."""

import json
import re
import subprocess
from datetime import datetime
from typing import List, Dict

TAX_KEYWORDS = [
    'tax', 'irs', '1099', 'w-2', 'w2', '1040', 'cpa', 'accountant',
    'deduction', 'withholding', 'refund', 'schedule', 'k-1', 'k1',
    'estimated tax', 'quarterly tax', 'filing', 'return', 'form 1099',
    'revenue service', 'assessment', 'property tax', 'income tax', 'capital gain',
    '1098', '1095', 'taxation', 'taxes', 'tax document', 'tax payment'
]

QUERY = 'label:inbox label:unread newer_than:7d'
MAX_RESULTS = '500'


def run_gog_query() -> List[Dict]:
    """Run gog CLI to fetch unread messages from the past 7 days."""
    cmd = [
        'gog',
        'gmail',
        'messages',
        'search',
        QUERY,
        '--max',
        MAX_RESULTS,
        '--json'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"gog command failed (code {result.returncode}): {result.stderr.strip()}"
        )
    payload = json.loads(result.stdout or '{}')
    return payload.get('messages', [])


def keyword_matches(text: str, keyword: str) -> bool:
    text = text.lower()
    keyword = keyword.lower()
    if any(ch in keyword for ch in [' ', '-', '/']):
        return keyword in text
    pattern = r'\b' + re.escape(keyword) + r'\b'
    return re.search(pattern, text) is not None


def is_tax_related(subject: str, sender: str) -> bool:
    """Check if the subject/sender text contains tax keywords."""
    haystack = f"{subject} {sender}".lower()
    return any(keyword_matches(haystack, keyword) for keyword in TAX_KEYWORDS)


def normalize_date(date_str: str) -> str:
    """Normalize gog date (YYYY-MM-DD HH:MM) to YYYY-MM-DD."""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        return date_str.split(' ')[0]


def main() -> int:
    try:
        messages = run_gog_query()
    except Exception as exc:
        print(json.dumps({'error': str(exc)}))
        return 1

    tax_emails: List[Dict] = []

    for msg in messages:
        subject = msg.get('subject', '')
        sender = msg.get('from', '')
        if not subject and not sender:
            continue
        if not is_tax_related(subject, sender):
            continue
        tax_emails.append({
            'date_received': normalize_date(msg.get('date', '')),
            'sender': sender,
            'subject': subject,
            'message_id': msg.get('id')
        })

    output = {
        'query': QUERY,
        'count': len(tax_emails),
        'emails': tax_emails
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
