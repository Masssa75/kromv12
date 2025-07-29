#!/usr/bin/env python3
import requests
import json

# Test tokens
tokens = [
    {"ticker": "OMALLEY", "contract": "0x90001c5F2C6fFD4B90A801AfDDEfcbf31965c667", "network": "ethereum"},
    {"ticker": "LICKB", "contract": "0xdb9172dD210a059D7C3a022A1834B4660821c7AA", "network": "ethereum"},
    {"ticker": "ROSE", "contract": "0x7eF83e12daF52e93B7D3f4cEC718fE207576B278", "network": "ethereum"},
]

print("Testing DexScreener API directly...\n")

for token in tokens:
    print(f"Testing {token['ticker']} ({token['network']}):")
    print(f"Contract: {token['contract']}")
    
    # Try DexScreener
    try:
        resp = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token['contract']}")
        data = resp.json()
        
        if data.get('pairs') and len(data['pairs']) > 0:
            pair = data['pairs'][0]
            print(f"✅ Found on DexScreener: ${pair['priceUsd']}")
        else:
            print("❌ Not found on DexScreener")
    except Exception as e:
        print(f"❌ DexScreener error: {e}")
    
    print("-" * 50)