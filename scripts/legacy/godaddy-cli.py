#!/usr/bin/env python3
"""
GoDaddy API client for Jarvis
Usage:
  godaddy-cli.py domains              - List all domains
  godaddy-cli.py dns <domain>         - List DNS records for domain
  godaddy-cli.py add-a <domain> <name> <ip> - Add A record
  godaddy-cli.py add-mx <domain> <priority> <host> - Add MX record
  godaddy-cli.py delete <domain> <type> <name> - Delete DNS record
"""

import sys
import json
import requests

API_KEY = "dL3r9iBF1DAQ_Ki1z5GcCGFP1sf2KC8vLwB"
API_SECRET = "XLqskopCtMGANxRysNNJ9A"
BASE_URL = "https://api.godaddy.com/v1"

HEADERS = {
    "Authorization": f"sso-key {API_KEY}:{API_SECRET}",
    "Content-Type": "application/json"
}

def list_domains():
    """List all domains in account"""
    url = f"{BASE_URL}/domains"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        domains = response.json()
        for domain in domains:
            print(f"📌 {domain['domain']} (expires: {domain.get('expires', 'N/A')})")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

def list_dns_records(domain):
    """List DNS records for a domain"""
    url = f"{BASE_URL}/domains/{domain}/records"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        records = response.json()
        if not records:
            print(f"ℹ️  No DNS records configured for {domain}")
        for record in records:
            print(f"{record['type']:6} {record['name']:20} → {record['data']} (TTL: {record['ttl']})")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

def add_a_record(domain, name, ip, ttl=3600):
    """Add an A record"""
    url = f"{BASE_URL}/domains/{domain}/records"
    data = [{
        "type": "A",
        "name": name,
        "data": ip,
        "ttl": ttl
    }]
    
    response = requests.patch(url, headers=HEADERS, json=data)
    
    if response.status_code in [200, 201]:
        print(f"✅ Added A record: {name}.{domain} → {ip}")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

def add_mx_record(domain, priority, host, ttl=3600):
    """Add an MX record"""
    url = f"{BASE_URL}/domains/{domain}/records"
    data = [{
        "type": "MX",
        "name": "@",
        "data": host,
        "priority": priority,
        "ttl": ttl
    }]
    
    response = requests.patch(url, headers=HEADERS, json=data)
    
    if response.status_code in [200, 201]:
        print(f"✅ Added MX record: {domain} → {host} (priority: {priority})")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

def delete_record(domain, record_type, name):
    """Delete a DNS record"""
    url = f"{BASE_URL}/domains/{domain}/records/{record_type}/{name}"
    response = requests.delete(url, headers=HEADERS)
    
    if response.status_code == 204:
        print(f"✅ Deleted {record_type} record: {name}.{domain}")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "domains":
        list_domains()
    elif command == "dns":
        if len(sys.argv) < 3:
            print("Usage: godaddy-cli.py dns <domain>")
            sys.exit(1)
        list_dns_records(sys.argv[2])
    elif command == "add-a":
        if len(sys.argv) < 5:
            print("Usage: godaddy-cli.py add-a <domain> <name> <ip>")
            sys.exit(1)
        add_a_record(sys.argv[2], sys.argv[3], sys.argv[4])
    elif command == "add-mx":
        if len(sys.argv) < 5:
            print("Usage: godaddy-cli.py add-mx <domain> <priority> <host>")
            sys.exit(1)
        add_mx_record(sys.argv[2], int(sys.argv[3]), sys.argv[4])
    elif command == "delete":
        if len(sys.argv) < 5:
            print("Usage: godaddy-cli.py delete <domain> <type> <name>")
            sys.exit(1)
        delete_record(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)
