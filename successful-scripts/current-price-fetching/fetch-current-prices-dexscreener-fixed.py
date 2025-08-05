#!/usr/bin/env python3
"""
Fixed DexScreener price fetcher - properly handles already processed tokens
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

# Keep track of processed tokens this session
processed_tokens = set()

def get_next_token():
    """Get ONE token that needs price, excluding already processed ones"""
    # Build exclusion list for query
    exclude_conditions = []
    if processed_tokens:
        # Create conditions to exclude each processed token
        for token_id in processed_tokens:
            exclude_conditions.append(f"id.neq.{token_id}")
    
    # Build query
    query = f"{SUPABASE_URL}/rest/v1/crypto_calls?"
    conditions = [
        "select=id,ticker,contract_address,network,price_at_call,krom_id",
        "current_price.is.null",
        "price_at_call.not.is.null",
        "contract_address.not.is.null",
        "network.not.is.null"
    ]
    
    # Add exclusions
    conditions.extend(exclude_conditions)
    
    # Add ordering and limit
    conditions.extend([
        "order=created_at.asc",
        "limit=1"
    ])
    
    query += "&".join(conditions)
    
    response = requests.get(query, headers=headers)
    
    if response.status_code != 200 or not response.json():
        return None
    
    return response.json()[0]

def main():
    print("🚀 DexScreener Price Fetcher (Fixed Version)")
    
    # Process up to 100 tokens
    for i in range(100):
        print(f"\n=== Token {i+1}/100 ===")
        
        # Get next token
        token = get_next_token()
        
        if not token:
            print("✅ No more tokens need prices!")
            break
        
        token_id = token['id']
        ticker = token.get('ticker', 'UNKNOWN')
        contract = token['contract_address']
        network = token['network']
        price_at_call = token.get('price_at_call', 0)
        krom_id = token.get('krom_id', 'N/A')
        
        # Add to processed set immediately
        processed_tokens.add(token_id)
        
        print(f"📊 Processing: {ticker} ({krom_id})")
        print(f"   Contract: {contract}")
        print(f"   Network: {network}")
        print(f"   Entry Price: ${price_at_call:.8f}")
        
        # Fetch from DexScreener
        url = f"https://api.dexscreener.com/latest/dex/tokens/{contract}"
        print(f"🔍 Fetching from DexScreener...")
        
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
                    print("❌ No pairs found for this token (likely dead)")
            else:
                print(f"❌ API error: {api_response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        # Small delay between requests
        time.sleep(1)
    
    print(f"\n✨ Processed {len(processed_tokens)} tokens total!")

if __name__ == "__main__":
    main()