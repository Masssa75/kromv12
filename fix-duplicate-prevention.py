#!/usr/bin/env python3
"""
Fix for duplicate token prevention - adds check for existing pool address
before inserting new tokens.
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import json

load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=== Checking for duplicate tokens with same pool address ===\n")

# Find duplicates by pool address
response = supabase.rpc('execute_sql', {
    'query': """
    SELECT pool_address, ticker, COUNT(*) as count, 
           array_agg(krom_id) as krom_ids,
           array_agg(created_at ORDER BY created_at DESC) as created_times
    FROM crypto_calls 
    WHERE pool_address IS NOT NULL
    GROUP BY pool_address, ticker
    HAVING COUNT(*) > 1
    ORDER BY COUNT(*) DESC, MAX(created_at) DESC
    LIMIT 20
    """
}).execute()

if response.data and len(response.data) > 0:
    print(f"Found {len(response.data)} sets of duplicate tokens:\n")
    
    for row in response.data:
        print(f"Token: {row['ticker']}")
        print(f"Pool: {row['pool_address']}")
        print(f"Duplicates: {row['count']}")
        print(f"KROM IDs: {', '.join(row['krom_ids'][:3])}...")
        print(f"Created: {row['created_times'][0]} (most recent)")
        print("-" * 60)
else:
    print("No duplicate tokens found!")

print("\n=== Suggested Fix ===")
print("""
To prevent future duplicates, modify crypto-poller to:

1. Check for existing pool_address before inserting:
   const existing = await supabase
     .from('crypto_calls')
     .select('id')
     .eq('pool_address', call.token.pa)
     .single()
   
   if (existing.data) {
     console.log(`Token already exists with pool ${call.token.pa}`)
     continue
   }

2. OR add a unique constraint on pool_address:
   ALTER TABLE crypto_calls 
   ADD CONSTRAINT unique_pool_address UNIQUE(pool_address);

3. OR update the existing record if pool found:
   const { data, error } = await supabase
     .from('crypto_calls')
     .upsert(callData, { onConflict: 'pool_address' })
""")

print("\n=== Cleanup Script ===")
print("To remove duplicates (keeping the oldest):")
print("""
DELETE FROM crypto_calls
WHERE id IN (
  SELECT id FROM (
    SELECT id, ROW_NUMBER() OVER (
      PARTITION BY pool_address 
      ORDER BY created_at ASC
    ) as rn
    FROM crypto_calls
    WHERE pool_address IS NOT NULL
  ) t
  WHERE rn > 1
);
""")