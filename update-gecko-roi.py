#!/usr/bin/env python3
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(supabase_url, supabase_key)

print("Calculating ROI for GeckoTerminal tokens...")

# Get all gecko_trending tokens
result = supabase.table('crypto_calls').select('id,ticker,price_at_call,current_price').eq('source', 'gecko_trending').execute()

tokens = result.data
print(f"Found {len(tokens)} GeckoTerminal tokens")

for token in tokens:
    price_at_call = token['price_at_call']
    current_price = token['current_price']
    
    if not price_at_call or price_at_call == 0:
        print(f"Skipping {token['ticker']} - no price_at_call")
        continue
    
    # Calculate ROI: ((current - entry) / entry) * 100
    roi_percent = ((current_price - price_at_call) / price_at_call) * 100
    
    # Update the database
    supabase.table('crypto_calls').update({
        'roi_percent': roi_percent
    }).eq('id', token['id']).execute()
    
    print(f"✅ {token['ticker']}: ROI = {roi_percent:.2f}% (Entry: ${price_at_call}, Current: ${current_price})")

print("\nDone! ROI calculated for all GeckoTerminal tokens.")