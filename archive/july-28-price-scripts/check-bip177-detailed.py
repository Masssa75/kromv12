#\!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
}

# Search for BIP177
query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id,ticker,krom_id,current_price,price_updated_at&ticker.eq.BIP177"
response = requests.get(query, headers=headers)

if response.status_code == 200:
    results = response.json()
    print(f"Found {len(results)} tokens with ticker BIP177:")
    for r in results:
        print(f"  ID: {r['id']}")
        print(f"  Ticker: {r['ticker']}")
        print(f"  KROM ID: {r['krom_id']}")
        print(f"  Current Price: {r['current_price']}")
        print(f"  Updated: {r['price_updated_at']}")
        print()
