#!/usr/bin/env python3
"""Analyze strategy for processing live tokens more frequently"""

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

print("Analyzing Live Token Processing Strategy")
print("="*60)

# Get total tokens
response = supabase.table('crypto_calls').select(
    'count', count='exact'
).not_.is_('pool_address', 'null').eq(
    'is_dead', False
).eq(
    'is_invalidated', False
).execute()

total_tokens = response.count
print(f"Total 'active' tokens in database: {total_tokens}")

# Check how many were updated recently (likely live)
recent_cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
response = supabase.table('crypto_calls').select(
    'count', count='exact'
).gte('price_updated_at', recent_cutoff).eq(
    'is_dead', False
).execute()

recently_updated = response.count
print(f"Tokens updated in last hour: {recently_updated}")

# Estimate live tokens based on our 52% coverage
estimated_live = int(total_tokens * 0.40)  # 40% as you suggested
print(f"Estimated live tokens (40%): {estimated_live}")

print(f"\n{'='*60}")
print("CURRENT SITUATION:")
print(f"  Processing rate: ~400 tokens/minute")
print(f"  Total tokens: {total_tokens}")
print(f"  Time to process all: {total_tokens/400:.1f} minutes")
print(f"  Problem: Wasting time on dead tokens")

print(f"\n{'='*60}")
print("PROPOSED STRATEGY:")
print("1. Add 'is_live' field to track tokens with DexScreener data")
print("2. When DexScreener returns no data, mark token as not live")
print("3. When DexScreener returns data, mark token as live")
print("4. Process live tokens every minute")
print("5. Check dead tokens once per hour to see if they're active again")

print(f"\n{'='*60}")
print("IMPLEMENTATION PLAN:")

# Calculate processing with live tokens only
live_tokens = estimated_live
processing_rate = 400  # tokens per minute

print(f"\nScenario 1: Process only live tokens (~{live_tokens} tokens)")
print(f"  Time to process all live tokens: {live_tokens/processing_rate:.1f} minutes")
print(f"  ✅ All live tokens updated every {live_tokens/processing_rate:.1f} minutes")

# With increased batch size
print(f"\nScenario 2: Increase batch to 30, process ~600 tokens/min")
processing_rate_optimized = 600
print(f"  Time to process all live tokens: {live_tokens/processing_rate_optimized:.1f} minutes")
print(f"  ✅ All live tokens updated every {live_tokens/processing_rate_optimized:.1f} minutes")

# Two-tier system
print(f"\nScenario 3: Two-tier system")
print(f"  - Process {live_tokens} live tokens every minute")
print(f"  - Process {total_tokens - live_tokens} dead tokens once per hour")
print(f"  - Live token update frequency: every {live_tokens/processing_rate:.1f} minutes")
print(f"  - Dead token check frequency: every 60 minutes")

print(f"\n{'='*60}")
print("DATABASE CHANGES NEEDED:")
print("""
1. Add new field:
   ALTER TABLE crypto_calls ADD COLUMN is_live BOOLEAN DEFAULT true;
   
2. Add index for performance:
   CREATE INDEX idx_live_tokens ON crypto_calls(is_live, ath_last_checked) 
   WHERE is_dead = false AND is_invalidated = false;

3. Update ultra-tracker query:
   - Primary: WHERE is_live = true ORDER BY ath_last_checked
   - Secondary: WHERE is_live = false AND last_live_check < 1 hour ago
""")

print(f"\n{'='*60}")
print("BENEFITS:")
print(f"✅ Live tokens get ATH updates every {live_tokens/processing_rate:.1f} minutes")
print("✅ Dead tokens don't waste processing time")
print("✅ Tokens can be revived if they start trading again")
print("✅ More efficient use of API calls")
print("✅ Better ATH notification timing")

# Check token distribution by age
print(f"\n{'='*60}")
print("TOKEN AGE ANALYSIS:")

for days in [1, 3, 7, 14, 30]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    response = supabase.table('crypto_calls').select(
        'count', count='exact'
    ).gte('created_at', cutoff).eq(
        'is_dead', False
    ).eq(
        'is_invalidated', False
    ).execute()
    
    count = response.count
    print(f"  Tokens from last {days:2} days: {count:4} ({count*100/total_tokens:5.1f}%)")

print(f"\n{'='*60}")
print("RECOMMENDATION:")
print("Implement the is_live field and two-tier processing system.")
print(f"This will ensure all actively trading tokens get updates every {live_tokens/processing_rate:.1f} minutes.")