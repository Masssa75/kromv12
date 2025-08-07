#!/usr/bin/env python3
"""
Check if the recently re-added tokens have supply data
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
print("Checking Supply Data for Recently Added Tokens")
print("=" * 60)

# Check specific tokens that were just re-added
tokens_to_check = ['FUH', 'MONO', 'PROTECT', 'SSI']

for ticker in tokens_to_check:
    result = supabase.table('crypto_calls').select(
        'ticker,created_at,price_at_call,total_supply,circulating_supply,'
        'market_cap_at_call,supply_updated_at,volume_24h,liquidity_usd'
    ).eq('ticker', ticker).order('created_at', desc=True).limit(1).execute()
    
    if result.data:
        call = result.data[0]
        print(f"\n{ticker}:")
        print(f"  Created: {call['created_at']}")
        print(f"  Price at call: ${call['price_at_call']:.8f}" if call['price_at_call'] else "  Price at call: None")
        
        if call['total_supply']:
            print(f"  Total supply: {call['total_supply']:,.0f}")
        else:
            print(f"  Total supply: None ❌")
            
        if call['circulating_supply']:
            print(f"  Circulating supply: {call['circulating_supply']:,.0f}")
        else:
            print(f"  Circulating supply: None ❌")
            
        if call['market_cap_at_call']:
            print(f"  Market cap at call: ${call['market_cap_at_call']:,.0f} ✅")
        else:
            print(f"  Market cap at call: None ⚠️")
            
        print(f"  Volume 24h: ${call['volume_24h']:,.0f}" if call['volume_24h'] else "  Volume 24h: None")
        print(f"  Liquidity: ${call['liquidity_usd']:,.0f}" if call['liquidity_usd'] else "  Liquidity: None")
        print(f"  Supply updated: {call['supply_updated_at']}" if call['supply_updated_at'] else "  Supply updated: Never")
    else:
        print(f"\n{ticker}: Not found in database")

print("\n" + "=" * 60)
print("Summary:")
print("✅ = Field populated correctly")
print("❌ = Field missing (should be populated)")
print("⚠️ = Field may be missing (depends on supply similarity)")
print("=" * 60)