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

print("Checking ACTIVE (non-dead) tokens...\n")

# Check tokens with is_dead flag
dead_result = supabase.table('crypto_calls').select(
    'count'
).eq('is_dead', True).execute()

not_dead_result = supabase.table('crypto_calls').select(
    'count'
).eq('is_dead', False).execute()

null_dead_result = supabase.table('crypto_calls').select(
    'count'
).is_('is_dead', None).execute()

dead_count = dead_result.data[0]['count'] if dead_result.data else 0
not_dead_count = not_dead_result.data[0]['count'] if not_dead_result.data else 0
null_dead_count = null_dead_result.data[0]['count'] if null_dead_result.data else 0

print("Token Status:")
print("-" * 40)
print(f"is_dead = True  : {dead_count:5} tokens")
print(f"is_dead = False : {not_dead_count:5} tokens") 
print(f"is_dead = NULL  : {null_dead_count:5} tokens")
print(f"TOTAL           : {dead_count + not_dead_count + null_dead_count:5} tokens")

# Now check active tokens by volume
print("\n\nACTIVE Tokens Volume Distribution:")
print("-" * 40)

volume_tiers = [
    (1000000, float('inf'), '>$1M'),
    (100000, 1000000, '$100K-$1M'),
    (10000, 100000, '$10K-$100K'),
    (1000, 10000, '$1K-$10K'),
    (0, 1000, '<$1K'),
]

total_active = 0
for min_vol, max_vol, label in volume_tiers:
    if max_vol == float('inf'):
        result = supabase.table('crypto_calls').select(
            'count'
        ).gt('volume_24h', min_vol).neq('is_dead', True).gt('liquidity_usd', 1000).execute()
    else:
        result = supabase.table('crypto_calls').select(
            'count'
        ).gte('volume_24h', min_vol).lt('volume_24h', max_vol).neq('is_dead', True).gt('liquidity_usd', 1000).execute()
    
    count = result.data[0]['count'] if result.data else 0
    total_active += count
    print(f"{label:15} : {count:5} tokens")

print("-" * 40)
print(f"{'TOTAL ACTIVE':15} : {total_active:5} tokens (not dead, >$1K liquidity)")

# Check what the ultra tracker actually queries
print("\n\nWhat Ultra Tracker Actually Processes:")
print("-" * 40)
# Based on the code: .not('pool_address', 'is', null).eq('is_invalidated', false)
actual_result = supabase.table('crypto_calls').select(
    'count'
).neq('pool_address', None).eq('is_invalidated', False).neq('is_dead', True).execute()

actual_count = actual_result.data[0]['count'] if actual_result.data else 0
print(f"Tokens with pool_address, not invalidated, not dead: {actual_count}")

# Also check without the is_dead filter to see if that's the issue
without_dead_filter = supabase.table('crypto_calls').select(
    'count'
).neq('pool_address', None).eq('is_invalidated', False).execute()

without_dead_count = without_dead_filter.data[0]['count'] if without_dead_filter.data else 0
print(f"Tokens with pool_address, not invalidated (includes dead): {without_dead_count}")