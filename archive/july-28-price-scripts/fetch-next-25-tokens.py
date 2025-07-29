#!/usr/bin/env python3
"""
Fetch current prices for the next 25 tokens that need current prices
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

def get_next_25_tokens():
    """Get next 25 tokens that need current prices"""
    query = f"""
    {SUPABASE_URL}/rest/v1/crypto_calls?
    select=id,krom_id,contract_address,network,pool_address,ticker,current_price,price_at_call,created_at&
    current_price.is.null&
    price_at_call.not.is.null&
    contract_address.not.is.null&
    network.not.is.null&
    order=created_at.asc&
    limit=25
    """.replace('\n', '').replace(' ', '')
    
    print(f"🔍 Fetching next 25 tokens needing current prices...")
    response = requests.get(query, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Error fetching tokens: {response.status_code}")
        print(response.text)
        return []
    
    tokens = response.json()
    print(f"📦 Found {len(tokens)} tokens to process")
    return tokens

def fetch_current_price(contract_address, network, pool_address=None):
    """Fetch current price using the crypto-price-single edge function"""
    # Network mapping - KROM stores "ethereum" but GeckoTerminal API requires "eth"
    network_map = {
        'ethereum': 'eth',
        'solana': 'solana',
        'bsc': 'bsc',
        'polygon': 'polygon',
        'arbitrum': 'arbitrum',
        'base': 'base'
    }
    
    mapped_network = network_map.get(network, network)
    
    payload = {
        "contractAddress": contract_address,
        "network": mapped_network,
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
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "current_price": data.get("currentPrice"),
                "market_cap": data.get("currentMarketCap"),
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

def update_token_current_price(token_id, current_price, current_market_cap=None):
    """Update token's current price in database"""
    update_data = {
        "current_price": current_price,
        "price_updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if current_market_cap is not None:
        update_data["current_market_cap"] = current_market_cap
    
    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/crypto_calls?id=eq.{token_id}",
        headers=headers,
        json=update_data
    )
    
    return response.status_code == 204

def calculate_and_update_roi(token_id, price_at_call, current_price):
    """Calculate and update ROI percentage"""
    if price_at_call and current_price and price_at_call > 0:
        roi_percent = ((current_price - price_at_call) / price_at_call) * 100
        
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/crypto_calls?id=eq.{token_id}",
            headers=headers,
            json={"roi_percent": roi_percent}
        )
        
        return response.status_code == 204, roi_percent
    
    return False, None

def main():
    print("🚀 Fetching Current Prices for Next 25 Tokens")
    print(f"📊 Supabase URL: {SUPABASE_URL}")
    print()
    
    # Get next 25 tokens
    tokens = get_next_25_tokens()
    
    if not tokens:
        print("✅ No more tokens need current price updates!")
        return
    
    successful = 0
    failed = 0
    
    print("📋 Processing tokens:")
    print("=" * 80)
    
    for i, token in enumerate(tokens, 1):
        token_id = token['id']
        krom_id = token.get('krom_id', 'N/A')
        ticker = token.get('ticker', 'UNKNOWN')
        contract_address = token['contract_address']
        network = token['network']
        pool_address = token.get('pool_address')
        price_at_call = token.get('price_at_call')
        created_at = token.get('created_at', '')
        
        print(f"\n[{i:2d}/25] {ticker} ({krom_id}) - {network}")
        print(f"         Created: {created_at[:10]}")
        print(f"         Entry: ${price_at_call}")
        
        # Fetch current price
        result = fetch_current_price(contract_address, network, pool_address)
        
        if result["success"] and result["current_price"]:
            current_price = result["current_price"]
            market_cap = result.get("market_cap")
            duration = result.get("duration", "N/A")
            
            # Update database
            if update_token_current_price(token_id, current_price, market_cap):
                # Calculate ROI
                roi_updated, roi_percent = calculate_and_update_roi(
                    token_id, price_at_call, current_price
                )
                
                roi_str = f" | ROI: {roi_percent:+.1f}%" if roi_updated else ""
                print(f"         ✅ Current: ${current_price:.8f}{roi_str} ({duration}s)")
                successful += 1
            else:
                print(f"         ❌ Database update failed")
                failed += 1
        else:
            error = result.get("error", "Unknown error")
            print(f"         ❌ {error}")
            failed += 1
        
        # Small delay between requests
        time.sleep(0.2)
    
    print("\n" + "=" * 80)
    print(f"🎉 Batch Complete! ✅ {successful} successful, ❌ {failed} failed")
    print(f"📊 Success Rate: {successful/25*100:.1f}%")

if __name__ == "__main__":
    main()