#!/usr/bin/env python3
"""
Check which tokens are marked as dead from the price_at_call fetch
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

# Check tokens that have price_at_call = 0 (indicating dead tokens)
print("🔍 Checking tokens marked as dead (price_at_call = 0)...")
query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id,ticker,contract_address,network,price_at_call&price_at_call=eq.0&limit=20"
response = requests.get(query, headers=headers)

if response.status_code == 200:
    dead_tokens = response.json()
    print(f"Found {len(dead_tokens)} tokens with price_at_call = 0")
    
    # Show some examples
    for token in dead_tokens[:10]:
        print(f"   - {token['ticker']} ({token['network']}) - Contract: {token['contract_address'][:20]}...")

# Count total dead tokens
count_query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&price_at_call=eq.0"
count_resp = requests.get(count_query, headers={**headers, "Prefer": "count=exact"}, params={"limit": 0})
if 'content-range' in count_resp.headers:
    total_dead = count_resp.headers['content-range'].split('/')[-1]
    print(f"\n📊 Total tokens marked as dead: {total_dead}")

# Check the failing tokens specifically
print("\n🔍 Checking specific failing tokens...")
failing_tokens = ['CC', 'TEST', 'DEPOT', 'ART', 'LARRY', 'EXTEND', 'PEPE', 'CAPITALISM']

for ticker in failing_tokens[:5]:
    query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=ticker,price_at_call,current_price,price_updated_at&ticker=eq.{ticker}&order=created_at.asc&limit=1"
    response = requests.get(query, headers=headers)
    
    if response.status_code == 200 and response.json():
        token = response.json()[0]
        print(f"   {ticker}: price_at_call={token['price_at_call']}, current_price={token['current_price']}, updated={token['price_updated_at']}")
        if token['price_at_call'] == 0:
            print(f"      ⚠️  This token is marked as DEAD!")

# Also check for the source price marker
print("\n🔍 Checking for price source markers...")
query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id,ticker,price_source&price_source.not.is.null&limit=10"
response = requests.get(query, headers=headers)

if response.status_code == 200:
    sources = response.json()
    if sources:
        print("Found price_source column with data:")
        for s in sources:
            print(f"   - {s['ticker']}: {s.get('price_source', 'N/A')}")
    else:
        print("❌ No price_source data found - this column might not exist")