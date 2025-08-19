#!/usr/bin/env python3
import os
from supabase import create_client
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(supabase_url, supabase_key)

print("Checking ATH tracking status...\n")

# Check recent ATH updates
try:
    response = supabase.table('crypto_calls').select(
        'ticker,ath_price,ath_roi_percent,ath_last_checked,liquidity_usd'
    ).order('ath_last_checked', desc=True).limit(10).execute()
    
    print("=== Most Recently Checked Tokens ===")
    for row in response.data[:5]:
        last_checked = row['ath_last_checked'] if row['ath_last_checked'] else 'Never'
        ath_price = row['ath_price'] if row['ath_price'] else 0
        price_str = f"${ath_price:.8f}" if ath_price and ath_price < 1 else f"${ath_price}"
        print(f"{row['ticker']}: Last checked {last_checked}, ATH {price_str}")
    
    # Check when was the last update
    if response.data and response.data[0]['ath_last_checked']:
        last_update = datetime.fromisoformat(response.data[0]['ath_last_checked'].replace('Z', '+00:00'))
        time_since = datetime.now(last_update.tzinfo) - last_update
        print(f"\n⏰ Last ATH check was {time_since.total_seconds() / 60:.1f} minutes ago")
        
        if time_since.total_seconds() > 3600:  # More than 1 hour
            print("⚠️  WARNING: No updates in over an hour!")
    
    # Check tokens with recent new ATHs
    print("\n=== Recent High ROI Tokens ===")
    recent_ath = supabase.table('crypto_calls').select(
        'ticker,ath_roi_percent,ath_last_checked'
    ).gt('ath_roi_percent', 10).order('ath_last_checked', desc=True).limit(5).execute()
    
    if recent_ath.data:
        for row in recent_ath.data:
            print(f"{row['ticker']}: {row['ath_roi_percent']:.1f}% ROI")
    else:
        print("No recent ATH notifications found")
    
    # Check active tokens (with good liquidity)
    print("\n=== Active Tokens Being Tracked ===")
    active = supabase.table('crypto_calls').select(
        'count'
    ).gt('liquidity_usd', 15000).execute()
    
    print(f"Total tokens with >$15K liquidity: {active.data[0]['count']}")
    
    # Check if ultra tracker marks tokens as dead
    dead_tokens = supabase.table('crypto_calls').select(
        'count'
    ).eq('is_dead_token', True).execute()
    
    if dead_tokens.data:
        print(f"Tokens marked as dead: {dead_tokens.data[0]['count']}")
        
except Exception as e:
    print(f"Error querying database: {e}")