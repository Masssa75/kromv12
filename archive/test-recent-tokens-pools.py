#!/usr/bin/env python3
"""Test pool addresses for tokens from last 24 hours"""

import requests
from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Get tokens from last 24 hours
cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

response = supabase.table('crypto_calls').select(
    'ticker, network, contract_address, pool_address, created_at'
).gte('created_at', cutoff).order(
    'created_at', desc=True
).limit(30).execute()

tokens = response.data
print(f"Found {len(tokens)} tokens from last 24 hours")

# Group by network
by_network = {}
for token in tokens:
    network = token['network'].lower()
    if network not in by_network:
        by_network[network] = []
    by_network[network].append(token)

print("\nTokens by network:")
for network, token_list in by_network.items():
    print(f"  {network}: {len(token_list)} tokens")

# Test Solana tokens with pools vs contracts
if 'solana' in by_network:
    solana_tokens = by_network['solana'][:10]
    print(f"\n{'='*60}")
    print(f"Testing {len(solana_tokens)} recent Solana tokens")
    print("="*60)
    
    # Test 1: Using pool addresses
    print("\n1. USING POOL ADDRESSES:")
    pool_addresses = ','.join([t['pool_address'] for t in solana_tokens if t['pool_address']])
    
    if pool_addresses:
        url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{pool_addresses}"
        print(f"URL: {url[:100]}...")
        
        resp = requests.get(url)
        data = resp.json()
        
        if data.get('pairs'):
            pairs = data['pairs']
            print(f"✅ Got {len(pairs)} pairs for {len(solana_tokens)} tokens")
            
            # Check which tokens matched
            found_tokens = []
            for token in solana_tokens:
                for pair in pairs:
                    if pair.get('pairAddress') == token['pool_address']:
                        found_tokens.append(token['ticker'])
                        break
            
            print(f"   Found: {found_tokens}")
            print(f"   Coverage: {len(found_tokens)}/{len(solana_tokens)} ({len(found_tokens)*100/len(solana_tokens):.0f}%)")
        else:
            print(f"❌ No pairs returned")
    
    # Test 2: Using contract addresses  
    print("\n2. USING CONTRACT ADDRESSES:")
    contract_addresses = ','.join([t['contract_address'] for t in solana_tokens])
    
    url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_addresses}"
    print(f"URL: {url[:100]}...")
    
    resp = requests.get(url)
    data = resp.json()
    
    if data.get('pairs'):
        pairs = data['pairs']
        print(f"✅ Got {len(pairs)} pairs for {len(solana_tokens)} tokens")
        
        # Check which tokens matched
        found_tokens = set()
        for token in solana_tokens:
            for pair in pairs:
                base_addr = pair.get('baseToken', {}).get('address', '').lower()
                quote_addr = pair.get('quoteToken', {}).get('address', '').lower()
                if token['contract_address'].lower() in [base_addr, quote_addr]:
                    found_tokens.add(token['ticker'])
                    break
        
        print(f"   Found: {list(found_tokens)}")
        print(f"   Coverage: {len(found_tokens)}/{len(solana_tokens)} ({len(found_tokens)*100/len(solana_tokens):.0f}%)")
    else:
        print(f"❌ No pairs returned")

# Test individual pools to see which ones exist
print(f"\n{'='*60}")
print("Testing each pool individually:")
print("="*60)

for token in solana_tokens[:5]:
    print(f"\n{token['ticker']}:")
    print(f"  Pool: {token['pool_address'][:20]}...")
    
    # Test pool endpoint
    url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{token['pool_address']}"
    resp = requests.get(url)
    data = resp.json()
    
    if data.get('pair'):
        print(f"  ✅ Pool exists on DexScreener")
    else:
        print(f"  ❌ Pool NOT found")
        
        # Try contract address
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}"
        resp = requests.get(url)
        data = resp.json()
        
        if data.get('pairs'):
            actual_pool = data['pairs'][0].get('pairAddress')
            print(f"  ℹ️  Contract found, actual pool: {actual_pool[:20]}...")
            print(f"      Our pool: {token['pool_address'][:20]}...")
            if actual_pool != token['pool_address']:
                print(f"      ⚠️  POOL MISMATCH!")