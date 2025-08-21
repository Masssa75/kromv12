#!/usr/bin/env python3
"""
Test if we can write to the database like ultra-tracker would
"""

import os
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client with service role key
url = os.getenv("SUPABASE_URL")
service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not service_key:
    print("❌ Missing Supabase credentials")
    exit(1)

supabase = create_client(url, service_key)

try:
    # Get a CHEW token to test with
    response = supabase.table("crypto_calls").select(
        "id, ticker, current_price, ath_last_checked"
    ).eq("ticker", "CHEW").limit(1).execute()
    
    if not response.data:
        print("❌ No CHEW token found")
        exit(1)
    
    token = response.data[0]
    print(f"Testing update for {token['ticker']} (ID: {token['id']})")
    print(f"Current values: price={token['current_price']}, last_checked={token['ath_last_checked']}")
    
    # Try to update it like ultra-tracker would
    update_data = {
        "current_price": 0.0004228,  # Price from DexScreener
        "ath_last_checked": datetime.utcnow().isoformat(),
        "price_updated_at": datetime.utcnow().isoformat()
    }
    
    update_response = supabase.table("crypto_calls").update(
        update_data
    ).eq("id", token['id']).execute()
    
    if update_response.data:
        print(f"✅ Successfully updated token!")
        print(f"New values: {update_response.data[0]}")
    else:
        print(f"❌ Update failed - no data returned")
        
except Exception as e:
    print(f"❌ Error: {e}")