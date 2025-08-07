#!/usr/bin/env python3
"""
Verify the backfill results
"""

import os
import warnings
warnings.filterwarnings("ignore")
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("=" * 60)
print("Verifying Backfill Results")
print("=" * 60)

# Count tokens with supply data
result = supabase.table('crypto_calls').select(
    'id', count='exact'
).not_.is_('total_supply', 'null').execute()

tokens_with_supply = result.count
print(f"\nTokens with supply data: {tokens_with_supply}")

# Count tokens with market_cap_at_call
result = supabase.table('crypto_calls').select(
    'id', count='exact'
).not_.is_('market_cap_at_call', 'null').execute()

tokens_with_mcap = result.count
print(f"Tokens with market_cap_at_call: {tokens_with_mcap}")

# Count tokens with current_market_cap
result = supabase.table('crypto_calls').select(
    'id', count='exact'
).not_.is_('current_market_cap', 'null').execute()

tokens_with_current_mcap = result.count
print(f"Tokens with current_market_cap: {tokens_with_current_mcap}")

# Get some sample tokens with market caps
print("\n" + "-" * 60)
print("Sample tokens with market caps:")
print("-" * 60)

result = supabase.table('crypto_calls').select(
    'ticker,price_at_call,total_supply,market_cap_at_call,current_price,current_market_cap'
).not_.is_('market_cap_at_call', 'null').order('market_cap_at_call', desc=True).limit(10).execute()

for token in result.data:
    print(f"\n{token['ticker']}:")
    print(f"  Price at call: ${token['price_at_call']:.8f}" if token['price_at_call'] else "  Price at call: None")
    print(f"  Total supply: {token['total_supply']:,.0f}" if token['total_supply'] else "  Total supply: None")
    print(f"  Market cap at call: ${token['market_cap_at_call']:,.0f}" if token['market_cap_at_call'] else "  Market cap at call: None")
    print(f"  Current price: ${token['current_price']:.8f}" if token['current_price'] else "  Current price: None")
    print(f"  Current market cap: ${token['current_market_cap']:,.0f}" if token['current_market_cap'] else "  Current market cap: None")

# Check for any errors (tokens without supply but with contract address)
result = supabase.table('crypto_calls').select(
    'id', count='exact'
).is_('total_supply', 'null').not_.is_('contract_address', 'null').neq('is_dead', True).execute()

tokens_needing_supply = result.count
print("\n" + "=" * 60)
print(f"Tokens still needing supply data: {tokens_needing_supply}")
print("=" * 60)