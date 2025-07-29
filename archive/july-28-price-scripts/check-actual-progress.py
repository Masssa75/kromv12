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

# Count tokens with current prices > 0
query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.gt.0"
response = requests.get(query, headers=headers)

if response.status_code == 200:
    # Get the actual count from the response
    tokens_with_prices = len(response.json())
    print(f"✅ Tokens with current prices (> 0): {tokens_with_prices}")
    
    # Also check tokens with any non-null current price
    query2 = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.not.is.null"
    response2 = requests.get(query2, headers=headers)
    
    if response2.status_code == 200:
        total_with_price_field = len(response2.json())
        print(f"📊 Tokens with non-null current_price: {total_with_price_field}")
        
    # Check for duplicates like BIP177
    query3 = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=ticker,krom_id,current_price&ticker.eq.BIP177"
    response3 = requests.get(query3, headers=headers)
    
    if response3.status_code == 200:
        bip177_records = response3.json()
        print(f"\n🔍 BIP177 duplicates found: {len(bip177_records)}")
        for i, record in enumerate(bip177_records):
            print(f"   {i+1}. KROM ID: {record['krom_id']}, Current Price: {record['current_price']}")
            
    # Get last 10 tokens with prices
    query4 = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=ticker,current_price,roi_percent,price_updated_at&current_price.gt.0&order=price_updated_at.desc&limit=10"
    response4 = requests.get(query4, headers=headers)
    
    if response4.status_code == 200:
        recent = response4.json()
        print(f"\n📈 Last 10 tokens with current prices:")
        for token in recent:
            roi = f" (ROI: {token['roi_percent']:+.1f}%)" if token.get('roi_percent') is not None else ""
            print(f"   - {token['ticker']}: ${token['current_price']:.8f}{roi}")
