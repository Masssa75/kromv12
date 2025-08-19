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

print("Analyzing token split by liquidity threshold...\n")

# Check different liquidity thresholds
thresholds = [10000, 15000, 20000, 25000, 30000, 50000]

for threshold in thresholds:
    # Tokens above threshold (main tracker - high priority)
    above = supabase.table('crypto_calls').select(
        'count'
    ).gte('liquidity_usd', threshold).neq('is_dead', True).neq('pool_address', None).eq('is_invalidated', False).execute()
    
    # Tokens below threshold but above $1K (low priority tracker)
    below = supabase.table('crypto_calls').select(
        'count'
    ).gte('liquidity_usd', 1000).lt('liquidity_usd', threshold).neq('is_dead', True).neq('pool_address', None).eq('is_invalidated', False).execute()
    
    above_count = above.data[0]['count'] if above.data else 0
    below_count = below.data[0]['count'] if below.data else 0
    
    print(f"Threshold: ${threshold:,}")
    print(f"  Main tracker (>=${threshold:,}): {above_count:,} tokens")
    print(f"  Low-priority tracker ($1K-${threshold:,}): {below_count:,} tokens")
    print(f"  Total: {above_count + below_count:,} tokens")
    print()

# Recommended split
print("=" * 50)
print("RECOMMENDATION: Use $10K threshold")
print("=" * 50)

# Get exact counts for $10K threshold
main_tracker = supabase.table('crypto_calls').select(
    'count'
).gte('liquidity_usd', 10000).neq('is_dead', True).neq('pool_address', None).eq('is_invalidated', False).execute()

low_priority = supabase.table('crypto_calls').select(
    'count'
).gte('liquidity_usd', 1000).lt('liquidity_usd', 10000).neq('is_dead', True).neq('pool_address', None).eq('is_invalidated', False).execute()

main_count = main_tracker.data[0]['count'] if main_tracker.data else 0
low_count = low_priority.data[0]['count'] if low_priority.data else 0

print(f"\nMain Ultra Tracker (>=$10K liquidity):")
print(f"  {main_count:,} tokens - Run every minute")
print(f"  These are active, liquid tokens likely to have ATH movements")

print(f"\nLow-Priority Tracker ($1K-$10K liquidity):")
print(f"  {low_count:,} tokens - Run every 10-15 minutes")
print(f"  These are less liquid, less likely to move quickly")

print(f"\nBenefit: Main tracker processes {3994-main_count:,} fewer tokens!")
print(f"Result: Should easily fit within CPU limits!")