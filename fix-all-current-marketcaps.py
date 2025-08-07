#!/usr/bin/env python3
"""Fix all current market caps by recalculating from current price × circulating supply"""

import os
import warnings
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("Fetching tokens with supply and price data...")

# Get all tokens with current price and circulating supply
result = supabase.table('crypto_calls').select(
    'id,ticker,current_price,current_market_cap,circulating_supply'
).not_.is_('current_price', 'null').not_.is_('circulating_supply', 'null').limit(1000).execute()

tokens = result.data
print(f"Found {len(tokens)} tokens to check")

fixed_count = 0
correct_count = 0

for token in tokens:
    current_price = float(token['current_price']) if token['current_price'] else 0
    current_mc = float(token['current_market_cap']) if token['current_market_cap'] else 0
    circ_supply = float(token['circulating_supply']) if token['circulating_supply'] else 0
    
    if current_price > 0 and circ_supply > 0:
        calculated_mc = current_price * circ_supply
        
        # Check if difference is more than 1%
        if current_mc > 0:
            diff_percent = abs(current_mc - calculated_mc) / current_mc * 100
        else:
            diff_percent = 100
        
        if diff_percent > 1:
            # Fix it
            try:
                supabase.table('crypto_calls').update({
                    'current_market_cap': calculated_mc
                }).eq('id', token['id']).execute()
                
                print(f"✅ {token['ticker']}: Fixed MC from ${current_mc:,.0f} to ${calculated_mc:,.0f} ({diff_percent:.1f}% diff)")
                fixed_count += 1
            except Exception as e:
                print(f"❌ {token['ticker']}: Error - {e}")
        else:
            correct_count += 1

print(f"\n" + "=" * 60)
print(f"Fixed {fixed_count} incorrect market caps")
print(f"Already correct: {correct_count}")
print("=" * 60)