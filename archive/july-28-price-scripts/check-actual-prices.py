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
    "Content-Type": "application/json"
}

# Get actual count by checking database
query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=ticker,current_price,roi_percent&current_price.gt.0&order=price_updated_at.desc&limit=10"
response = requests.get(query, headers=headers)

if response.status_code == 200:
    tokens = response.json()
    print(f"✅ Tokens with actual current prices (> 0):")
    for token in tokens:
        ticker = token.get('ticker', 'UNKNOWN')
        price = token.get('current_price', 0)
        roi = token.get('roi_percent')
        roi_str = f" (ROI: {roi:+.1f}%)" if roi is not None else ""
        print(f"   - {ticker}: ${price:.8f}{roi_str}")
        
# Get total count
query2 = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.gt.0&limit=10000"
response2 = requests.get(query2, headers=headers)
if response2.status_code == 200:
    print(f"\n📊 Total tokens with actual prices: {len(response2.json())}")
