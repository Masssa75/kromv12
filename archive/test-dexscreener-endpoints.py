#!/usr/bin/env python3
"""Test different DexScreener API endpoints"""

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

# Get a token we know exists
response = supabase.table('crypto_calls').select(
    'ticker, network, contract_address, pool_address'
).eq('ticker', 'SOL').eq('network', 'solana').limit(1).execute()

if response.data:
    token = response.data[0]
    print(f"Testing with {token['ticker']} on {token['network']}")
    print(f"Contract: {token['contract_address']}")
    print(f"Pool: {token['pool_address'] or 'No pool address stored'}")
    print("="*60)
    
    # Test 1: Token endpoint (what we're currently using)
    print("\n1. TOKEN ENDPOINT (/tokens/):")
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}"
    print(f"   URL: {url}")
    
    resp = requests.get(url)
    data = resp.json()
    if data.get('pairs'):
        print(f"   ✅ Found {len(data['pairs'])} pairs")
        # Get pool addresses from the response
        pools = [p.get('pairAddress') for p in data['pairs'][:3]]
        print(f"   Pool addresses returned: {pools}")
    else:
        print(f"   ❌ No pairs found")
    
    # Test 2: Try pairs endpoint with pool address
    if data.get('pairs') and data['pairs']:
        pool_address = data['pairs'][0].get('pairAddress')
        if pool_address:
            print(f"\n2. PAIRS ENDPOINT (/pairs/):")
            url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{pool_address}"
            print(f"   URL: {url}")
            
            resp = requests.get(url)
            pair_data = resp.json()
            if pair_data.get('pair'):
                print(f"   ✅ Found pair data")
                print(f"   Price: ${pair_data['pair'].get('priceUsd', 0)}")
                print(f"   Volume: ${pair_data['pair'].get('volume', {}).get('h24', 0):,.0f}")
            elif pair_data.get('pairs'):
                print(f"   ✅ Found {len(pair_data.get('pairs', []))} pairs")
            else:
                print(f"   ❌ No pair data")
    
    # Test 3: Search endpoint
    print(f"\n3. SEARCH ENDPOINT:")
    url = f"https://api.dexscreener.com/latest/dex/search?q={token['ticker']}"
    print(f"   URL: {url}")
    
    resp = requests.get(url)
    search_data = resp.json()
    if search_data.get('pairs'):
        print(f"   ✅ Found {len(search_data['pairs'])} pairs")
        # Check how many are for our specific token
        matching = [p for p in search_data['pairs'] if 
                   p.get('baseToken', {}).get('address', '').lower() == token['contract_address'].lower() or
                   p.get('quoteToken', {}).get('address', '').lower() == token['contract_address'].lower()]
        print(f"   Matching our token: {len(matching)}")
    else:
        print(f"   ❌ No results")

# Test batch request with multiple individual tokens
print("\n" + "="*60)
print("TESTING BATCH STRATEGIES:")
print("="*60)

# Get 5 tokens we know exist
test_tickers = ['SOL', 'TUCKER', 'NITEFEEDER', 'TAP', 'PILSO']
response = supabase.table('crypto_calls').select(
    'ticker, network, contract_address'
).in_('ticker', test_tickers).execute()

tokens = response.data[:5]  # Just first 5
print(f"\nUsing {len(tokens)} known tokens")

# Strategy 1: Single batch request (current approach)
print("\nStrategy 1: Single batch request with comma-separated addresses")
addresses = ','.join([t['contract_address'] for t in tokens])
url = f"https://api.dexscreener.com/latest/dex/tokens/{addresses}"

resp = requests.get(url)
data = resp.json()
if data.get('pairs'):
    found_tokens = set()
    for pair in data['pairs']:
        for token in tokens:
            if (token['contract_address'].lower() == pair.get('baseToken', {}).get('address', '').lower() or
                token['contract_address'].lower() == pair.get('quoteToken', {}).get('address', '').lower()):
                found_tokens.add(token['ticker'])
    
    print(f"  Result: {len(data['pairs'])} pairs returned, {len(found_tokens)}/{len(tokens)} tokens found")
    print(f"  Found: {found_tokens}")

# Strategy 2: Individual requests (one per token)
print("\nStrategy 2: Individual requests per token")
found_count = 0
for token in tokens:
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}"
    resp = requests.get(url)
    data = resp.json()
    if data.get('pairs'):
        found_count += 1
        print(f"  ✅ {token['ticker']}: {len(data['pairs'])} pairs")
    else:
        print(f"  ❌ {token['ticker']}: No pairs")

print(f"  Result: {found_count}/{len(tokens)} tokens found individually")