#!/usr/bin/env python3
"""
Check BIP177 status in database
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

# Get BIP177 data
query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=*&krom_id=eq.682a2529eb25eec68c92e87f&limit=1"
response = requests.get(query, headers=headers)

if response.status_code == 200 and response.json():
    token = response.json()[0]
    print("🔍 BIP177 Current Status:")
    print(f"   Ticker: {token.get('ticker')}")
    print(f"   Contract: {token.get('contract_address')}")
    print(f"   Network: {token.get('network')}")
    print(f"   Entry Price: ${token.get('price_at_call')}")
    print(f"   Current Price: ${token.get('current_price')}")
    print(f"   ROI: {token.get('roi_percent')}%")
    print(f"   Price Updated At: {token.get('price_updated_at')}")
else:
    print("❌ Could not fetch BIP177 data")

# Now check how many tokens still need prices
query2 = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.is.null&price_at_call.not.is.null&contract_address.not.is.null&network.not.is.null&limit=10"
response2 = requests.get(query2, headers=headers)

if response2.status_code == 200:
    tokens = response2.json()
    print(f"\n📊 Tokens still needing prices: {len(tokens)}")
    if tokens:
        print("First few tokens needing prices:")
        for i, t in enumerate(tokens[:5]):
            # Get full details for each
            detail_query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=ticker,krom_id&id=eq.{t['id']}"
            detail_resp = requests.get(detail_query, headers=headers)
            if detail_resp.status_code == 200 and detail_resp.json():
                detail = detail_resp.json()[0]
                print(f"   {i+1}. {detail.get('ticker', 'UNKNOWN')} ({detail.get('krom_id', 'N/A')})")