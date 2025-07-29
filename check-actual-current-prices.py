#!/usr/bin/env python3
"""
Check actual current price progress - with better queries
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

# Get total count
total_query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id"
total_resp = requests.get(total_query, headers={**headers, "Prefer": "count=exact"}, params={"limit": 0})
total_tokens = int(total_resp.headers.get('content-range', '/0').split('/')[-1])

# Get tokens with actual non-null current prices
with_prices_query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id,ticker,current_price&current_price.not.is.null&current_price.gt.0&order=price_updated_at.desc&limit=10"
response = requests.get(with_prices_query, headers=headers)

if response.status_code == 200:
    tokens_with_prices = response.json()
    
    # Get count with proper query
    count_query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.not.is.null&current_price.gt.0"
    count_resp = requests.get(count_query, headers={**headers, "Prefer": "count=exact"}, params={"limit": 0})
    count_with_prices = int(count_resp.headers.get('content-range', '/0').split('/')[-1])
    
    print(f"✅ Tokens with actual current prices (>0): {count_with_prices}")
    print(f"📊 Total tokens in database: {total_tokens}")
    print(f"📈 Progress: {(count_with_prices/total_tokens*100):.1f}%")
    
    if tokens_with_prices:
        print(f"\n📈 Recent tokens with current prices:")
        for token in tokens_with_prices[:5]:
            ticker = token.get('ticker', 'UNKNOWN')
            price = token.get('current_price')
            if price:
                print(f"   - {ticker}: ${float(price):.8f}")
            else:
                print(f"   - {ticker}: Price is null")
else:
    print(f"❌ Error: {response.status_code}")

# Check tokens that need prices
need_prices_query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&price_at_call.not.is.null&contract_address.not.is.null&network.not.is.null&or=(current_price.is.null,current_price.eq.0)"
need_resp = requests.get(need_prices_query, headers={**headers, "Prefer": "count=exact"}, params={"limit": 0})
need_count = int(need_resp.headers.get('content-range', '/0').split('/')[-1])

print(f"\n📊 Tokens still needing current prices: {need_count}")

# Check timestamp issues
timestamp_query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.is.null&price_updated_at.not.is.null"
timestamp_resp = requests.get(timestamp_query, headers={**headers, "Prefer": "count=exact"}, params={"limit": 0})
timestamp_count = int(timestamp_resp.headers.get('content-range', '/0').split('/')[-1])

if timestamp_count > 0:
    print(f"\n⚠️  Records with timestamps but null prices: {timestamp_count}")
    print("    (These need to be cleaned up)")