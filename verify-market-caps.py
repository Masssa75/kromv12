#!/usr/bin/env python3
"""
Verify that market caps are being correctly calculated
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
print("Verifying Market Cap Calculations")
print("=" * 60)

# Get tokens that were recently updated by ultra-tracker
result = supabase.table('crypto_calls').select(
    'ticker,current_price,current_market_cap,ath_price,ath_market_cap,'
    'circulating_supply,total_supply,price_updated_at'
).not_.is_('total_supply', 'null').not_.is_('current_market_cap', 'null')\
.order('price_updated_at', desc=True).limit(10).execute()

if not result.data:
    print("No recently updated tokens found")
    exit(1)

print("\nRecently updated tokens with market caps:\n")

correct_count = 0
mismatch_count = 0

for token in result.data:
    ticker = token['ticker']
    current_price = float(token['current_price'] or 0)
    current_mc = float(token['current_market_cap'] or 0)
    circ_supply = float(token['circulating_supply'] or 0)
    
    if current_price > 0 and circ_supply > 0:
        expected_mc = current_price * circ_supply
        diff_percent = abs(current_mc - expected_mc) / expected_mc * 100 if expected_mc > 0 else 0
        
        if diff_percent < 0.01:  # Less than 0.01% difference (rounding tolerance)
            status = "✅"
            correct_count += 1
        else:
            status = "❌"
            mismatch_count += 1
            
        print(f"{status} {ticker}:")
        print(f"   Price: ${current_price:.8f}")
        print(f"   Circulating: {circ_supply:,.0f}")
        print(f"   Current MC: ${current_mc:,.0f}")
        print(f"   Expected MC: ${expected_mc:,.0f}")
        
        if diff_percent > 0.01:
            print(f"   Difference: {diff_percent:.2f}%")
        
        # Check ATH market cap if exists
        if token['ath_market_cap'] and token['ath_price'] and token['total_supply']:
            ath_price = float(token['ath_price'])
            ath_mc = float(token['ath_market_cap'])
            total_supply = float(token['total_supply'])
            expected_ath_mc = ath_price * total_supply
            ath_diff = abs(ath_mc - expected_ath_mc) / expected_ath_mc * 100 if expected_ath_mc > 0 else 0
            
            if ath_diff < 0.01:
                print(f"   ATH MC: ${ath_mc:,.0f} ✅")
            else:
                print(f"   ATH MC: ${ath_mc:,.0f} (expected ${expected_ath_mc:,.0f}) ❌")
        
        print()

print("=" * 60)
print(f"Summary: {correct_count} correct, {mismatch_count} mismatches")
print("=" * 60)