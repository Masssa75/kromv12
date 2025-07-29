#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    'apikey': SUPABASE_SERVICE_ROLE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}'
}

# Get records where current_price is actually greater than 0
url = f'{SUPABASE_URL}/rest/v1/crypto_calls?select=ticker,current_price,roi_percent&current_price.gt.0&order=price_updated_at.desc&limit=20'

response = requests.get(url, headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f'✅ Successfully fetched current prices for tokens:')
    print('\nTokens with actual prices:')
    for i, r in enumerate(data):
        price = r['current_price']
        roi = r.get('roi_percent')
        roi_str = f' (ROI: {roi:+.1f}%)' if roi is not None else ''
        print(f'  {i+1}. {r["ticker"]}: ${price:.8f}{roi_str}')
        
# Count total with price > 0
count_url = f'{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.gt.0'
count_resp = requests.get(count_url, headers={**headers, 'Prefer': 'count=exact'}, params={'limit': 0})
if 'content-range' in count_resp.headers:
    total = count_resp.headers['content-range'].split('/')[-1]
    print(f'\n📊 TOTAL tokens with current_price > 0: {total}')
    
# Check BIP177 with the KROM ID we were updating
bip_url = f'{SUPABASE_URL}/rest/v1/crypto_calls?select=ticker,current_price,roi_percent,price_updated_at&krom_id=eq.6829fb9aeb25eec68c92d935'
bip_resp = requests.get(bip_url, headers=headers)
if bip_resp.status_code == 200 and bip_resp.json():
    bip = bip_resp.json()[0]
    print(f'\n🔍 BIP177 status (KROM ID: 6829fb9aeb25eec68c92d935):')
    print(f'   Current Price: ${bip["current_price"]:.8f}')
    print(f'   ROI: {bip["roi_percent"]:+.1f}%')
    print(f'   Updated: {bip["price_updated_at"]}')