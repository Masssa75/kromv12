#!/usr/bin/env python3
"""
Smart Current Price Fetcher using DexScreener API

This version properly handles records that have timestamps but null prices
(from the clear-prices functionality).
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

def get_tokens_needing_prices(limit=10):
    """Get tokens that actually need current prices, ignoring timestamp-only records"""
    # Query for tokens that:
    # 1. Have an entry price (price_at_call not null)
    # 2. Have contract and network info
    # 3. Either:
    #    - Have no current_price at all, OR
    #    - Have current_price but it's null (from clear-prices)
    # 4. Order by oldest first
    
    query = f"""
    {SUPABASE_URL}/rest/v1/crypto_calls?
    select=id,ticker,contract_address,network,price_at_call,current_price,price_updated_at,krom_id&
    price_at_call.not.is.null&
    contract_address.not.is.null&
    network.not.is.null&
    or=(current_price.is.null,and(price_updated_at.not.is.null,current_price.is.null))&
    order=created_at.asc&
    limit={limit}
    """.replace('\n', '').replace(' ', '')
    
    response = requests.get(query, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Error fetching tokens: {response.status_code}")
        print(f"Response: {response.text}")
        return []
    
    tokens = response.json()
    
    # Filter out any that somehow have actual prices
    return [t for t in tokens if t.get('current_price') is None]

def fetch_from_dexscreener(contract_address, network):
    """Fetch current price from DexScreener API"""
    # Network mapping
    network_map = {
        'ethereum': 'ethereum',
        'solana': 'solana',
        'bsc': 'bsc',
        'polygon': 'polygon',
        'arbitrum': 'arbitrum',
        'base': 'base'
    }
    
    mapped_network = network_map.get(network, network)
    url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            pairs = data.get('pairs', [])
            
            if not pairs:
                return {"success": False, "error": "No pairs found (token likely dead)"}
            
            # Filter by network and sort by liquidity
            network_pairs = [p for p in pairs if p.get('chainId', '').lower() == mapped_network.lower()]
            if not network_pairs:
                network_pairs = pairs  # Fallback to all pairs
            
            network_pairs.sort(key=lambda x: float(x.get('liquidity', {}).get('usd', 0)), reverse=True)
            best_pair = network_pairs[0]
            
            price_usd = float(best_pair.get('priceUsd', 0))
            
            if price_usd > 0:
                return {
                    "success": True,
                    "current_price": price_usd,
                    "liquidity": float(best_pair.get('liquidity', {}).get('usd', 0)),
                    "dex_name": best_pair.get('dexId', 'Unknown')
                }
            else:
                return {"success": False, "error": "No valid price found"}
        else:
            return {"success": False, "error": f"API error: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_token_price(token_id, current_price):
    """Update token's current price and timestamp"""
    update_data = {
        "current_price": current_price,
        "price_updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/crypto_calls?id=eq.{token_id}",
        headers=headers,
        json=update_data
    )
    
    return response.status_code == 204

def calculate_roi(price_at_call, current_price):
    """Calculate ROI percentage"""
    if price_at_call and current_price and price_at_call > 0:
        return ((current_price - price_at_call) / price_at_call) * 100
    return None

def update_roi(token_id, roi_percent):
    """Update ROI in database"""
    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/crypto_calls?id=eq.{token_id}",
        headers=headers,
        json={"roi_percent": roi_percent}
    )
    return response.status_code == 204

def main():
    print("🚀 Smart Current Price Fetcher (DexScreener)")
    print("📊 Handles cleared prices properly\n")
    
    # Get initial statistics
    stats_query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.not.is.null&price_updated_at.not.is.null"
    stats_resp = requests.get(stats_query, headers={**headers, "Prefer": "count=exact"}, params={"limit": 0})
    
    if 'content-range' in stats_resp.headers:
        total_with_timestamps = stats_resp.headers['content-range'].split('/')[-1]
        print(f"📊 Records with timestamps: {total_with_timestamps}")
    
    batch_size = 25
    total_processed = 0
    successful = 0
    failed = 0
    
    while True:
        # Get next batch
        tokens = get_tokens_needing_prices(batch_size)
        
        if not tokens:
            print("\n✅ No more tokens need current prices!")
            break
        
        print(f"\n📦 Processing batch of {len(tokens)} tokens...")
        
        for i, token in enumerate(tokens, 1):
            token_id = token['id']
            ticker = token.get('ticker', 'UNKNOWN')
            contract = token['contract_address']
            network = token['network']
            price_at_call = token.get('price_at_call', 0)
            krom_id = token.get('krom_id', 'N/A')
            has_timestamp = token.get('price_updated_at') is not None
            
            status = " (cleared)" if has_timestamp else ""
            print(f"  [{i:2d}/{len(tokens)}] {ticker} ({krom_id}) - {network}{status}...")
            
            # Fetch current price
            result = fetch_from_dexscreener(contract, network)
            
            if result["success"] and result["current_price"]:
                current_price = result["current_price"]
                liquidity = result.get("liquidity", 0)
                dex = result.get("dex_name", "Unknown")
                
                # Update price
                if update_token_price(token_id, current_price):
                    # Calculate and update ROI
                    roi = calculate_roi(price_at_call, current_price)
                    if roi is not None:
                        update_roi(token_id, roi)
                        roi_str = f" | ROI: {roi:+.1f}%"
                    else:
                        roi_str = ""
                    
                    print(f"      ✅ ${current_price:.8f}{roi_str} (via {dex}, liq: ${liquidity:,.0f})")
                    successful += 1
                else:
                    print(f"      ❌ Database update failed")
                    failed += 1
            else:
                error = result.get("error", "Unknown error")
                print(f"      ❌ {error}")
                failed += 1
            
            total_processed += 1
            
            # Small delay between requests
            time.sleep(0.5)
        
        print(f"\n📊 Batch Complete: {successful} successful, {failed} failed")
        print(f"🔄 Total Processed: {total_processed}")
        
        # Brief pause between batches
        time.sleep(2)
    
    print(f"\n🎉 Completed!")
    print(f"✅ Successfully updated: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Total processed: {total_processed}")

if __name__ == "__main__":
    main()