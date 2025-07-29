#!/usr/bin/env python3
"""
Test individual token price fetching
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Network mapping
NETWORK_MAP = {
    'ethereum': 'eth',
    'solana': 'solana',
    'bsc': 'bsc',
    'polygon': 'polygon',
    'arbitrum': 'arbitrum',
    'base': 'base'
}

# Test tokens - mix of different networks and states
test_tokens = [
    # From our earlier tests
    {"ticker": "OMALLEY", "contract": "0x90001c5F2C6fFD4B90A801AfDDEfcbf31965c667", "network": "ethereum"},
    {"ticker": "BIP177", "contract": "EzaNX1MHGzwAMHJahgLVxahiJJYm3cKCBmqKcnGL5pump", "network": "solana"},
    {"ticker": "VIRAL", "contract": "E5sJv2tTUVdBzqcrG5BfUwxqSKWJdLCzf8xgNRMypump", "network": "solana"},
    # Add a few more
    {"ticker": "PEPE", "contract": "0x6982508145454Ce325dDbE47a25d4ec3d2311933", "network": "ethereum"},
    {"ticker": "WIF", "contract": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm", "network": "solana"},
]

print("🔍 Testing Individual Token Price Fetching")
print("=" * 60)

for token in test_tokens:
    print(f"\n📊 Testing {token['ticker']} on {token['network']}")
    print(f"   Contract: {token['contract']}")
    
    # Test DexScreener
    print("\n   DexScreener API:")
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token['contract']}"
        resp = requests.get(url)
        print(f"   - Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('pairs') and len(data['pairs']) > 0:
                pair = data['pairs'][0]
                print(f"   - Found: {pair['baseToken']['symbol']} on {pair['chainId']}")
                print(f"   - Price: ${pair['priceUsd']}")
                print(f"   - Liquidity: ${pair.get('liquidity', {}).get('usd', 'N/A')}")
            else:
                print("   - No pairs found")
        else:
            print(f"   - Error: {resp.text[:100]}")
    except Exception as e:
        print(f"   - Exception: {e}")
    
    # Test GeckoTerminal
    print("\n   GeckoTerminal API:")
    try:
        api_network = NETWORK_MAP.get(token['network'], token['network'])
        url = f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{token['contract']}"
        resp = requests.get(url)
        print(f"   - Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('data') and data['data'].get('attributes'):
                attrs = data['data']['attributes']
                print(f"   - Found: {attrs.get('symbol', 'N/A')} ({attrs.get('name', 'N/A')})")
                print(f"   - Price: ${attrs.get('price_usd', 'N/A')}")
                print(f"   - Market Cap: ${attrs.get('market_cap_usd', 'N/A')}")
            else:
                print("   - No data found")
        else:
            print(f"   - Error: {resp.text[:100]}")
    except Exception as e:
        print(f"   - Exception: {e}")
    
    print("-" * 60)