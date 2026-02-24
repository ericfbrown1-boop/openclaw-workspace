#!/usr/bin/env python3
"""Filter tax emails to only include truly tax-related items."""

import json

# Load the data
with open('/dev/stdin') as f:
    data = json.load(f)

# Filter for truly tax-related emails
# Exclude: daily reports, translations, airline stuff, general shopping
exclude_patterns = [
    'Daily AI Productivity Report',
    'Cohesity Technical Articles',
    'Wi-Fi and entertainment',
    'Alumni Game',
    'Your Google Play Order Receipt'
]

tax_specific_senders = [
    'keystone.cpa',
    'nt-llp.com',  # Chad Nardiello attorney
    '@irs.gov',
    'cch.com'  # Tax software
]

def is_truly_tax_related(email):
    """Check if email is truly tax-related."""
    # Exclude patterns
    for pattern in exclude_patterns:
        if pattern in email['subject']:
            return False
    
    # Include if from tax-specific senders
    for sender_pattern in tax_specific_senders:
        if sender_pattern in email['sender_email']:
            return True
    
    # Include specific tax-related subjects
    tax_subjects = [
        'tax',
        'irs',
        'attorney client privileged',
        'supplemental brief',
        'appeals submission',
        'offshore charter llc'
    ]
    
    subject_lower = email['subject'].lower()
    for tax_sub in tax_subjects:
        if tax_sub in subject_lower:
            return True
    
    # Check if it's about lease/rental income
    if 'lease' in subject_lower or 'rental' in subject_lower:
        if 'tesla' not in subject_lower:  # Tesla lease might be business expense
            return True
    
    return False

filtered = [email for email in data if is_truly_tax_related(email)]

print(json.dumps(filtered, indent=2))
