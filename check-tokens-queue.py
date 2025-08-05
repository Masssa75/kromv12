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

print("=== Investigating Token Queue ===\n")

# Base API URL
api_url = f"{SUPABASE_URL}/rest/v1"
headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
}

# Check tokens that should be in the queue
print("1. Checking tokens eligible for ATH processing:")

# Count tokens with required fields
response = requests.get(
    f"{api_url}/crypto_calls",
    headers={
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Prefer": "count=exact"
    },
    params={
        "select": "id",
        "pool_address": "not.is.null",
        "price_at_call": "not.is.null",
        "is_dead": "not.is.true",
        "limit": "0"
    }
)
total_eligible = int(response.headers.get('content-range', '0').split('/')[-1])
print(f"- Tokens with pool_address and price_at_call: {total_eligible}")

# Count tokens already with ATH data
response2 = requests.get(
    f"{api_url}/crypto_calls",
    headers={
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Prefer": "count=exact"
    },
    params={
        "select": "id",
        "pool_address": "not.is.null",
        "price_at_call": "not.is.null",
        "ath_price": "not.is.null",
        "limit": "0"
    }
)
with_ath = int(response2.headers.get('content-range', '0').split('/')[-1])
print(f"- Tokens already with ATH data: {with_ath}")

# Count tokens marked as dead
response3 = requests.get(
    f"{api_url}/crypto_calls",
    headers={
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Prefer": "count=exact"
    },
    params={
        "select": "id",
        "is_dead": "is.true",
        "limit": "0"
    }
)
dead_tokens = int(response3.headers.get('content-range', '0').split('/')[-1])
print(f"- Tokens marked as dead: {dead_tokens}")

print("\n2. Checking what crypto-ath-update sees:")

# Query exactly what the edge function queries
response4 = requests.get(
    f"{api_url}/crypto_calls",
    headers=headers,
    params={
        "select": "id,ticker,network,pool_address,buy_timestamp,price_at_call,ath_price,ath_timestamp,ath_roi_percent,ath_last_checked,raw_data",
        "pool_address": "not.is.null",
        "price_at_call": "not.is.null",
        "is_dead": "not.is.true",
        "order": "ath_last_checked.asc.nullsfirst",
        "limit": "5"
    }
)
next_tokens = response4.json()

print(f"\nNext 5 tokens in queue:")
for token in next_tokens:
    last_checked = token.get('ath_last_checked', 'Never')
    has_ath = 'Yes' if token.get('ath_price') else 'No'
    print(f"- {token['ticker']}: Last checked: {last_checked}, Has ATH: {has_ath}")

# Check if there's an is_dead column issue
print("\n3. Checking is_dead column:")
response5 = requests.get(
    f"{api_url}/crypto_calls",
    headers={
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Prefer": "count=exact"
    },
    params={
        "select": "id",
        "is_dead": "is.null",
        "limit": "0"
    }
)
null_is_dead = int(response5.headers.get('content-range', '0').split('/')[-1])
print(f"- Tokens with NULL is_dead: {null_is_dead}")

# Try the exact query without is_dead filter
print("\n4. Testing query without is_dead filter:")
response6 = requests.get(
    f"{api_url}/crypto_calls",
    headers=headers,
    params={
        "select": "id,ticker,network,pool_address,ath_last_checked",
        "pool_address": "not.is.null",
        "price_at_call": "not.is.null",
        "order": "ath_last_checked.asc.nullsfirst",
        "limit": "5"
    }
)
tokens_no_dead_filter = response6.json()

if tokens_no_dead_filter:
    print(f"\nFound {len(tokens_no_dead_filter)} tokens without is_dead filter:")
    for token in tokens_no_dead_filter[:3]:
        print(f"- {token['ticker']}: Last checked: {token.get('ath_last_checked', 'Never')}")
else:
    print("❌ No tokens found even without is_dead filter!")

print("\n=== Diagnosis ===")
if not next_tokens and tokens_no_dead_filter:
    print("⚠️ The is_dead column filter is preventing tokens from being processed!")
    print("The edge function filters out tokens where is_dead = true")
    print("But the column might not exist or all tokens might be marked as dead")
elif not tokens_no_dead_filter:
    print("❌ No tokens have both pool_address and price_at_call!")
    print("This is why the cron job processes 0 tokens")