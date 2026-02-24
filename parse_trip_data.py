#!/usr/bin/env python3
"""Parse trip emails to extract flight and expense details."""

import json
import re
from html.parser import HTMLParser

class TripHTMLParser(HTMLParser):
    """Simple HTML parser to extract text."""
    def __init__(self):
        super().__init__()
        self.text_content = []
        
    def handle_data(self, data):
        if data.strip():
            self.text_content.append(data.strip())
    
    def get_text(self):
        return ' '.join(self.text_content)

def extract_amounts(text):
    """Extract dollar amounts from text."""
    patterns = [
        r'\$\s*[\d,]+\.\d{2}',
        r'USD\s*[\d,]+\.\d{2}',
        r'Total[:\s]+\$?\s*[\d,]+\.\d{2}',
    ]
    
    amounts = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        amounts.extend(matches)
    
    return amounts

def clean_amount(amount_str):
    """Clean and convert amount string to float."""
    # Remove currency symbols and whitespace
    cleaned = re.sub(r'[^\d.]', '', amount_str)
    try:
        return float(cleaned)
    except:
        return 0.0

def parse_united_booking(email_data):
    """Parse United Airlines booking confirmation."""
    body = email_data['body']
    subject = email_data['subject']
    date = email_data['date']
    
    # Parse HTML to get text
    parser = TripHTMLParser()
    parser.feed(body)
    text = parser.get_text()
    
    # Extract confirmation number
    conf_match = re.search(r'(?:confirmation|booking)\s+(?:number|code)?[:\s-]+([A-Z0-9]{6})', subject + ' ' + text, re.IGNORECASE)
    confirmation = conf_match.group(1) if conf_match else None
    
    # Extract flight details
    flights = []
    
    # Look for city pairs and dates
    # Common patterns: SFO to ORD, ORD to TVC, etc.
    flight_patterns = [
        r'([A-Z]{3})\s+to\s+([A-Z]{3})',
        r'Depart[ing]*\s+([A-Z]{3})',
        r'Arriv[ing]*\s+([A-Z]{3})',
    ]
    
    # Look for dates
    date_patterns = [
        r'((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})',
        r'(\d{1,2}/\d{1,2}/\d{4})',
    ]
    
    # Extract amounts
    amounts = extract_amounts(body + text)
    
    # Look for total
    total_match = re.search(r'Total[:\s]+\$?\s*([\d,]+\.\d{2})', text, re.IGNORECASE)
    total_amount = total_match.group(1) if total_match else None
    
    return {
        'type': 'United Airlines Flight',
        'date': date,
        'subject': subject,
        'confirmation': confirmation,
        'amounts_found': amounts,
        'total': total_amount,
        'text_sample': text[:500]
    }

def main():
    """Parse all trip emails."""
    with open('/Users/ericbrown/.openclaw/workspace/trip_details.json', 'r') as f:
        emails = json.load(f)
    
    print("="*80)
    print("TRIP EXPENSE ANALYSIS - September/October 2025")
    print("="*80)
    
    trip_items = []
    
    for email in emails:
        subject = email['subject']
        from_addr = email['from']
        
        print(f"\n{'='*80}")
        print(f"Date: {email['date']}")
        print(f"From: {from_addr}")
        print(f"Subject: {subject}")
        
        if 'United Airlines' in from_addr and ('booking confirmation' in subject or 'Itinerary' in subject):
            details = parse_united_booking(email)
            print(f"\n  Type: {details['type']}")
            if details['confirmation']:
                print(f"  Confirmation: {details['confirmation']}")
            if details['total']:
                print(f"  Total: ${details['total']}")
            if details['amounts_found']:
                print(f"  Amounts found: {', '.join(details['amounts_found'][:5])}")
            
            trip_items.append(details)
        
        elif 'hotel' in subject.lower() or 'montage' in email['body'].lower():
            print(f"  Type: Hotel/Lodging")
            amounts = extract_amounts(email['body'])
            if amounts:
                print(f"  Amounts found: {', '.join(amounts[:5])}")
            trip_items.append({
                'type': 'Hotel/Lodging',
                'date': email['date'],
                'subject': subject,
                'amounts_found': amounts
            })
        
        elif 'rental car' in subject.lower() or 'rental car' in email['body'].lower():
            print(f"  Type: Rental Car")
            amounts = extract_amounts(email['body'])
            if amounts:
                print(f"  Amounts found: {', '.join(amounts[:5])}")
            trip_items.append({
                'type': 'Rental Car',
                'date': email['date'],
                'subject': subject,
                'amounts_found': amounts
            })
    
    print(f"\n{'='*80}")
    print(f"\nTotal trip-related items found: {len(trip_items)}")
    
    # Calculate total if possible
    all_amounts = []
    for item in trip_items:
        if 'total' in item and item['total']:
            all_amounts.append(clean_amount(item['total']))
        elif 'amounts_found' in item:
            for amt in item['amounts_found']:
                cleaned = clean_amount(amt)
                if cleaned > 0:
                    all_amounts.append(cleaned)
    
    if all_amounts:
        print(f"\nAmounts extracted: ${', $'.join(f'{amt:.2f}' for amt in all_amounts[:10])}")
    
    # Save parsed data
    output_file = '/Users/ericbrown/.openclaw/workspace/trip_parsed.json'
    with open(output_file, 'w') as f:
        json.dump(trip_items, f, indent=2)
    print(f"\nParsed data saved to: {output_file}")

if __name__ == "__main__":
    main()
