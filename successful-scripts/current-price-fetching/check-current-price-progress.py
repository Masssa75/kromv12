#!/usr/bin/env python3
"""
Check progress of current price fetching
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

# Get all tokens with current prices (not null)
query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id,ticker,current_price&current_price.not.is.null&order=price_updated_at.desc.nullsfirst&limit=1000"
response = requests.get(query, headers=headers)

if response.status_code == 200:
    tokens_with_prices = response.json()
    count_with_prices = len(tokens_with_prices)
    print(f"✅ Tokens with current prices: {count_with_prices}")
else:
    print(f"❌ Error getting tokens with prices: {response.status_code}")
    count_with_prices = 0

# Get all tokens needing prices
query2 = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.is.null&price_at_call.not.is.null&contract_address.not.is.null&network.not.is.null&limit=10000"
response2 = requests.get(query2, headers=headers)

if response2.status_code == 200:
    tokens_needing_prices = response2.json()
    count_needing = len(tokens_needing_prices)
    print(f"📊 Tokens still needing current prices: {count_needing}")
    
    # Calculate percentage
    total = count_with_prices + count_needing
    if total > 0:
        percent = (count_with_prices / total) * 100
        print(f"📈 Progress: {percent:.1f}% complete ({count_with_prices}/{total})")
else:
    print(f"❌ Error getting tokens needing prices: {response2.status_code}")

# Show last 5 tokens that got current prices
if count_with_prices > 0:
    print("\n📈 Last 5 tokens with current prices:")
    for i, token in enumerate(tokens_with_prices[:5]):
        ticker = token.get('ticker', 'UNKNOWN')
        price = token.get('current_price')
        if price:
            print(f"   - {ticker}: ${price:.8f}")
        else:
            print(f"   - {ticker}: Price stored but value is null")