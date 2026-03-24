#!/usr/bin/env python3
"""
Comprehensive Tax Email Search for 2025
Searches Gmail via IMAP for all tax-related items from Jan 1, 2025 - Feb 9, 2026
"""

import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime
import json

# Gmail credentials
EMAIL = "ericfbrown1@gmail.com"
PASSWORD = "jplmfcfecipqwkgi"

# Tax-related search keywords
INCOME_KEYWORDS = [
    "W-2", "W2", "1099", "Cohesity", "Informatica",
    "Morgan Stanley", "Bernstein", "E*Trade", "E-Trade",
    "dividend", "interest income", "tax form",
    "rental income", "3469 Old Mission", "100 Main Street Los Altos",
    "farm income", "3553 Old Mission", "cherry", "cherries", "pear", "pears", "grape", "grapes",
    "stock income", "investment income", "Pillsbury", "retirement", "pension"
]

EXPENSE_KEYWORDS = [
    "Agrivine", "Manigold", "Ginops",
    "farm expense", "farm supply", "farm equipment",
    "Soper Services", "rental expense", "property repair", "property maintenance",
    "property tax", "mortgage interest", "Wells Fargo mortgage", "Morgan Stanley mortgage",
    "charitable donation", "donation receipt",
    "business travel", "Traverse City", "flight", "hotel",
    "legal fees", "accounting fees", "professional fees",
    "farm insurance", "rental insurance", "property insurance"
]

ALL_KEYWORDS = INCOME_KEYWORDS + EXPENSE_KEYWORDS

def connect_gmail():
    """Connect to Gmail via IMAP"""
    print("Connecting to Gmail...")
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL, PASSWORD)
    return mail

def decode_email_subject(subject):
    """Decode email subject handling various encodings"""
    if subject is None:
        return ""
    decoded_parts = decode_header(subject)
    result = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            result += part.decode(encoding if encoding else 'utf-8', errors='ignore')
        else:
            result += part
    return result

def get_email_body(msg):
    """Extract email body text"""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                try:
                    body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            pass
    return body

def search_emails_by_keyword(mail, keyword, start_date="01-Jan-2025", end_date="09-Feb-2026"):
    """Search emails by keyword within date range"""
    print(f"  Searching for: {keyword}")
    
    # Search criteria - using Gmail's search syntax
    search_criteria = f'(SINCE "{start_date}" BEFORE "{end_date}" OR SUBJECT "{keyword}" OR BODY "{keyword}")'
    
    results = []
    
    # Search in all folders
    folders = ['INBOX', '[Gmail]/All Mail', '[Gmail]/Sent Mail']
    
    for folder in folders:
        try:
            mail.select(folder)
            status, messages = mail.search(None, search_criteria)
            
            if status == "OK":
                email_ids = messages[0].split()
                print(f"    Found {len(email_ids)} emails in {folder}")
                
                for email_id in email_ids:
                    try:
                        status, msg_data = mail.fetch(email_id, "(RFC822)")
                        if status == "OK":
                            msg = email.message_from_bytes(msg_data[0][1])
                            
                            # Extract details
                            subject = decode_email_subject(msg["Subject"])
                            sender = msg["From"]
                            date_str = msg["Date"]
                            message_id = msg["Message-ID"]
                            
                            # Parse date
                            try:
                                date_tuple = email.utils.parsedate_to_datetime(date_str)
                                date_received = date_tuple.strftime("%Y-%m-%d")
                            except:
                                date_received = date_str
                            
                            # Get body snippet
                            body = get_email_body(msg)
                            body_snippet = body[:200] if body else ""
                            
                            # Check if keyword is actually in subject or body
                            if keyword.lower() in subject.lower() or keyword.lower() in body.lower():
                                results.append({
                                    "keyword": keyword,
                                    "folder": folder,
                                    "date_received": date_received,
                                    "sender": sender,
                                    "subject": subject,
                                    "body_snippet": body_snippet,
                                    "message_id": message_id,
                                    "gmail_link": f"https://mail.google.com/mail/u/0/#inbox/{email_id.decode()}"
                                })
                    except Exception as e:
                        print(f"    Error processing email {email_id}: {e}")
                        continue
        except Exception as e:
            print(f"    Error searching {folder}: {e}")
            continue
    
    return results

def classify_tax_type(subject, body_snippet, keyword):
    """Classify the type of tax income or expense"""
    text = (subject + " " + body_snippet).lower()
    
    # Income classifications
    if any(k in text for k in ["w-2", "w2", "form w-2"]):
        return "W-2 Wage Income"
    elif "1099" in text:
        if "div" in text:
            return "1099-DIV Dividend Income"
        elif "int" in text:
            return "1099-INT Interest Income"
        elif "misc" in text or "nec" in text:
            return "1099-MISC/NEC Income"
        else:
            return "1099 Income (Type TBD)"
    elif any(k in text for k in ["rental", "3469 old mission", "100 main street"]):
        return "Rental Income"
    elif any(k in text for k in ["farm", "3553 old mission", "cherry", "pear", "grape"]):
        return "Farm Income"
    elif any(k in text for k in ["dividend", "stock", "investment"]):
        return "Investment Income"
    elif "pension" in text or "retirement" in text:
        return "Retirement/Pension Income"
    
    # Expense classifications
    elif any(k in text for k in ["agrivine", "manigold", "ginops"]) or "farm" in text:
        return "Farm Expense"
    elif any(k in text for k in ["soper", "repair", "maintenance"]) and "rental" in text:
        return "Rental Property Expense"
    elif "property tax" in text:
        return "Property Tax"
    elif "mortgage" in text:
        return "Mortgage Interest"
    elif "charitable" in text or "donation" in text:
        return "Charitable Donation"
    elif any(k in text for k in ["flight", "hotel", "travel"]) and "traverse" in text:
        return "Business Travel (Farm)"
    elif any(k in text for k in ["legal", "accounting", "professional"]):
        return "Professional Fees"
    elif "insurance" in text:
        return "Insurance Expense"
    
    return "Other/Unclassified"

def main():
    """Main execution"""
    print("=" * 80)
    print("TAX EMAIL SEARCH - 2025 TAX YEAR")
    print("Searching: Jan 1, 2025 - Feb 9, 2026")
    print("=" * 80)
    
    mail = connect_gmail()
    
    all_results = []
    seen_message_ids = set()
    
    # Search by each keyword
    for keyword in ALL_KEYWORDS:
        results = search_emails_by_keyword(mail, keyword)
        
        # Deduplicate by message ID
        for result in results:
            msg_id = result["message_id"]
            if msg_id not in seen_message_ids:
                seen_message_ids.add(msg_id)
                
                # Classify
                result["tax_type"] = classify_tax_type(
                    result["subject"], 
                    result["body_snippet"],
                    keyword
                )
                
                all_results.append(result)
    
    mail.logout()
    
    print("\n" + "=" * 80)
    print(f"SEARCH COMPLETE: Found {len(all_results)} unique tax-related emails")
    print("=" * 80)
    
    # Save results
    output_file = "tax_emails_2025.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    # Print summary by category
    print("\nSUMMARY BY CATEGORY:")
    print("-" * 80)
    
    categories = {}
    for result in all_results:
        tax_type = result["tax_type"]
        if tax_type not in categories:
            categories[tax_type] = 0
        categories[tax_type] += 1
    
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count}")
    
    print("\n" + "=" * 80)
    print("Next step: Create Google Sheet and populate with this data")
    print("=" * 80)
    
    return all_results

if __name__ == "__main__":
    main()
