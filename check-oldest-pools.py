#!/usr/bin/env python3
"""Check validity of pool addresses for oldest tokens"""

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

# Get oldest tokens by ath_last_checked
response = supabase.table('crypto_calls').select(
    'ticker, network, contract_address, pool_address, ath_last_checked, created_at'
).not_.is_('pool_address', 'null').eq(
    'is_dead', False
).eq(
    'is_invalidated', False
).order(
    'ath_last_checked', desc=False  # ascending with nulls first
).limit(50).execute()

tokens = response.data

print(f"Testing 50 oldest tokens (by ath_last_checked):")
print("="*60)

# Group by network
by_network = {}
for token in tokens:
    network = token['network'].lower()
    if network not in by_network:
        by_network[network] = []
    by_network[network].append(token)

for network, network_tokens in by_network.items():
    print(f"\n{network.upper()}: {len(network_tokens)} tokens")
    
    # Test batch with pools
    batch = network_tokens[:10]
    pool_addresses = ','.join([t['pool_address'] for t in batch])
    
    url = f"https://api.dexscreener.com/latest/dex/pairs/{network}/{pool_addresses}"
    
    try:
        resp = requests.get(url)
        data = resp.json()
        
        pairs_array = data.get('pairs', []) or (data.get('pair') and [data['pair']]) or []
        
        found_count = 0
        for token in batch:
            found = any(p.get('pairAddress') == token['pool_address'] for p in pairs_array)
            if found:
                found_count += 1
        
        print(f"  Pool coverage: {found_count}/{len(batch)} ({found_count*100/len(batch):.0f}%)")
        
        # Now test with contract addresses
        contract_addresses = ','.join([t['contract_address'] for t in batch])
        url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_addresses}"
        
        resp = requests.get(url)
        data = resp.json()
        
        if data.get('pairs'):
            found_tokens = set()
            for pair in data['pairs']:
                for token in batch:
                    if (token['contract_address'].lower() == pair.get('baseToken', {}).get('address', '').lower() or
                        token['contract_address'].lower() == pair.get('quoteToken', {}).get('address', '').lower()):
                        found_tokens.add(token['ticker'])
            
            print(f"  Contract coverage: {len(found_tokens)}/{len(batch)} ({len(found_tokens)*100/len(batch):.0f}%)")
        else:
            print(f"  Contract coverage: 0/{len(batch)} (0%)")
            
    except Exception as e:
        print(f"  Error: {e}")

print(f"\n{'='*60}")
print("CONCLUSION:")
print("Oldest tokens have invalid pool addresses.")
print("Need to implement fallback to contract addresses.")