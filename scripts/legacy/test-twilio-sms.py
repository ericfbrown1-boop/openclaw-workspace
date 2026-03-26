#!/usr/bin/env python3
"""Test Twilio SMS sending after A2P 10DLC registration"""

from twilio.rest import Client

# Twilio credentials
ACCOUNT_SID = "ACdb9bf5270e6a9a5c9df25557309d6478"
AUTH_TOKEN = "6867632c5dbe17b98027753f641c69b6"

# Phone numbers
TOLL_FREE = "+18333027822"
LOCAL_CA = "+16505296717"
ERIC_CELL = "+15712153060"

def test_sms(from_number, phone_label):
    """Test SMS sending from a specific Twilio number"""
    try:
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        
        message = client.messages.create(
            body=f"Twilio SMS test from {phone_label}. A2P 10DLC registration complete!",
            from_=from_number,
            to=ERIC_CELL
        )
        
        print(f"✅ SUCCESS from {phone_label} ({from_number})")
        print(f"   Message SID: {message.sid}")
        print(f"   Status: {message.status}")
        return True
        
    except Exception as e:
        print(f"❌ FAILED from {phone_label} ({from_number})")
        print(f"   Error: {str(e)}")
        return False

def main():
    print("Testing Twilio SMS after A2P 10DLC registration (36 hours)...\n")
    
    # Test toll-free number
    result1 = test_sms(TOLL_FREE, "Toll-Free")
    print()
    
    # Test local CA number
    result2 = test_sms(LOCAL_CA, "Local CA")
    print()
    
    if result1 and result2:
        print("🎉 Both SMS tests PASSED! Twilio is ready for production use.")
    elif result1 or result2:
        print("⚠️ Partial success - one number working, check the other.")
    else:
        print("⚠️ Both tests FAILED - check A2P campaign approval status in Twilio console.")

if __name__ == "__main__":
    main()
