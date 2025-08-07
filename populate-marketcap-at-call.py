#!/usr/bin/env python3
"""
Populate market_cap_at_call for tokens where circulating_supply ≈ total_supply
For pump.fun and similar tokens, supply is typically fixed at launch
"""

import os
import warnings
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

load_dotenv()

# Initialize Supabase with service role key
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

def populate_marketcap_at_call():
    """Calculate and populate market_cap_at_call using total_supply * price_at_call"""
    
    print("=" * 60)
    print("Market Cap at Call Calculator")
    print("=" * 60)
    
    # Get tokens with price_at_call and total_supply but no market_cap_at_call
    result = supabase.table('crypto_calls').select(
        'id,ticker,price_at_call,circulating_supply,total_supply,market_cap_at_call'
    ).not_.is_('price_at_call', 'null').not_.is_('total_supply', 'null').is_('market_cap_at_call', 'null').execute()
    
    tokens = result.data
    print(f"\nFound {len(tokens)} tokens to process")
    
    updated_count = 0
    skipped_count = 0
    
    for i, token in enumerate(tokens, 1):
        ticker = token['ticker']
        price_at_call = float(token['price_at_call'])
        circ_supply = float(token['circulating_supply']) if token['circulating_supply'] else None
        total_supply = float(token['total_supply'])
        
        # Check if circulating and total are approximately equal (within 1%)
        if circ_supply:
            diff_percent = abs(circ_supply - total_supply) / total_supply * 100 if total_supply > 0 else 100
            
            if diff_percent > 1:
                print(f"  [{i}] {ticker}: Skipping - supplies differ by {diff_percent:.1f}%")
                skipped_count += 1
                continue
        
        # Calculate market cap at call using total supply
        market_cap_at_call = price_at_call * total_supply
        
        # Update database
        try:
            update_result = supabase.table('crypto_calls').update({
                'market_cap_at_call': market_cap_at_call
            }).eq('id', token['id']).execute()
            
            print(f"  [{i}] {ticker}: ✅ Market cap at call: ${market_cap_at_call:,.2f}")
            updated_count += 1
            
        except Exception as e:
            print(f"  [{i}] {ticker}: ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print(f"Processing complete!")
    print(f"Updated: {updated_count} tokens")
    print(f"Skipped: {skipped_count} tokens (supply mismatch)")
    print("=" * 60)
    
    # Show some examples
    if updated_count > 0:
        print("\nSample of updated tokens:")
        sample_result = supabase.table('crypto_calls').select(
            'ticker,price_at_call,total_supply,market_cap_at_call'
        ).not_.is_('market_cap_at_call', 'null').order('market_cap_at_call', desc=True).limit(5).execute()
        
        for token in sample_result.data:
            print(f"  {token['ticker']}: ${token['market_cap_at_call']:,.0f} "
                  f"(${token['price_at_call']:.6f} × {token['total_supply']/1000000:.1f}M)")

if __name__ == "__main__":
    populate_marketcap_at_call()