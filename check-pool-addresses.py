#!/usr/bin/env python3
"""Check if we have pool addresses and test the pairs endpoint"""

import requests
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Check how many tokens have pool addresses
response = supabase.table('crypto_calls').select(
    'ticker, network, contract_address, pool_address'
).not_.is_('contract_address', 'null').eq(
    'is_dead', False
).eq(
    'is_invalidated', False
).limit(100).execute()

tokens = response.data
with_pool = [t for t in tokens if t.get('pool_address')]
without_pool = [t for t in tokens if not t.get('pool_address')]

print(f"Pool Address Status:")
print(f"  Tokens WITH pool address: {len(with_pool)}")
print(f"  Tokens WITHOUT pool address: {len(without_pool)}")
print(f"  Total: {len(tokens)}")

if with_pool:
    print(f"\nTesting PAIRS endpoint with pool addresses:")
    print("="*60)
    
    # Test first 5 tokens with pool addresses
    for token in with_pool[:5]:
        print(f"\n{token['ticker']} on {token['network']}")
        print(f"  Pool: {token['pool_address']}")
        
        # Try the pairs endpoint with pool address
        url = f"https://api.dexscreener.com/latest/dex/pairs/{token['network']}/{token['pool_address']}"
        print(f"  URL: {url}")
        
        try:
            resp = requests.get(url)
            data = resp.json()
            
            if data.get('pair'):
                pair = data['pair']
                print(f"  ✅ Found pair data!")
                print(f"     Price: ${pair.get('priceUsd', 0)}")
                print(f"     Volume 24h: ${pair.get('volume', {}).get('h24', 0):,.0f}")
                print(f"     Liquidity: ${pair.get('liquidity', {}).get('usd', 0):,.0f}")
            elif data.get('pairs'):
                print(f"  ✅ Found {len(data['pairs'])} pairs")
            else:
                print(f"  ❌ No pair data found")
                print(f"     Response: {data}")
        except Exception as e:
            print(f"  ⚠️  Error: {e}")

# Test batch with pool addresses
if len(with_pool) >= 5:
    print("\n" + "="*60)
    print("Testing BATCH request with pool addresses:")
    print("="*60)
    
    batch = with_pool[:5]
    
    # Try comma-separated pool addresses
    pool_addresses = ','.join([t['pool_address'] for t in batch])
    
    # First try: tokens endpoint with pool addresses
    print("\n1. Tokens endpoint with pool addresses:")
    url = f"https://api.dexscreener.com/latest/dex/tokens/{pool_addresses}"
    resp = requests.get(url)
    data = resp.json()
    if data.get('pairs'):
        print(f"   ✅ Got {len(data['pairs'])} pairs")
    else:
        print(f"   ❌ No pairs returned")
    
    # Second try: see if there's a batch pairs endpoint
    print("\n2. Trying batch pairs endpoint (if it exists):")
    # Most APIs don't support batch pool lookups, but let's try
    for network in ['solana', 'ethereum']:
        tokens_in_network = [t for t in batch if t['network'] == network]
        if tokens_in_network:
            pools = ','.join([t['pool_address'] for t in tokens_in_network])
            url = f"https://api.dexscreener.com/latest/dex/pairs/{network}/{pools}"
            print(f"   Testing {network}: {url[:100]}...")
            resp = requests.get(url)
            data = resp.json()
            if data.get('pair') or data.get('pairs'):
                print(f"   ✅ Got response!")
            else:
                print(f"   ❌ No data")