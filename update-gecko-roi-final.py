#!/usr/bin/env python3
"""
Final fix for gecko_trending tokens to ensure proper ROI display.
- Marks them as alive (is_dead = false)
- Updates ROI with proper calculation
- Ensures they're tracked by ultra-tracker
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
    # Get all gecko_trending tokens
    response = supabase.table("crypto_calls").select(
        "id, ticker, price_at_call, current_price, roi_percent, is_dead"
    ).eq("source", "gecko_trending").execute()
    
    if not response.data:
        print("⚠️ No gecko_trending tokens found")
        exit(0)
    
    tokens = response.data
    print(f"📊 Processing {len(tokens)} gecko_trending tokens")
    
    updated_count = 0
    for token in tokens:
        # Calculate ROI if we have prices
        if token['price_at_call'] and token['current_price']:
            price_at_call = float(token['price_at_call'])
            current_price = float(token['current_price'])
            
            if price_at_call > 0:
                roi = ((current_price - price_at_call) / price_at_call) * 100
            else:
                roi = 0
        else:
            roi = 0
        
        # Update token to be alive with proper ROI
        update_data = {
            "is_dead": False,
            "roi_percent": roi
        }
        
        update_response = supabase.table("crypto_calls").update(
            update_data
        ).eq("id", token['id']).execute()
        
        if update_response.data:
            status = "✅" if roi != 0 else "⚠️"
            print(f"{status} {token['ticker']}: ROI={roi:.2f}%, is_dead=False")
            updated_count += 1
    
    print(f"\n✅ Updated {updated_count} tokens successfully")
    print("🔄 These tokens will now be tracked by ultra-tracker every minute")
    
except Exception as e:
    print(f"❌ Error: {e}")