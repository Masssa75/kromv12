#!/usr/bin/env python3
"""
Get accurate current price progress using pagination
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    'apikey': SUPABASE_SERVICE_ROLE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
    'Content-Type': 'application/json'
}

# Count tokens with current prices by fetching in batches
total_with_prices = 0
offset = 0
batch_size = 1000

print("📊 Counting tokens with current prices...")

while True:
    query = f'{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.not.is.null&limit={batch_size}&offset={offset}'
    resp = requests.get(query, headers=headers)
    
    if resp.status_code == 200:
        batch = resp.json()
        if not batch:
            break
        total_with_prices += len(batch)
        offset += batch_size
        print(f"   Counted {total_with_prices} so far...")
    else:
        print(f"Error: {resp.status_code}")
        break

print(f"\n✅ Total tokens with current prices: {total_with_prices}")

# Count tokens still needing prices
total_needing = 0
offset = 0

print("\n📊 Counting tokens needing current prices...")

while True:
    query = f'{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.is.null&price_at_call.gt.0&contract_address.not.is.null&network.not.is.null&limit={batch_size}&offset={offset}'
    resp = requests.get(query, headers=headers)
    
    if resp.status_code == 200:
        batch = resp.json()
        if not batch:
            break
        total_needing += len(batch)
        offset += batch_size
    else:
        print(f"Error: {resp.status_code}")
        break

print(f"📈 Total tokens still needing prices: {total_needing}")

# Get total eligible tokens
total_eligible_query = f'{SUPABASE_URL}/rest/v1/crypto_calls?select=id&price_at_call.gt.0&contract_address.not.is.null&network.not.is.null&limit=1'
total_resp = requests.get(total_eligible_query, headers={**headers, "Prefer": "count=exact"})
if 'content-range' in total_resp.headers:
    total_eligible = int(total_resp.headers['content-range'].split('/')[-1])
    print(f"\n📊 Total eligible tokens: {total_eligible}")
    print(f"🎯 Progress: {(total_with_prices/total_eligible*100):.1f}% complete")

# Show recent updates
print("\n📈 Recent price updates:")
recent_query = f'{SUPABASE_URL}/rest/v1/crypto_calls?select=ticker,current_price,price_updated_at&current_price.not.is.null&order=price_updated_at.desc&limit=5'
recent_resp = requests.get(recent_query, headers=headers)
if recent_resp.status_code == 200:
    recent = recent_resp.json()
    for r in recent:
        print(f"   - {r['ticker']}: ${float(r['current_price']):.8f} (updated: {r['price_updated_at'][:19]})")