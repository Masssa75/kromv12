#!/usr/bin/env python3
"""Check BTH token market cap issue"""

from dotenv import load_dotenv
import os
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

# Check BTH token with the specific contract
result = supabase.table('crypto_calls').select(
    'ticker,contract_address,current_price,current_market_cap,'
    'price_updated_at,supply_updated_at,circulating_supply,total_supply'
).eq('contract_address', '81KzC6LsZEN4BGcMRcg5BoanAsXk4ctP8gFhQDweBAGS').execute()

for token in result.data:
    current_price = float(token['current_price']) if token['current_price'] else 0
    current_mc = float(token['current_market_cap']) if token['current_market_cap'] else 0
    circ_supply = float(token['circulating_supply']) if token['circulating_supply'] else 0
    
    calculated_mc = current_price * circ_supply
    
    print(f'BTH Token Analysis:')
    print(f'Current Price: ${current_price:.8f}')
    print(f'Current MC in DB: ${current_mc:,.0f}')
    print(f'Circulating Supply: {circ_supply:,.0f}')
    print(f'\nWhat MC should be: ${calculated_mc:,.0f}')
    print(f'\nTimestamps:')
    print(f'Price Updated: {token["price_updated_at"]}')
    print(f'Supply Updated: {token["supply_updated_at"]}')
    
    if abs(current_mc - calculated_mc) > 1000:  # More than $1000 difference
        print(f'\n❌ ERROR: Market cap is WRONG!')
        print(f'   DB has ${current_mc:,.0f}')
        print(f'   Should be ${calculated_mc:,.0f}')
        print(f'   Difference: ${abs(current_mc - calculated_mc):,.0f}')
        
        # Fix it
        print('\nFixing market cap...')
        update_result = supabase.table('crypto_calls').update({
            'current_market_cap': calculated_mc
        }).eq('contract_address', '81KzC6LsZEN4BGcMRcg5BoanAsXk4ctP8gFhQDweBAGS').execute()
        print('✅ Fixed!')
    else:
        print('\n✅ Market cap is correct')