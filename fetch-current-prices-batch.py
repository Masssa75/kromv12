#!/usr/bin/env python3
"""
Batch Current Price Fetcher

This script fetches current prices for all tokens in the database using the 
crypto-price-single Supabase Edge Function. It updates the current_price and 
price_updated_at columns.

Usage:
    python3 fetch-current-prices-batch.py

Environment Variables Required:
    SUPABASE_URL - Supabase project URL
    SUPABASE_SERVICE_ROLE_KEY - Service role key for database access
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

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Error: Missing required environment variables")
    print("Required: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
    sys.exit(1)

# Supabase Edge Function URL
EDGE_FUNCTION_URL = f"{SUPABASE_URL}/functions/v1/crypto-price-single"

# Headers for Supabase API calls
headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

def get_tokens_needing_current_prices(limit=50):
    """Get tokens that need current price updates"""
    # Get tokens that either have no current_price or need refresh
    # For first run, prioritize tokens that have entry prices (price_at_call)
    query = f"""
    {SUPABASE_URL}/rest/v1/crypto_calls?
    select=id,krom_id,contract_address,network,pool_address,ticker,current_price,price_updated_at,price_at_call&
    current_price.is.null&
    price_at_call.not.is.null&
    contract_address.not.is.null&
    network.not.is.null&
    order=created_at.asc&
    limit={limit}
    """.replace('\n', '').replace(' ', '')
    
    print(f"🔍 Query: {query}")
    response = requests.get(query, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Error fetching tokens: {response.status_code}")
        print(response.text)
        return []
    
    return response.json()

def fetch_current_price_via_edge_function(contract_address, network, pool_address=None):
    """Fetch current price using the crypto-price-single edge function"""
    payload = {
        "contractAddress": contract_address,
        "network": network,
        "callTimestamp": int(time.time()),  # Current timestamp
    }
    
    if pool_address:
        payload["poolAddress"] = pool_address
    
    try:
        response = requests.post(
            EDGE_FUNCTION_URL,
            headers={
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "current_price": data.get("currentPrice"),
                "market_cap": data.get("currentMarketCap"),
                "fdv": data.get("currentFDV"),
                "duration": data.get("duration")
            }
        else:
            return {
                "success": False,
                "error": f"Edge function error: {response.status_code}",
                "details": response.text[:200]
            }
            
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_token_current_price(token_id, current_price, current_market_cap=None, current_fdv=None):
    """Update token's current price in database"""
    update_data = {
        "current_price": current_price,
        "price_updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if current_market_cap is not None:
        update_data["current_market_cap"] = current_market_cap
    
    if current_fdv is not None:
        update_data["current_fdv"] = current_fdv
    
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
    print("🚀 Starting Current Price Batch Fetcher")
    print(f"📊 Supabase URL: {SUPABASE_URL}")
    print(f"🔧 Edge Function: {EDGE_FUNCTION_URL}")
    print()
    
    # Get initial counts
    count_response = requests.get(
        f"{SUPABASE_URL}/rest/v1/crypto_calls?select=count&current_price.not.is.null",
        headers={**headers, "Prefer": "count=exact"}
    )
    
    total_with_prices = 0
    if count_response.status_code == 200:
        total_with_prices = len(count_response.json())
    
    print(f"📈 Tokens with current prices: {total_with_prices}")
    
    batch_size = 10
    processed = 0
    successful = 0
    failed = 0
    
    while True:
        # Get next batch of tokens
        tokens = get_tokens_needing_current_prices(batch_size)
        
        if not tokens:
            print("\n✅ No more tokens need current price updates!")
            break
        
        print(f"\n📦 Processing batch of {len(tokens)} tokens...")
        
        for i, token in enumerate(tokens, 1):
            token_id = token['id']
            krom_id = token.get('krom_id', 'N/A')
            contract_address = token['contract_address']
            network = token['network']
            pool_address = token.get('pool_address')
            ticker = token.get('ticker', 'UNKNOWN')
            price_at_call = token.get('price_at_call')
            
            print(f"  [{i:2d}/{len(tokens)}] {ticker} ({krom_id}) - {network}...")
            
            # Fetch current price
            result = fetch_current_price_via_edge_function(
                contract_address, 
                network, 
                pool_address
            )
            
            if result["success"] and result["current_price"]:
                current_price = result["current_price"]
                market_cap = result.get("market_cap")
                fdv = result.get("fdv")
                duration = result.get("duration", "N/A")
                
                # Update database
                if update_token_current_price(token_id, current_price, market_cap, fdv):
                    # Calculate ROI if we have entry price
                    roi_updated, roi_percent = calculate_and_update_roi(
                        token_id, price_at_call, current_price
                    )
                    
                    roi_str = f" | ROI: {roi_percent:+.1f}%" if roi_updated else ""
                    print(f"      ✅ ${current_price:.8f}{roi_str} ({duration}s)")
                    successful += 1
                else:
                    print(f"      ❌ Database update failed")
                    failed += 1
            else:
                error = result.get("error", "Unknown error")
                print(f"      ❌ {error}")
                failed += 1
            
            processed += 1
            
            # Small delay to be nice to the API
            time.sleep(0.1)
        
        print(f"\n📊 Batch Complete: {successful} successful, {failed} failed")
        print(f"🔄 Total Processed: {processed}")
        
        # Brief pause between batches
        time.sleep(2)
    
    print(f"\n🎉 Current Price Fetching Complete!")
    print(f"✅ Successfully processed: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Total processed: {processed}")

if __name__ == "__main__":
    main()