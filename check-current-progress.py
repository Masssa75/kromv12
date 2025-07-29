#!/usr/bin/env python3
"""
Check current price fetching progress
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    'apikey': SUPABASE_SERVICE_ROLE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
    'Content-Type': 'application/json'
}

# Check tokens with current prices
query = f'{SUPABASE_URL}/rest/v1/crypto_calls?select=id,ticker,current_price,price_updated_at&current_price.not.is.null&order=price_updated_at.desc&limit=10'
response = requests.get(query, headers=headers)

if response.status_code == 200:
    tokens = response.json()
    print(f'✅ Recent tokens with current prices:')
    for token in tokens[:5]:
        price = token.get('current_price')
        ticker = token.get('ticker', 'UNKNOWN')
        updated = token.get('price_updated_at', 'Unknown')
        if price:
            print(f'   - {ticker}: ${float(price):.8f} (updated: {updated[:19]})')

# Count total with prices
count_query = f'{SUPABASE_URL}/rest/v1/crypto_calls?select=ticker&current_price.not.is.null'
count_resp = requests.get(count_query, headers=headers)
if count_resp.status_code == 200:
    total_with_prices = len(count_resp.json())
    print(f'\n📊 Total tokens with current prices: {total_with_prices}/5707 ({total_with_prices/5707*100:.1f}%)')
    
# Count needing prices
need_query = f'{SUPABASE_URL}/rest/v1/crypto_calls?select=ticker&current_price.is.null&price_at_call.gt.0&contract_address.not.is.null&network.not.is.null'
need_resp = requests.get(need_query, headers=headers)
if need_resp.status_code == 200:
    need_prices = len(need_resp.json())
    print(f'📈 Tokens still needing current prices: {need_prices}')
    
    # Show a few that need prices
    if need_prices > 0:
        sample_query = f'{SUPABASE_URL}/rest/v1/crypto_calls?select=ticker,network,price_at_call&current_price.is.null&price_at_call.gt.0&contract_address.not.is.null&network.not.is.null&limit=5'
        sample_resp = requests.get(sample_query, headers=headers)
        if sample_resp.status_code == 200:
            samples = sample_resp.json()
            print(f'\n🔄 Sample tokens still needing prices:')
            for s in samples:
                print(f'   - {s["ticker"]} ({s["network"]}) - price_at_call: {s["price_at_call"]}')