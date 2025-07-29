#!/usr/bin/env python3
"""
Test more tokens to understand the issue
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

# Network mapping
NETWORK_MAP = {
    'ethereum': 'eth',
    'solana': 'solana',
    'bsc': 'bsc',
    'polygon': 'polygon',
    'arbitrum': 'arbitrum',
    'base': 'base'
}

# Get 20 tokens that need prices
query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id,ticker,contract_address,network,price_at_call&current_price.is.null&contract_address.not.is.null&network.not.is.null&price_at_call.gt.0&order=created_at.asc&limit=20"

resp = requests.get(query, headers=headers)
tokens = resp.json()

print(f"Testing {len(tokens)} tokens...\n")

success_count = 0
failure_reasons = {}

for i, token in enumerate(tokens, 1):
    print(f"[{i}/20] {token['ticker']} ({token['network']})")
    print(f"   Contract: {token['contract_address'][:20]}...")
    
    found = False
    
    # Try DexScreener
    try:
        resp = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}")
        data = resp.json()
        if data.get('pairs') and len(data['pairs']) > 0:
            price = float(data['pairs'][0]['priceUsd'])
            print(f"   ✅ DexScreener: ${price:.8f}")
            success_count += 1
            found = True
        else:
            print(f"   ❌ DexScreener: No pairs")
    except Exception as e:
        print(f"   ❌ DexScreener error: {e}")
    
    if not found:
        # Try GeckoTerminal
        try:
            api_network = NETWORK_MAP.get(token['network'], token['network'])
            resp = requests.get(f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{token['contract_address']}")
            
            if resp.status_code == 404:
                print(f"   ❌ GeckoTerminal: Not found (404)")
                failure_reasons['404'] = failure_reasons.get('404', 0) + 1
            else:
                data = resp.json()
                if data.get('data') and data['data'].get('attributes'):
                    price_str = data['data']['attributes'].get('price_usd')
                    if price_str:
                        print(f"   ✅ GeckoTerminal: ${float(price_str):.8f}")
                        success_count += 1
                        found = True
                    else:
                        print(f"   ❌ GeckoTerminal: No price")
                else:
                    print(f"   ❌ GeckoTerminal: No data")
        except Exception as e:
            print(f"   ❌ GeckoTerminal error: {e}")
    
    if not found:
        failure_reasons['no_price'] = failure_reasons.get('no_price', 0) + 1
    
    print()

print(f"\nSummary:")
print(f"  Successful: {success_count}/{len(tokens)} ({success_count/len(tokens)*100:.1f}%)")
print(f"  Failures: {failure_reasons}")