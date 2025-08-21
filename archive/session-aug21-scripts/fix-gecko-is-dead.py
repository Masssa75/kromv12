#!/usr/bin/env python3
"""
Fix is_dead flag for gecko_trending tokens.
These are actively traded tokens from GeckoTerminal trending list, they should not be marked as dead.
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
    # Mark all gecko_trending tokens as alive (is_dead = false)
    response = supabase.table("crypto_calls").update({
        "is_dead": False
    }).eq("source", "gecko_trending").execute()
    
    if response.data:
        print(f"✅ Updated {len(response.data)} gecko_trending tokens to is_dead=false")
        for token in response.data:
            print(f"  - {token['ticker']}: is_dead={token['is_dead']}")
    else:
        print("⚠️ No tokens updated")
        
except Exception as e:
    print(f"❌ Error updating tokens: {e}")