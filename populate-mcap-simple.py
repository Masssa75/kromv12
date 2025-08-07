#!/usr/bin/env python3
"""Simple script to populate market_cap_at_call"""

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

print("Fetching tokens...")

# Get first 100 tokens to test
result = supabase.table('crypto_calls').select(
    'id,ticker,price_at_call,total_supply,market_cap_at_call'
).not_.is_('price_at_call', 'null').not_.is_('total_supply', 'null').is_('market_cap_at_call', 'null').limit(500).execute()

tokens = result.data
print(f"Processing {len(tokens)} tokens...")

updated = 0
for token in tokens:  # Process all
    mcap = float(token['price_at_call']) * float(token['total_supply'])
    
    try:
        supabase.table('crypto_calls').update({
            'market_cap_at_call': mcap
        }).eq('id', token['id']).execute()
        
        print(f"✅ {token['ticker']}: ${mcap:,.0f}")
        updated += 1
    except Exception as e:
        print(f"❌ {token['ticker']}: {e}")

print(f"\nUpdated {updated} tokens")