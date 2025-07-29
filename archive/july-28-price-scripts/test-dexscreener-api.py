#!/usr/bin/env python3
"""
Test DexScreener API with a known token
"""

import requests
import json

# Test with a well-known token (PEPE on Ethereum)
test_contract = "0x6982508145454ce325ddbe47a25d4ec3d2311933"

url = f"https://api.dexscreener.com/latest/dex/tokens/{test_contract}"

print("🧪 Testing DexScreener API...")
print(f"URL: {url}")

try:
    response = requests.get(url, timeout=10)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        pairs = data.get('pairs', [])
        
        print(f"✅ Success! Found {len(pairs)} pairs")
        
        if pairs:
            # Show first pair
            pair = pairs[0]
            print(f"\nFirst pair info:")
            print(f"  Token: {pair.get('baseToken', {}).get('symbol')}")
            print(f"  Price: ${pair.get('priceUsd')}")
            print(f"  Liquidity: ${pair.get('liquidity', {}).get('usd'):,.2f}")
            print(f"  DEX: {pair.get('dexId')}")
            print(f"  Chain: {pair.get('chainId')}")
    else:
        print(f"❌ Error: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ Exception: {e}")