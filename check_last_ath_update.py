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

print("Checking ATH update history...\n")

# Check tokens that were updated in the past
response = supabase.table('crypto_calls').select(
    'ticker,ath_last_checked,ath_price,ath_roi_percent,liquidity_usd'
).order('ath_last_checked', desc=True).limit(10).execute()

if response.data:
    print("=== Last Successfully Updated Tokens ===")
    for row in response.data:
        last_checked = row['ath_last_checked']
        # Parse date
        try:
            check_time = datetime.fromisoformat(last_checked.replace('Z', '+00:00'))
            time_ago = datetime.now(check_time.tzinfo) - check_time
            hours_ago = time_ago.total_seconds() / 3600
            print(f"{row['ticker']}: Updated {hours_ago:.1f} hours ago, ATH ROI: {row['ath_roi_percent']:.1f}%")
        except:
            print(f"{row['ticker']}: Updated {last_checked}")
else:
    print("No tokens have been updated with ATH data")

# Check how many tokens need updates
print("\n=== Tokens Needing Updates ===")
needs_update = supabase.table('crypto_calls').select(
    'count'
).is_('ath_last_checked', None).gt('liquidity_usd', 15000).execute()

if needs_update.data:
    print(f"Tokens with >$15K liquidity never checked: {needs_update.data[0]['count']}")

# Check total active tokens
total_active = supabase.table('crypto_calls').select(
    'count'
).gt('liquidity_usd', 15000).execute()

if total_active.data:
    print(f"Total active tokens (>$15K liquidity): {total_active.data[0]['count']}")