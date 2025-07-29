#!/usr/bin/env python3
"""
Simple DexScreener price fetcher - processes one token at a time
"""

import os
import sys
import time
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

print("🚀 DexScreener Price Fetcher (Simple Version)")

# Get ONE token that needs price
query = f"""
{SUPABASE_URL}/rest/v1/crypto_calls?
select=id,ticker,contract_address,network,price_at_call,krom_id&
current_price.is.null&
price_at_call.not.is.null&
contract_address.not.is.null&
network.not.is.null&
order=created_at.asc&
limit=1
""".replace('\n', '').replace(' ', '')

response = requests.get(query, headers=headers)

if response.status_code != 200 or not response.json():
    print("❌ No tokens need prices or error fetching")
    sys.exit(0)

token = response.json()[0]
token_id = token['id']
ticker = token.get('ticker', 'UNKNOWN')
contract = token['contract_address']
network = token['network']
price_at_call = token.get('price_at_call', 0)

print(f"\n📊 Processing: {ticker}")
print(f"   Contract: {contract}")
print(f"   Network: {network}")
print(f"   Entry Price: ${price_at_call:.8f}")

# Fetch from DexScreener
url = f"https://api.dexscreener.com/latest/dex/tokens/{contract}"
print(f"\n🔍 Fetching from DexScreener...")

try:
    api_response = requests.get(url, timeout=10)
    
    if api_response.status_code == 200:
        data = api_response.json()
        pairs = data.get('pairs', [])
        
        if pairs:
            # Get first pair (highest liquidity)
            pair = pairs[0]
            current_price = float(pair.get('priceUsd', 0))
            
            if current_price > 0:
                print(f"✅ Found price: ${current_price:.8f}")
                
                # Calculate ROI
                roi = ((current_price - price_at_call) / price_at_call * 100) if price_at_call > 0 else 0
                print(f"📈 ROI: {roi:+.1f}%")
                
                # Update database
                update_data = {
                    "current_price": current_price,
                    "price_updated_at": datetime.now(timezone.utc).isoformat(),
                    "roi_percent": roi
                }
                
                update_response = requests.patch(
                    f"{SUPABASE_URL}/rest/v1/crypto_calls?id=eq.{token_id}",
                    headers=headers,
                    json=update_data
                )
                
                if update_response.status_code == 204:
                    print("✅ Database updated successfully!")
                else:
                    print(f"❌ Database update failed: {update_response.status_code}")
            else:
                print("❌ No valid price found")
        else:
            print("❌ No pairs found for this token")
    else:
        print(f"❌ API error: {api_response.status_code}")
        
except Exception as e:
    print(f"❌ Exception: {e}")

print("\n✨ Done!")