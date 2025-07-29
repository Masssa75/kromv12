#!/usr/bin/env python3
"""
Batch Current Price Fetcher using DexScreener API

This script fetches current prices for all tokens in the database using the 
DexScreener API instead of GeckoTerminal to avoid rate limits.

Usage:
    python3 fetch-current-prices-dexscreener.py

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

# DexScreener API base URL
DEXSCREENER_API_BASE = "https://api.dexscreener.com/latest/dex"

# Headers for Supabase API calls
headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

def get_tokens_needing_current_prices(limit=10):
    """Get tokens that need current price updates"""
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
    
    print(f"🔍 Fetching next {limit} tokens needing prices...")
    response = requests.get(query, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Error fetching tokens: {response.status_code}")
        print(response.text)
        return []
    
    return response.json()

def fetch_price_from_dexscreener(contract_address, network):
    """Fetch current price from DexScreener API"""
    # Network mapping for DexScreener
    network_map = {
        'ethereum': 'ethereum',
        'solana': 'solana',
        'bsc': 'bsc',
        'polygon': 'polygon',
        'arbitrum': 'arbitrum',
        'base': 'base'
    }
    
    mapped_network = network_map.get(network, network)
    
    # DexScreener endpoint for token info
    url = f"{DEXSCREENER_API_BASE}/tokens/{contract_address}"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Find pairs for the correct network
            pairs = data.get('pairs', [])
            if not pairs:
                return {"success": False, "error": "No pairs found"}
            
            # Filter pairs by network
            network_pairs = [p for p in pairs if p.get('chainId', '').lower() == mapped_network.lower()]
            
            if not network_pairs:
                # If no exact network match, try all pairs
                network_pairs = pairs
            
            # Sort by liquidity (USD) and get the best pair
            network_pairs.sort(key=lambda x: float(x.get('liquidity', {}).get('usd', 0)), reverse=True)
            best_pair = network_pairs[0]
            
            # Extract price and market data
            price_usd = float(best_pair.get('priceUsd', 0))
            liquidity_usd = float(best_pair.get('liquidity', {}).get('usd', 0))
            volume_24h = float(best_pair.get('volume', {}).get('h24', 0))
            
            # Get FDV if available
            fdv = float(best_pair.get('fdv', 0)) if best_pair.get('fdv') else None
            
            return {
                "success": True,
                "current_price": price_usd,
                "liquidity": liquidity_usd,
                "volume_24h": volume_24h,
                "fdv": fdv,
                "dex_name": best_pair.get('dexId', 'Unknown'),
                "pair_address": best_pair.get('pairAddress')
            }
        else:
            return {
                "success": False,
                "error": f"DexScreener API error: {response.status_code}"
            }
            
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_token_current_price(token_id, current_price, current_fdv=None):
    """Update token's current price in database"""
    update_data = {
        "current_price": current_price,
        "price_updated_at": datetime.now(timezone.utc).isoformat()
    }
    
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
    print("🚀 Starting Current Price Batch Fetcher (DexScreener API)")
    print(f"📊 Using DexScreener API to avoid GeckoTerminal rate limits")
    print()
    
    # Get initial counts
    count_response = requests.get(
        f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.not.is.null&limit=5000",
        headers=headers
    )
    
    total_with_prices = 0
    if count_response.status_code == 200:
        total_with_prices = len(count_response.json())
    
    print(f"📈 Tokens with current prices: {total_with_prices}")
    
    batch_size = 10  # Small batch to be nice to DexScreener
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
            ticker = token.get('ticker', 'UNKNOWN')
            price_at_call = token.get('price_at_call')
            
            print(f"  [{i:2d}/{len(tokens)}] {ticker} ({krom_id}) - {network}...")
            
            # Fetch current price from DexScreener
            result = fetch_price_from_dexscreener(contract_address, network)
            
            if result["success"] and result["current_price"]:
                current_price = result["current_price"]
                fdv = result.get("fdv")
                dex_name = result.get("dex_name", "Unknown")
                liquidity = result.get("liquidity", 0)
                
                # Update database
                if update_token_current_price(token_id, current_price, fdv):
                    # Calculate ROI if we have entry price
                    roi_updated, roi_percent = calculate_and_update_roi(
                        token_id, price_at_call, current_price
                    )
                    
                    roi_str = f" | ROI: {roi_percent:+.1f}%" if roi_updated else ""
                    print(f"      ✅ ${current_price:.8f}{roi_str} (via {dex_name}, liq: ${liquidity:,.0f})")
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
            time.sleep(0.5)  # DexScreener is generally more lenient than GeckoTerminal
        
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