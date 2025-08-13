#!/usr/bin/env python3
"""Test batch pairs endpoint with pool addresses"""

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

# Get tokens with pool addresses
response = supabase.table('crypto_calls').select(
    'ticker, network, contract_address, pool_address'
).not_.is_('pool_address', 'null').eq(
    'is_dead', False
).eq(
    'is_invalidated', False
).limit(30).execute()

tokens = response.data

# Group by network
by_network = {}
for token in tokens:
    network = token['network'].lower()
    if network not in by_network:
        by_network[network] = []
    by_network[network].append(token)

print("Testing BATCH PAIRS endpoint:")
print("="*60)

for network, network_tokens in by_network.items():
    if network not in ['ethereum', 'solana', 'bsc', 'polygon', 'arbitrum', 'base']:
        continue
    
    print(f"\n{network.upper()}: {len(network_tokens)} tokens")
    
    # Test with batch of 5
    batch = network_tokens[:5]
    pool_addresses = ','.join([t['pool_address'] for t in batch])
    
    url = f"https://api.dexscreener.com/latest/dex/pairs/{network}/{pool_addresses}"
    print(f"  URL: ...pairs/{network}/[{len(batch)} pools]")
    print(f"  Tokens: {[t['ticker'] for t in batch]}")
    
    try:
        resp = requests.get(url)
        data = resp.json()
        
        # Check what format the response is in
        if data.get('pair'):
            # Single pair response
            print(f"  ✅ Got single pair data")
            print(f"     Price: ${data['pair'].get('priceUsd', 0)}")
        elif data.get('pairs'):
            # Multiple pairs response
            pairs = data['pairs']
            print(f"  ✅ Got {len(pairs)} pairs!")
            
            # Check which tokens we got data for
            found_tokens = set()
            for pair in pairs:
                for token in batch:
                    if pair.get('pairAddress') == token['pool_address']:
                        found_tokens.add(token['ticker'])
                        break
            
            print(f"     Coverage: {len(found_tokens)}/{len(batch)} tokens")
            print(f"     Found: {found_tokens}")
            
            # Show some data
            if pairs:
                total_volume = sum(p.get('volume', {}).get('h24', 0) for p in pairs)
                print(f"     Total volume 24h: ${total_volume:,.0f}")
        else:
            print(f"  ❌ No pairs data")
            print(f"     Response: {data}")
            
    except Exception as e:
        print(f"  ⚠️  Error: {e}")

# Test larger batch
print("\n" + "="*60)
print("Testing LARGER BATCH (10 pools):")
print("="*60)

if 'solana' in by_network and len(by_network['solana']) >= 10:
    batch = by_network['solana'][:10]
    pool_addresses = ','.join([t['pool_address'] for t in batch])
    
    url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{pool_addresses}"
    print(f"Requesting 10 Solana pools...")
    
    resp = requests.get(url)
    data = resp.json()
    
    if data.get('pairs'):
        pairs = data['pairs']
        print(f"✅ Got {len(pairs)} pairs back!")
        
        # Check coverage
        found_pools = set(p.get('pairAddress') for p in pairs)
        requested_pools = set(t['pool_address'] for t in batch)
        
        print(f"Requested: {len(requested_pools)} pools")
        print(f"Received: {len(found_pools)} unique pools")
        print(f"Coverage: {len(found_pools)*100/len(requested_pools):.0f}%")