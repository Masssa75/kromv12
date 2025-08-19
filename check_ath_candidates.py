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

print("Checking for potential ATH notification candidates...\n")

# Check tokens with high ROI that were updated recently
response = supabase.table('crypto_calls').select(
    'ticker,ath_price,ath_roi_percent,price_at_call,current_price,ath_last_checked,liquidity_usd'
).gt('ath_roi_percent', 250).order('ath_roi_percent', desc=True).limit(20).execute()

print("=== Tokens with >250% ROI ===")
count = 0
for row in response.data[:10]:
    if row['current_price'] and row['ath_price']:
        # Check if current price could be 20% higher than ATH
        potential_increase = ((row['current_price'] - row['ath_price']) / row['ath_price']) * 100 if row['ath_price'] else 0
        if potential_increase > 0:
            print(f"{row['ticker']}: ROI {row['ath_roi_percent']:.1f}%, Current vs ATH: {potential_increase:.1f}% higher")
            count += 1
        elif potential_increase > -20:
            print(f"{row['ticker']}: ROI {row['ath_roi_percent']:.1f}%, Current vs ATH: {potential_increase:.1f}% (close to ATH)")

if count == 0:
    print("No tokens are currently above their ATH")

# Check when ultra tracker last ran successfully
print("\n=== Ultra Tracker Status ===")
last_checked = supabase.table('crypto_calls').select(
    'ath_last_checked'
).not_('ath_last_checked', 'is', None).order('ath_last_checked', desc=True).limit(1).execute()

if last_checked.data:
    last_time = last_checked.data[0]['ath_last_checked']
    try:
        check_time = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
        time_ago = datetime.now(check_time.tzinfo) - check_time
        print(f"Last successful update: {time_ago.total_seconds() / 60:.1f} minutes ago")
    except:
        print(f"Last update: {last_time}")