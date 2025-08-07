#!/usr/bin/env python3
"""
Test if crypto-poller is correctly saving supply data
"""

import os
import warnings
warnings.filterwarnings("ignore")
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("=" * 60)
print("Testing Supply Data from crypto-poller")
print("=" * 60)

# Get most recent calls (last hour)
one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
print(f"\nFetching calls created in the last hour...")

result = supabase.table('crypto_calls').select(
    'id,ticker,created_at,price_at_call,total_supply,circulating_supply,market_cap_at_call,supply_updated_at'
).gte('created_at', one_hour_ago).order('created_at', desc=True).limit(10).execute()

if result.data:
    print(f"Found {len(result.data)} recent calls:\n")
    for call in result.data:
        print(f"Token: {call['ticker']}")
        print(f"  Created: {call['created_at']}")
        print(f"  Price at call: ${call['price_at_call']}" if call['price_at_call'] else "  Price at call: None")
        print(f"  Total supply: {call['total_supply']:,.0f}" if call['total_supply'] else "  Total supply: None")
        print(f"  Circulating supply: {call['circulating_supply']:,.0f}" if call['circulating_supply'] else "  Circulating supply: None")
        print(f"  Market cap at call: ${call['market_cap_at_call']:,.0f}" if call['market_cap_at_call'] else "  Market cap at call: None")
        print(f"  Supply updated: {call['supply_updated_at']}" if call['supply_updated_at'] else "  Supply updated: Never")
        print()
else:
    print("No calls found in the last hour")
    print("\nChecking last 5 calls regardless of time...")
    
    result = supabase.table('crypto_calls').select(
        'id,ticker,created_at,price_at_call,total_supply,circulating_supply,market_cap_at_call,supply_updated_at'
    ).order('created_at', desc=True).limit(5).execute()
    
    if result.data:
        for call in result.data:
            print(f"Token: {call['ticker']}")
            print(f"  Created: {call['created_at']}")
            print(f"  Price at call: ${call['price_at_call']}" if call['price_at_call'] else "  Price at call: None")
            print(f"  Total supply: {call['total_supply']:,.0f}" if call['total_supply'] else "  Total supply: None")
            print(f"  Circulating supply: {call['circulating_supply']:,.0f}" if call['circulating_supply'] else "  Circulating supply: None")
            print(f"  Market cap at call: ${call['market_cap_at_call']:,.0f}" if call['market_cap_at_call'] else "  Market cap at call: None")
            print(f"  Supply updated: {call['supply_updated_at']}" if call['supply_updated_at'] else "  Supply updated: Never")
            print()

print("=" * 60)