#!/usr/bin/env python3
"""
Tax Email Search for 2025 - Comprehensive search for all tax-related items
"""

import imaplib
import email
from email.header import decode_header
from datetime import datetime
import json
import time

# Gmail credentials
EMAIL = "ericfbrown1@gmail.com"
PASSWORD = "jplmfcfecipqwkgi"

# Primary search terms (simplified to avoid IMAP complexity)
SEARCH_TERMS = [
    "W-2", "W2", "1099",
    "Cohesity", "Informatica",
    "Morgan Stanley", "Bernstein", "E*Trade",
    "property tax", "mortgage interest",
    "Agrivine", "Manigold", "Ginops", "Soper",
    "charitable", "donation",
    "Traverse City"
]

def connect_gmail():
    """Connect to Gmail"""
    print("Connecting to Gmail...")
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL, PASSWORD)
        print("✓ Connected\n")
        return mail
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def decode_subject(subject):
    """Decode email subject"""
    if not subject:
        return ""
    try:
        decoded = decode_header(subject)[0]
        if isinstance(decoded[0], bytes):
            return decoded[0].decode(decoded[1] or 'utf-8', errors='ignore')
        return str(decoded[0])
    except:
        return str(subject)

def get_email_body(msg):
    """Extract email body"""
    body = ""
    try:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body += payload.decode('utf-8', errors='ignore')
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode('utf-8', errors='ignore')
    except:
        pass
    return body[:500]  # First 500 chars

def classify_tax_item(subject, body, sender):
    """Classify the type of tax item"""
    text = (subject + " " + body + " " + sender).lower()
    
    # Income items
    if "w-2" in text or "w2" in text:
        return "W-2 Wage Income"
    elif "1099" in text:
        if "div" in text:
            return "1099-DIV Dividend Income"
        elif "int" in text:
            return "1099-INT Interest Income"
        elif "b" in text or "broker" in text:
            return "1099-B Broker Statement"
        else:
            return "1099 Income Form"
    elif any(x in text for x in ["rental", "3469 old mission", "100 main"]):
        return "Rental Income"
    elif any(x in text for x in ["farm", "3553 old mission", "cherry", "pear", "grape"]):
        return "Farm Income/Expense"
    elif "dividend" in text:
        return "Investment Dividend"
    elif "interest" in text and "income" in text:
        return "Interest Income"
    
    # Expense items
    elif any(x in text for x in ["agrivine", "manigold", "ginops"]):
        return "Farm Expense"
    elif "soper" in text:
        return "Rental Property Expense"
    elif "property tax" in text:
        return "Property Tax"
    elif "mortgage" in text:
        return "Mortgage Interest"
    elif "charitable" in text or "donation" in text:
        return "Charitable Donation"
    elif "traverse city" in text and ("flight" in text or "hotel" in text or "travel" in text):
        return "Business Travel"
    elif any(x in text for x in ["legal fee", "accounting", "professional"]):
        return "Professional Fees"
    elif "insurance" in text:
        return "Insurance Expense"
    
    return "Other Tax Item"

def search_tax_emails(mail):
    """Search for tax-related emails from 2025"""
    
    results = []
    seen_ids = set()
    
    # Select All Mail folder for comprehensive search
    print("Searching [Gmail]/All Mail...")
    try:
        mail.select('"[Gmail]/All Mail"', readonly=True)
    except:
        print("Trying INBOX instead...")
        mail.select('INBOX', readonly=True)
    
    # Search for emails since Jan 1, 2025
    since_date = "01-Jan-2025"
    
    print(f"Date range: Since {since_date}")
    print(f"Searching for {len(SEARCH_TERMS)} keyword groups...\n")
    
    for term in SEARCH_TERMS:
        print(f"  Searching: {term}...")
        
        try:
            # Simple subject search - more reliable
            search_query = f'(SINCE {since_date} SUBJECT "{term}")'
            status, msg_ids = mail.search(None, search_query)
            
            if status == 'OK' and msg_ids[0]:
                ids = msg_ids[0].split()
                print(f"    Found {len(ids)} emails")
                
                for msg_id in ids:
                    if msg_id in seen_ids:
                        continue
                    seen_ids.add(msg_id)
                    
                    try:
                        status, msg_data = mail.fetch(msg_id, '(RFC822)')
                        if status != 'OK':
                            continue
                        
                        msg = email.message_from_bytes(msg_data[0][1])
                        
                        # Extract details
                        subject = decode_subject(msg.get('Subject', ''))
                        sender = msg.get('From', '')
                        date_str = msg.get('Date', '')
                        
                        # Parse date
                        try:
                            date_tuple = email.utils.parsedate_to_datetime(date_str)
                            date_received = date_tuple.strftime("%Y-%m-%d")
                        except:
                            date_received = date_str
                        
                        # Get body snippet
                        body = get_email_body(msg)
                        
                        # Classify
                        tax_type = classify_tax_item(subject, body, sender)
                        
                        # Generate Gmail link (approximation)
                        gmail_link = f"https://mail.google.com/mail/u/0/#search/{term.replace(' ', '+')}"
                        
                        results.append({
                            "date_received": date_received,
                            "sender": sender,
                            "subject": subject,
                            "description": body[:150],
                            "tax_type": tax_type,
                            "gmail_link": gmail_link,
                            "comments": ""
                        })
                        
                    except Exception as e:
                        print(f"      Error processing email: {e}")
                        continue
            else:
                print(f"    No results")
        
        except Exception as e:
            print(f"    Search error: {e}")
            continue
        
        time.sleep(0.5)  # Rate limiting
    
    return results

def main():
    print("=" * 80)
    print("TAX EMAIL SEARCH - 2025 TAX YEAR")
    print("Searching Jan 1, 2025 - Present")
    print("=" * 80)
    print()
    
    mail = connect_gmail()
    if not mail:
        return None
    
    try:
        results = search_tax_emails(mail)
        
        print("\n" + "=" * 80)
        print(f"FOUND {len(results)} TAX-RELATED EMAILS")
        print("=" * 80)
        
        # Save to JSON
        output_file = "tax_emails_2025.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Saved to: {output_file}")
        
        # Summary by category
        print("\nSUMMARY BY CATEGORY:")
        print("-" * 80)
        
        categories = {}
        for item in results:
            cat = item["tax_type"]
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat:40} {count:3}")
        
        print("\n" + "=" * 80)
        
        return results
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        try:
            mail.close()
            mail.logout()
            print("\n✓ Disconnected")
        except:
            pass

if __name__ == "__main__":
    results = main()
