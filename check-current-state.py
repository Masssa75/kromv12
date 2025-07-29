#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    'apikey': SUPABASE_SERVICE_ROLE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
}

# Get a sample of records
query = f'{SUPABASE_URL}/rest/v1/crypto_calls?select=id,ticker,current_price&order=price_updated_at.desc&limit=100'
resp = requests.get(query, headers=headers)
tokens = resp.json()

# Count nulls vs non-nulls
null_count = sum(1 for t in tokens if t['current_price'] is None)
non_null_count = sum(1 for t in tokens if t['current_price'] is not None)

print(f'Sample of 100 most recently updated tokens:')
print(f'  NULL current_price: {null_count}')
print(f'  Non-NULL current_price: {non_null_count}')
print()
print('Examples with current_price:')
for t in tokens[:20]:
    if t['current_price'] is not None:
        print(f'  {t["ticker"]}: ${t["current_price"]}')