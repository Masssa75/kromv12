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

print("Checking token distribution by network...\n")

# Get count by network for active tokens
networks = ['solana', 'ethereum', 'bsc', 'polygon', 'arbitrum', 'base', 'avalanche', 'optimism']

total = 0
for network in networks:
    result = supabase.table('crypto_calls').select(
        'count'
    ).eq('network', network).gt('liquidity_usd', 1000).execute()
    
    count = result.data[0]['count'] if result.data else 0
    total += count
    print(f"{network:12} : {count:5} tokens")

print(f"\n{'TOTAL':12} : {total:5} tokens with >$1K liquidity")

# Also check total tokens that need tracking
all_result = supabase.table('crypto_calls').select(
    'count'
).gt('liquidity_usd', 1000).execute()

all_count = all_result.data[0]['count'] if all_result.data else 0
print(f"All networks : {all_count:5} tokens (including other networks)")