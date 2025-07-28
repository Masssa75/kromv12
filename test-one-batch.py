#!/usr/bin/env python3
"""
Test running just one batch to see what's happening
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Headers for Supabase API calls
headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

def get_tokens_needing_current_prices(limit=5):
    """Get tokens that need current price updates"""
    query = f"""
    {SUPABASE_URL}/rest/v1/crypto_calls?
    select=id,krom_id,contract_address,network,pool_address,ticker,current_price,price_at_call&
    current_price.is.null&
    price_at_call.not.is.null&
    contract_address.not.is.null&
    network.not.is.null&
    order=created_at.asc&
    limit={limit}
    """.replace('\n', '').replace(' ', '')
    
    print(f"🔍 Fetching {limit} tokens...")
    response = requests.get(query, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Error fetching tokens: {response.status_code}")
        print(response.text)
        return []
    
    tokens = response.json()
    print(f"📦 Found {len(tokens)} tokens")
    return tokens

def fetch_current_price(contract_address, network, pool_address=None):
    """Fetch current price using the crypto-price-single edge function"""
    payload = {
        "contractAddress": contract_address,
        "network": network,
        "callTimestamp": int(time.time()),
    }
    
    if pool_address:
        payload["poolAddress"] = pool_address
    
    try:
        response = requests.post(
            f"{SUPABASE_URL}/functions/v1/crypto-price-single",
            headers={
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "current_price": data.get("currentPrice"),
                "duration": data.get("duration")
            }
        else:
            return {
                "success": False,
                "error": f"Status {response.status_code}",
                "details": response.text[:100]
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    print("🧪 Testing One Batch of Current Price Fetching")
    
    # Get 5 tokens
    tokens = get_tokens_needing_current_prices(5)
    
    if not tokens:
        print("❌ No tokens found")
        return
    
    for i, token in enumerate(tokens, 1):
        krom_id = token.get('krom_id', 'N/A')
        ticker = token.get('ticker', 'UNKNOWN')
        contract_address = token['contract_address']
        network = token['network']
        pool_address = token.get('pool_address')
        price_at_call = token.get('price_at_call')
        
        print(f"\n[{i}/5] {ticker} ({krom_id}) - {network}")
        print(f"        Contract: {contract_address}")
        print(f"        Entry: ${price_at_call}")
        
        # Fetch current price
        result = fetch_current_price(contract_address, network, pool_address)
        
        if result["success"] and result["current_price"]:
            current_price = result["current_price"]
            duration = result.get("duration", "N/A")
            
            if price_at_call:
                roi = ((current_price - price_at_call) / price_at_call) * 100
                print(f"        ✅ Current: ${current_price:.8f} | ROI: {roi:+.1f}% ({duration}s)")
            else:
                print(f"        ✅ Current: ${current_price:.8f} ({duration}s)")
        else:
            error = result.get("error", "Unknown error")
            print(f"        ❌ {error}")

if __name__ == "__main__":
    main()