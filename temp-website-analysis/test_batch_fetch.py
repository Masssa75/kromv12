#!/usr/bin/env python3
"""Test fetching utility tokens from Supabase"""

import os
import sys
from dotenv import load_dotenv
import requests

load_dotenv()

print("1. Loading environment...")
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not supabase_key:
    print("ERROR: Missing environment variables")
    sys.exit(1)

print("2. Making request to Supabase...")
print(f"   URL: {supabase_url}/rest/v1/crypto_calls")

response = requests.get(
    f'{supabase_url}/rest/v1/crypto_calls',
    headers={
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}'
    },
    params={
        'select': 'ticker,network,website_url,liquidity_usd',
        'is_utility': 'eq.true',
        'website_url': 'not.is.null',
        'order': 'liquidity_usd.desc.nullsfirst',
        'limit': '5'
    },
    timeout=10
)

print(f"3. Response status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"4. Found {len(data)} utility tokens")
    for token in data[:3]:
        print(f"   - {token['ticker']}: {token['website_url']}")
else:
    print(f"ERROR: {response.text[:200]}")