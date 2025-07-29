#!/usr/bin/env python3
"""
Check what's really in the current_price column
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

# Check various price states
print("📊 Checking current price states...")

# 1. Tokens with actual prices (not null, not zero)
query1 = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.not.is.null&current_price.gt.0"
resp1 = requests.get(query1, headers={**headers, "Prefer": "count=exact"}, params={"limit": 0})
count1 = int(resp1.headers.get('content-range', '/0').split('/')[-1])
print(f"✅ Tokens with current_price > 0: {count1}")

# 2. Tokens with null prices
query2 = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.is.null"
resp2 = requests.get(query2, headers={**headers, "Prefer": "count=exact"}, params={"limit": 0})
count2 = int(resp2.headers.get('content-range', '/0').split('/')[-1])
print(f"❌ Tokens with current_price NULL: {count2}")

# 3. Tokens with zero prices
query3 = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.eq.0"
resp3 = requests.get(query3, headers={**headers, "Prefer": "count=exact"}, params={"limit": 0})
count3 = int(resp3.headers.get('content-range', '/0').split('/')[-1])
print(f"⚠️  Tokens with current_price = 0: {count3}")

# 4. Tokens with price_at_call > 0 but no current price
query4 = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&price_at_call.gt.0&current_price.is.null"
resp4 = requests.get(query4, headers={**headers, "Prefer": "count=exact"}, params={"limit": 0})
count4 = int(resp4.headers.get('content-range', '/0').split('/')[-1])
print(f"🔄 Tokens with price_at_call > 0 but current_price NULL: {count4}")

# 5. Sample some tokens with NULL current prices
print("\n📋 Sample tokens with NULL current prices:")
sample_query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=ticker,contract_address,network,price_at_call,current_price,price_updated_at&current_price.is.null&price_at_call.gt.0&limit=10"
sample_resp = requests.get(sample_query, headers=headers)

if sample_resp.status_code == 200:
    samples = sample_resp.json()
    for i, token in enumerate(samples, 1):
        print(f"   [{i}] {token['ticker']} - {token['network']}")
        print(f"       Contract: {token['contract_address'][:20]}...")
        print(f"       Price at call: {token['price_at_call']}")
        print(f"       Updated at: {token['price_updated_at']}")

# 6. Check tokens updated in last hour
from datetime import datetime, timezone, timedelta
one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
query6 = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&price_updated_at.gt.{one_hour_ago}"
resp6 = requests.get(query6, headers={**headers, "Prefer": "count=exact"}, params={"limit": 0})
if 'content-range' in resp6.headers:
    count6 = int(resp6.headers.get('content-range', '/0').split('/')[-1])
    print(f"\n🕐 Tokens updated in last hour: {count6}")