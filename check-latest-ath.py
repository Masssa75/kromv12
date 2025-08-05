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

# Base API URL
api_url = f"{SUPABASE_URL}/rest/v1"
headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
}

# Get most recently checked tokens
response = requests.get(
    f"{api_url}/crypto_calls",
    headers=headers,
    params={
        "select": "ticker,ath_last_checked,ath_roi_percent",
        "ath_last_checked": "not.is.null",
        "order": "ath_last_checked.desc",
        "limit": "10"
    }
)

tokens = response.json()
if tokens:
    print("=== Most Recently Checked Tokens ===")
    now = datetime.now(timezone.utc)
    
    for token in tokens:
        check_time = datetime.fromisoformat(token['ath_last_checked'].replace('Z', '+00:00'))
        minutes_ago = (now - check_time).total_seconds() / 60
        roi = token.get('ath_roi_percent', 0)
        
        print(f"{token['ticker']}: checked {minutes_ago:.1f} min ago (ROI: +{roi:.1f}%)")
    
    # Check if processing resumed
    if tokens:
        latest_check = datetime.fromisoformat(tokens[0]['ath_last_checked'].replace('Z', '+00:00'))
        if (now - latest_check).total_seconds() < 120:  # Within 2 minutes
            print("\n✅ ATH processing is active!")
        else:
            print(f"\n⚠️ Last check was {(now - latest_check).total_seconds() / 60:.1f} minutes ago")