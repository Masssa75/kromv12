#!/usr/bin/env python3
import os
from datetime import datetime, timedelta, timezone
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/Users/marcschwyn/Desktop/projects/KROMV12/.env')

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("ERROR: Missing Supabase credentials in .env file")
    exit(1)

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

print("=== ATH Cron Job Status Check ===\n")

# Check tokens with ATH data
ath_data = supabase.table('crypto_calls') \
    .select('id, ticker, ath_price, ath_timestamp, ath_roi_percent, ath_last_checked') \
    .neq('ath_price', None) \
    .execute()

total_with_ath = len(ath_data.data)
print(f"Total tokens with ATH data: {total_with_ath}")

# Check tokens processed in last 2 hours
two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
recent_checks = [t for t in ath_data.data if t.get('ath_last_checked') and 
                datetime.fromisoformat(t['ath_last_checked'].replace('Z', '+00:00')) > two_hours_ago]

print(f"Tokens checked in last 2 hours: {len(recent_checks)}")

# Look for high ROI tokens that should have triggered notifications
high_roi_tokens = [t for t in ath_data.data if t.get('ath_roi_percent', 0) > 10]
print(f"\nTokens with ATH ROI > 10%: {len(high_roi_tokens)}")

# Show recent high ROI tokens
recent_high_roi = [t for t in high_roi_tokens if t.get('ath_last_checked') and 
                   datetime.fromisoformat(t['ath_last_checked'].replace('Z', '+00:00')) > two_hours_ago]

if recent_high_roi:
    print(f"\nHigh ROI tokens updated in last 2 hours:")
    for token in sorted(recent_high_roi, key=lambda x: x['ath_roi_percent'], reverse=True)[:10]:
        roi = token['ath_roi_percent']
        last_checked = token.get('ath_last_checked', 'Never')
        print(f"  - {token['ticker']}: +{roi:.1f}% (checked: {last_checked})")
else:
    print("\nNo high ROI tokens were updated in the last 2 hours")

# Check processing pattern
print("\n=== Processing Pattern ===")
if ath_data.data:
    # Sort by last checked time
    sorted_tokens = sorted([t for t in ath_data.data if t.get('ath_last_checked')], 
                          key=lambda x: x['ath_last_checked'])
    
    if sorted_tokens:
        oldest = sorted_tokens[0]
        newest = sorted_tokens[-1]
        
        oldest_time = datetime.fromisoformat(oldest['ath_last_checked'].replace('Z', '+00:00'))
        newest_time = datetime.fromisoformat(newest['ath_last_checked'].replace('Z', '+00:00'))
        
        print(f"Oldest check: {oldest['ticker']} at {oldest['ath_last_checked']}")
        print(f"Newest check: {newest['ticker']} at {newest['ath_last_checked']}")
        print(f"Time span: {(newest_time - oldest_time).total_seconds() / 3600:.1f} hours")
        
        # Check if processing is happening regularly
        now = datetime.now(timezone.utc)
        time_since_last = (now - newest_time).total_seconds() / 60
        print(f"\nTime since last check: {time_since_last:.1f} minutes")
        
        if time_since_last > 10:
            print("⚠️  WARNING: No processing in last 10 minutes - cron job may be stopped")
        else:
            print("✅ Cron job appears to be running")

# Check for tokens that should be processed
tokens_needing_check = supabase.table('crypto_calls') \
    .select('id', count='exact') \
    .neq('pool_address', None) \
    .neq('price_at_call', None) \
    .execute()

print(f"\nTokens needing ATH check: {tokens_needing_check.count}")

# Sample of tokens being processed
print("\n=== Recent Processing Sample ===")
recent_sample = sorted(recent_checks, key=lambda x: x['ath_last_checked'], reverse=True)[:5]
for token in recent_sample:
    roi = token.get('ath_roi_percent', 0)
    print(f"{token['ticker']}: ATH ROI +{roi:.1f}% (checked {token['ath_last_checked']})")