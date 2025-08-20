#!/usr/bin/env python3
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(supabase_url, supabase_key)

print("Initializing ATH for GeckoTerminal tokens...")

# Get all gecko_trending tokens without ATH
result = supabase.table('crypto_calls').select('id,ticker,price_at_call,current_price,market_cap_at_call,buy_timestamp').eq('source', 'gecko_trending').is_('ath_price', 'null').execute()

tokens = result.data
print(f"Found {len(tokens)} tokens without ATH initialization")

for token in tokens:
    # Set initial ATH to the price_at_call (entry price)
    ath_price = token['price_at_call'] or token['current_price']
    
    if not ath_price:
        print(f"Skipping {token['ticker']} - no price data")
        continue
    
    update_data = {
        'ath_price': ath_price,
        'ath_timestamp': token['buy_timestamp'],
        'ath_roi_percent': 0.0,  # Start at 0% ROI
        'ath_market_cap': token['market_cap_at_call']
    }
    
    supabase.table('crypto_calls').update(update_data).eq('id', token['id']).execute()
    print(f"✅ Initialized ATH for {token['ticker']}: ${ath_price}")

print("\nDone! ATH initialized for all GeckoTerminal tokens.")