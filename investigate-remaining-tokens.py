#!/usr/bin/env python3
"""
Investigate the remaining 441 tokens without supply data
"""

import os
import warnings
warnings.filterwarnings("ignore")
from dotenv import load_dotenv
from supabase import create_client
import requests
from collections import Counter

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("=" * 60)
print("Investigating Remaining Tokens Without Supply Data")
print("=" * 60)

# Get tokens without supply data
result = supabase.table('crypto_calls').select(
    'id,ticker,contract_address,network,created_at,is_dead,price_at_call,current_price'
).neq('is_dead', True).is_('total_supply', 'null').not_.is_('contract_address', 'null').limit(500).execute()

tokens = result.data
print(f"\nFound {len(tokens)} tokens without supply data")

# Analyze characteristics
networks = Counter()
has_price = 0
no_price = 0
old_tokens = 0
recent_tokens = 0

for token in tokens:
    # Count by network
    networks[token.get('network', 'unknown')] += 1
    
    # Check if has price data
    if token.get('price_at_call') or token.get('current_price'):
        has_price += 1
    else:
        no_price += 1
    
    # Check age
    created = token.get('created_at', '')
    if '2024' in created or '2023' in created:
        old_tokens += 1
    else:
        recent_tokens += 1

print("\n--- Characteristics ---")
print(f"Has price data: {has_price}")
print(f"No price data: {no_price}")
print(f"Old tokens (2023-2024): {old_tokens}")
print(f"Recent tokens (2025): {recent_tokens}")

print("\n--- By Network ---")
for network, count in networks.most_common():
    print(f"  {network}: {count}")

# Test a few tokens with DexScreener
print("\n--- Testing Sample Tokens ---")
sample_tokens = tokens[:5]

for token in sample_tokens:
    print(f"\n{token['ticker']} ({token['network']})")
    print(f"  Contract: {token['contract_address'][:20]}...")
    print(f"  Created: {token['created_at'][:10]}")
    
    # Try DexScreener API
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('pairs'):
                pair = data['pairs'][0]
                print(f"  ✅ Found on DexScreener: {pair.get('baseToken', {}).get('symbol')}")
                print(f"     FDV: ${pair.get('fdv', 'N/A')}")
                print(f"     Market Cap: ${pair.get('marketCap', 'N/A')}")
            else:
                print(f"  ❌ Not found on DexScreener (no pairs)")
        else:
            print(f"  ❌ DexScreener error: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error checking DexScreener: {e}")

# Check if these might be actually dead
print("\n--- Checking for Dead Tokens ---")
dead_characteristics = 0
for token in tokens[:50]:  # Check first 50
    if not token.get('current_price') and not token.get('price_at_call'):
        dead_characteristics += 1

print(f"Tokens with no price data at all: {dead_characteristics}/50 sampled")

print("\n" + "=" * 60)
print("RECOMMENDATION:")
if no_price > has_price:
    print("Most tokens have NO price data - likely dead/delisted")
    print("Action: Mark these as is_dead=true rather than retry")
else:
    print("Many tokens still have price data - might be worth retrying")
    print("Action: Retry with modified script to handle edge cases")
print("=" * 60)