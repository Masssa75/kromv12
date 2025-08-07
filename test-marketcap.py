#!/usr/bin/env python3
"""Simple test of market cap updater"""

import os
import warnings
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
from supabase import create_client
import requests
from datetime import datetime

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("Fetching tokens...")
result = supabase.table('crypto_calls').select(
    'id,ticker,contract_address,current_price'
).not_.is_('current_price', 'null').is_('current_market_cap', 'null').limit(10).execute()

tokens = result.data
print(f"Found {len(tokens)} tokens")

# Process first 5 tokens individually
for token in tokens[:5]:
    if not token['contract_address']:
        continue
    
    print(f"\nProcessing {token['ticker']}...")
    
    # Call DexScreener
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}"
    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        if 'pairs' in data and data['pairs']:
            pair = data['pairs'][0]  # Get first pair
            
            fdv = pair.get('fdv')
            market_cap = pair.get('marketCap')
            price = float(pair.get('priceUsd', 0))
            
            if market_cap:
                # Calculate circulating supply
                circ_supply = market_cap / price if price > 0 else None
                
                # Update database
                update_data = {
                    'current_market_cap': market_cap,
                    'circulating_supply': circ_supply,
                    'supply_updated_at': datetime.utcnow().isoformat()
                }
                
                result = supabase.table('crypto_calls').update(update_data).eq('id', token['id']).execute()
                print(f"  ✅ Updated: MC=${market_cap:,.0f}")
            else:
                print(f"  ⚠️ No market cap data")
    else:
        print(f"  ❌ API error: {response.status_code}")

print("\nDone!")