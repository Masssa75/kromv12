#!/usr/bin/env python3
import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/Users/marcschwyn/Desktop/projects/KROMV12/.env')

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("ERROR: Missing Supabase credentials in .env file")
    exit(1)

print("=== ATH Processing Status ===\n")

# Base API URL
api_url = f"{SUPABASE_URL}/rest/v1"
headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Prefer": "count=exact"
}

# 1. Count tokens that still need ATH calculation
response = requests.get(
    f"{api_url}/crypto_calls",
    headers=headers,
    params={
        "select": "id",
        "pool_address": "not.is.null",
        "price_at_call": "not.is.null",
        "ath_price": "is.null",
        "limit": "0"
    }
)
without_ath = int(response.headers.get('content-range', '0').split('/')[-1])

# 2. Count total eligible tokens
response2 = requests.get(
    f"{api_url}/crypto_calls",
    headers=headers,
    params={
        "select": "id",
        "pool_address": "not.is.null",
        "price_at_call": "not.is.null",
        "limit": "0"
    }
)
total_eligible = int(response2.headers.get('content-range', '0').split('/')[-1])

# 3. Get most recent processing
response3 = requests.get(
    f"{api_url}/crypto_calls",
    headers={'apikey': SUPABASE_SERVICE_ROLE_KEY},
    params={
        "select": "ticker,ath_last_checked,ath_roi_percent",
        "ath_last_checked": "not.is.null",
        "order": "ath_last_checked.desc",
        "limit": "10"
    }
)
latest = response3.json()

print(f"📊 ATH Coverage Statistics:")
print(f"- Total eligible tokens: {total_eligible:,}")
print(f"- Tokens with ATH data: {total_eligible - without_ath:,}")
print(f"- Tokens without ATH: {without_ath:,}")
print(f"- Coverage: {((total_eligible - without_ath) / total_eligible * 100):.1f}%")

print(f"\n⏱️ Processing Rate:")
if latest:
    # Calculate processing rate
    now = datetime.now(timezone.utc)
    try:
        oldest_time = datetime.fromisoformat(latest[-1]['ath_last_checked'].replace('Z', '+00:00'))
        newest_time = datetime.fromisoformat(latest[0]['ath_last_checked'].replace('Z', '+00:00'))
    except:
        # Handle fractional seconds
        oldest_ts = latest[-1]['ath_last_checked'].split('.')[0] + '+00:00'
        newest_ts = latest[0]['ath_last_checked'].split('.')[0] + '+00:00'
        oldest_time = datetime.fromisoformat(oldest_ts)
        newest_time = datetime.fromisoformat(newest_ts)
    
    time_span = (newest_time - oldest_time).total_seconds() / 60  # minutes
    if time_span > 0:
        rate = len(latest) / time_span
        print(f"- Current rate: {rate:.1f} tokens/minute")
        print(f"- Time to complete remaining: {without_ath / rate:.0f} minutes (~{without_ath / rate / 60:.1f} hours)")
    
    print(f"\n🔄 Most Recently Processed:")
    for token in latest[:5]:
        roi = token.get('ath_roi_percent', 0)
        try:
            check_time = datetime.fromisoformat(token['ath_last_checked'].replace('Z', '+00:00'))
        except:
            check_ts = token['ath_last_checked'].split('.')[0] + '+00:00'
            check_time = datetime.fromisoformat(check_ts)
        mins_ago = (now - check_time).total_seconds() / 60
        print(f"- {token['ticker']}: {mins_ago:.0f} min ago (ROI: +{roi:.1f}%)")

# 4. Check for any stuck tokens
print(f"\n🔍 Checking for problematic tokens...")
response4 = requests.get(
    f"{api_url}/crypto_calls",
    headers={'apikey': SUPABASE_SERVICE_ROLE_KEY},
    params={
        "select": "ticker,network,pool_address",
        "pool_address": "not.is.null",
        "price_at_call": "not.is.null",
        "ath_price": "is.null",
        "limit": "5"
    }
)
stuck_tokens = response4.json()

if stuck_tokens:
    print("Next tokens in queue (without ATH):")
    for token in stuck_tokens:
        print(f"- {token['ticker']} ({token['network']})")
        
print(f"\n✅ Summary:")
if without_ath == 0:
    print("🎉 ALL TOKENS HAVE BEEN PROCESSED!")
elif without_ath < 50:
    print(f"Almost done! Only {without_ath} tokens left to process.")
else:
    print(f"Processing continues. {without_ath} tokens remaining.")