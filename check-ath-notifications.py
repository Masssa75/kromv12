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

print("=== ATH Notification Analysis ===\n")

# Base API URL
api_url = f"{SUPABASE_URL}/rest/v1"
headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
}

# Get all high ROI tokens with recent ATH updates
two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)

# Query for tokens with high ROI that were recently updated
response = requests.get(
    f"{api_url}/crypto_calls",
    headers=headers,
    params={
        "select": "id,ticker,network,raw_data,ath_price,ath_timestamp,ath_roi_percent,ath_last_checked,price_at_call,buy_timestamp",
        "ath_roi_percent": "gte.10",
        "ath_last_checked": f"gte.{one_day_ago.isoformat()}",
        "order": "ath_roi_percent.desc",
        "limit": "50"
    }
)
high_roi_tokens = response.json()

print(f"Tokens with ATH ROI >= 10% updated in last 24 hours: {len(high_roi_tokens)}")

# Check which ones hit ATH in last 2 hours
recent_ath_hits = []
for token in high_roi_tokens:
    if token.get('ath_timestamp'):
        try:
            ath_time = datetime.fromisoformat(token['ath_timestamp'].replace('Z', '+00:00'))
            if ath_time > two_hours_ago:
                recent_ath_hits.append(token)
        except:
            pass

print(f"Tokens that hit new ATH in last 2 hours: {len(recent_ath_hits)}")

if recent_ath_hits:
    print("\n=== Recent ATH Hits (should have triggered notifications) ===")
    for token in recent_ath_hits[:10]:
        roi = token.get('ath_roi_percent', 0)
        ath_time = token.get('ath_timestamp', 'Unknown')
        if ath_time != 'Unknown':
            try:
                ath_dt = datetime.fromisoformat(ath_time.replace('Z', '+00:00'))
                time_ago = (datetime.now(timezone.utc) - ath_dt).total_seconds() / 60
                ath_time = f"{time_ago:.0f} minutes ago"
            except:
                pass
        
        # Get group name from raw_data
        group_name = "Unknown"
        if token.get('raw_data') and 'group' in token['raw_data']:
            group_name = token['raw_data']['group'].get('name', 'Unknown')
        
        print(f"\n{token['ticker']} ({token['network']})")
        print(f"  ATH ROI: +{roi:.1f}%")
        print(f"  ATH hit: {ath_time}")
        print(f"  Group: {group_name}")
        print(f"  Entry: ${token.get('price_at_call', 0):.6f}")
        print(f"  ATH: ${token.get('ath_price', 0):.6f}")

# Check last few hours of processing
print("\n=== Processing Timeline (Last 4 Hours) ===")
four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=4)

response = requests.get(
    f"{api_url}/crypto_calls",
    headers=headers,
    params={
        "select": "ath_last_checked,ath_roi_percent",
        "ath_last_checked": f"gte.{four_hours_ago.isoformat()}",
        "ath_roi_percent": "not.is.null",
        "order": "ath_last_checked.desc",
        "limit": "500"
    }
)
recent_checks = response.json()

# Group by hour
hourly_counts = {}
high_roi_by_hour = {}

for check in recent_checks:
    if check.get('ath_last_checked'):
        try:
            check_time = datetime.fromisoformat(check['ath_last_checked'].replace('Z', '+00:00'))
        except:
            # Handle fractional seconds
            timestamp = check['ath_last_checked'].split('.')[0] + '+00:00'
            check_time = datetime.fromisoformat(timestamp)
        hour_key = check_time.strftime('%Y-%m-%d %H:00')
        
        hourly_counts[hour_key] = hourly_counts.get(hour_key, 0) + 1
        
        if check.get('ath_roi_percent', 0) > 10:
            high_roi_by_hour[hour_key] = high_roi_by_hour.get(hour_key, 0) + 1

for hour in sorted(hourly_counts.keys(), reverse=True)[:4]:
    high_count = high_roi_by_hour.get(hour, 0)
    print(f"{hour} UTC: {hourly_counts[hour]} tokens processed ({high_count} with >10% ROI)")

print("\n=== Recommendation ===")
if len(recent_checks) == 0 or (datetime.now(timezone.utc) - datetime.fromisoformat(recent_checks[0]['ath_last_checked'].replace('Z', '+00:00'))).total_seconds() > 1800:
    print("⚠️ ATH cron job appears to be STOPPED!")
    print("Action needed: Check pg_cron configuration or restart the cron job")
else:
    print("✅ ATH processing is active")
    if recent_ath_hits:
        print(f"⚠️ {len(recent_ath_hits)} tokens hit new ATH but you didn't receive notifications")
        print("Possible issues:")
        print("- Telegram bot token or group ID incorrect")
        print("- Notification edge function failing")
        print("- Check crypto-ath-notifier logs")