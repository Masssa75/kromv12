#!/usr/bin/env python3
import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(supabase_url, supabase_key)

print("Analyzing volume distribution...\n")

# Define volume tiers
volume_tiers = [
    (1000000, float('inf'), '>$1M'),      # High volume
    (100000, 1000000, '$100K-$1M'),       # Medium-high
    (10000, 100000, '$10K-$100K'),        # Medium
    (1000, 10000, '$1K-$10K'),            # Low-medium
    (0, 1000, '<$1K'),                    # Low
]

print("Volume Tier Distribution:")
print("-" * 40)

total_with_liquidity = 0
for min_vol, max_vol, label in volume_tiers:
    if max_vol == float('inf'):
        result = supabase.table('crypto_calls').select(
            'count'
        ).gt('volume_24h', min_vol).gt('liquidity_usd', 1000).execute()
    else:
        result = supabase.table('crypto_calls').select(
            'count'
        ).gte('volume_24h', min_vol).lt('volume_24h', max_vol).gt('liquidity_usd', 1000).execute()
    
    count = result.data[0]['count'] if result.data else 0
    total_with_liquidity += count
    print(f"{label:15} : {count:5} tokens")

print("-" * 40)
print(f"{'TOTAL':15} : {total_with_liquidity:5} tokens with >$1K liquidity")

# Also show tokens with null volume
null_volume = supabase.table('crypto_calls').select(
    'count'
).is_('volume_24h', None).gt('liquidity_usd', 1000).execute()

null_count = null_volume.data[0]['count'] if null_volume.data else 0
print(f"{'NULL volume':15} : {null_count:5} tokens (need initial fetch)")

print("\n\nProposed Processing Strategy:")
print("=" * 50)
print("\nTier 1 (Every minute): >$100K volume")
print("  - Highest priority, most active tokens")
print("  - Most likely to have ATH movements")
print("\nTier 2 (Every 2 minutes): $10K-$100K volume") 
print("  - Medium priority tokens")
print("  - Still active but less volatile")
print("\nTier 3 (Every 5 minutes): <$10K volume")
print("  - Lower priority tokens")
print("  - Less likely to have rapid movements")
print("\nThis ensures all tokens are checked within 5 minutes max!")