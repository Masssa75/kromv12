#!/usr/bin/env python3
"""Test the exact response format from pairs endpoint"""

import requests
from supabase import create_client
import os
from dotenv import load_dotenv
import json

load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Get some tokens with pool addresses
response = supabase.table('crypto_calls').select(
    'ticker, network, contract_address, pool_address'
).not_.is_('pool_address', 'null').eq(
    'is_dead', False
).eq(
    'is_invalidated', False
).eq(
    'network', 'solana'
).order(
    'ath_last_checked', desc=False
).limit(5).execute()

tokens = response.data
print(f"Testing with {len(tokens)} Solana tokens")
for t in tokens:
    print(f"  - {t['ticker']}: pool={t['pool_address'][:20]}... contract={t['contract_address'][:20]}...")

# Make the same API call ultra-tracker would make
pool_addresses = ','.join([t['pool_address'] for t in tokens])
url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{pool_addresses}"

print(f"\nAPI URL: {url[:100]}...")
resp = requests.get(url)
data = resp.json()

print(f"\nResponse structure:")
print(f"  - Has 'pairs' key: {'pairs' in data}")
print(f"  - Has 'pair' key: {'pair' in data}")

if 'pairs' in data and data['pairs']:
    pairs = data['pairs']
    print(f"  - Number of pairs: {len(pairs)}")
    print(f"\nFirst pair structure:")
    pair = pairs[0]
    print(f"  - pairAddress: {pair.get('pairAddress', 'MISSING')}")
    print(f"  - baseToken.address: {pair.get('baseToken', {}).get('address', 'MISSING')}")
    print(f"  - quoteToken.address: {pair.get('quoteToken', {}).get('address', 'MISSING')}")
    print(f"  - priceUsd: {pair.get('priceUsd', 'MISSING')}")
    print(f"  - volume.h24: {pair.get('volume', {}).get('h24', 'MISSING')}")
    
    # Check which tokens match
    print(f"\nMatching tokens by pool address:")
    for token in tokens:
        found = False
        for p in pairs:
            if p.get('pairAddress') == token['pool_address']:
                found = True
                # Check if contract address matches base or quote
                is_base = p.get('baseToken', {}).get('address', '').lower() == token['contract_address'].lower()
                is_quote = p.get('quoteToken', {}).get('address', '').lower() == token['contract_address'].lower()
                print(f"  ✅ {token['ticker']}: Found! (is_base={is_base}, is_quote={is_quote})")
                break
        if not found:
            print(f"  ❌ {token['ticker']}: Pool not found in response")
elif 'pair' in data:
    print(f"  - Single pair response")
    print(f"  - pairAddress: {data['pair'].get('pairAddress', 'MISSING')}")
else:
    print(f"  - Empty response or error")
    print(f"  - Full response: {json.dumps(data, indent=2)}")