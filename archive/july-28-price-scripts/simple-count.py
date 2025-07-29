#\!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Simple count query
url = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=ticker,current_price&current_price.gt.0&limit=50"

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    print(f"✅ Found {len(data)} tokens with current prices > 0")
    
    # Show first 20
    print("\nFirst 20 tokens with prices:")
    for i, token in enumerate(data[:20]):
        price = token.get('current_price', 0)
        ticker = token.get('ticker', 'UNKNOWN')
        print(f"   {i+1}. {ticker}: ${price:.8f}")
        
    # Check BIP177 specifically with its actual KROM ID
    print("\n🔍 Checking specific BIP177 record (6829fb9aeb25eec68c92d935):")
    bip_url = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=*&krom_id=eq.6829fb9aeb25eec68c92d935"
    bip_resp = requests.get(bip_url, headers=headers)
    
    if bip_resp.status_code == 200 and bip_resp.json():
        bip = bip_resp.json()[0]
        print(f"   Ticker: {bip.get('ticker')}")
        print(f"   Current Price: {bip.get('current_price')}")
        print(f"   ROI: {bip.get('roi_percent')}%")
        print(f"   Updated: {bip.get('price_updated_at')}")
else:
    print(f"Error: {response.status_code}")
