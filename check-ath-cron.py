#!/usr/bin/env python3
import os
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/Users/marcschwyn/Desktop/projects/KROMV12/.env')

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("ERROR: Missing Supabase credentials in .env file")
    exit(1)

print("=== ATH Cron Job Status Check ===\n")

# Base API URL
api_url = f"{SUPABASE_URL}/rest/v1"
headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
}

# Check tokens with ATH data
response = requests.get(
    f"{api_url}/crypto_calls",
    headers=headers,
    params={
        "select": "id,ticker,ath_price,ath_timestamp,ath_roi_percent,ath_last_checked",
        "ath_price": "not.is.null",
        "limit": "5000"
    }
)
ath_data = response.json()

total_with_ath = len(ath_data)
print(f"Total tokens with ATH data: {total_with_ath}")

# Check tokens processed in last 2 hours
two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
recent_checks = []
high_roi_tokens = []

for token in ath_data:
    roi = token.get('ath_roi_percent')
    if roi is not None and roi > 10:
        high_roi_tokens.append(token)
    
    if token.get('ath_last_checked'):
        try:
            check_time = datetime.fromisoformat(token['ath_last_checked'].replace('Z', '+00:00'))
            if check_time > two_hours_ago:
                recent_checks.append(token)
        except:
            pass

print(f"Tokens checked in last 2 hours: {len(recent_checks)}")
print(f"\nTokens with ATH ROI > 10%: {len(high_roi_tokens)}")

# Show recent high ROI tokens
recent_high_roi = [t for t in high_roi_tokens if t in recent_checks]

if recent_high_roi:
    print(f"\nHigh ROI tokens updated in last 2 hours:")
    for token in sorted(recent_high_roi, key=lambda x: x.get('ath_roi_percent', 0), reverse=True)[:10]:
        roi = token.get('ath_roi_percent', 0)
        last_checked = token.get('ath_last_checked', 'Never')
        print(f"  - {token['ticker']}: +{roi:.1f}% (checked: {last_checked})")
else:
    print("\nNo high ROI tokens were updated in the last 2 hours")

# Check processing pattern
print("\n=== Processing Pattern ===")
if ath_data:
    # Sort by last checked time
    sorted_tokens = sorted([t for t in ath_data if t.get('ath_last_checked')], 
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

# Sample of tokens being processed
print("\n=== Recent Processing Sample ===")
recent_sample = sorted(recent_checks, key=lambda x: x.get('ath_last_checked', ''), reverse=True)[:10]
for token in recent_sample:
    roi = token.get('ath_roi_percent', 0)
    ath_time = token.get('ath_timestamp', 'Unknown')
    if ath_time != 'Unknown':
        try:
            ath_dt = datetime.fromisoformat(ath_time.replace('Z', '+00:00'))
            ath_time = ath_dt.strftime('%Y-%m-%d %H:%M UTC')
        except:
            pass
    print(f"{token['ticker']}: ATH ROI +{roi:.1f}% | ATH at {ath_time}")

# Check specific cron job execution
print("\n=== Checking Supabase Edge Function Logs ===")
print("To see recent executions, run:")
print("supabase functions logs crypto-ath-update --limit 10")