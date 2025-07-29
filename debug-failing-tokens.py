#!/usr/bin/env python3
"""
Debug why certain tokens keep appearing and failing
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

# Check specific failing tokens
failing_tokens = ['CC', 'TEST', 'DEPOT', 'ART', 'LARRY']

for ticker in failing_tokens:
    print(f"\n🔍 Checking {ticker}...")
    
    # Get all instances of this ticker
    query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id,ticker,contract_address,network,current_price,price_updated_at,krom_id&ticker=eq.{ticker}&order=created_at.asc"
    response = requests.get(query, headers=headers)
    
    if response.status_code == 200:
        tokens = response.json()
        print(f"   Found {len(tokens)} instances of {ticker}")
        
        for i, token in enumerate(tokens[:3]):  # Show first 3
            print(f"   [{i+1}] ID: {token['id'][:8]}...")
            print(f"       Contract: {token['contract_address']}")
            print(f"       Network: {token['network']}")
            print(f"       Current Price: {token['current_price']}")
            print(f"       Updated At: {token['price_updated_at']}")
            
            # Try to fetch price directly
            if token['contract_address'] and token['network']:
                # Test DexScreener
                url = f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}"
                try:
                    r = requests.get(url, timeout=5)
                    if r.status_code == 200:
                        data = r.json()
                        if data.get('pairs'):
                            print(f"       ✅ DexScreener: Found {len(data['pairs'])} pairs")
                        else:
                            print(f"       ❌ DexScreener: No pairs found")
                    else:
                        print(f"       ❌ DexScreener: HTTP {r.status_code}")
                except Exception as e:
                    print(f"       ❌ DexScreener error: {e}")

# Check why same tokens appear multiple times
print("\n\n🔍 Checking ordering issue...")
query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id,ticker,price_updated_at&contract_address.not.is.null&network.not.is.null&order=price_updated_at.asc.nullsfirst,created_at.asc&limit=10"
response = requests.get(query, headers=headers)

if response.status_code == 200:
    tokens = response.json()
    print("First 10 tokens by price_updated_at (nulls first):")
    for i, token in enumerate(tokens):
        print(f"   [{i+1}] {token['ticker']} - Updated: {token['price_updated_at']}")