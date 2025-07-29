#!/usr/bin/env python3
"""
Final Current Price Fetcher - Simple and Robust
Fetches current prices for ALL tokens regardless of database state
Updates price and timestamp no matter what's currently stored
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

# Network mapping - CRITICAL for success
NETWORK_MAP = {
    'ethereum': 'eth',
    'solana': 'solana',
    'bsc': 'bsc',
    'polygon': 'polygon',
    'arbitrum': 'arbitrum',
    'base': 'base'
}

def get_tokens_to_update(limit=50):
    """Get tokens that have contract address and network - that's all we need"""
    query = f"""
    {SUPABASE_URL}/rest/v1/crypto_calls?
    select=id,ticker,contract_address,network,price_at_call,current_price,krom_id&
    contract_address.not.is.null&
    network.not.is.null&
    order=price_updated_at.asc.nullsfirst,created_at.asc&
    limit={limit}
    """.replace('\n', '').replace(' ', '')
    
    response = requests.get(query, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Error fetching tokens: {response.status_code}")
        print(f"Response: {response.text}")
        return []
    
    return response.json()

def fetch_from_geckoterminal(contract_address, network):
    """Fetch current price from GeckoTerminal API"""
    # Map network name
    mapped_network = NETWORK_MAP.get(network, network)
    
    # GeckoTerminal token info endpoint
    url = f"https://api.geckoterminal.com/api/v2/networks/{mapped_network}/tokens/{contract_address}"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            token_data = data.get('data', {})
            attributes = token_data.get('attributes', {})
            
            price_usd = attributes.get('price_usd')
            
            if price_usd:
                return {
                    "success": True,
                    "current_price": float(price_usd),
                    "market_cap": float(attributes.get('market_cap_usd', 0)),
                    "fdv": float(attributes.get('fdv_usd', 0)),
                    "volume_24h": float(attributes.get('volume_usd', {}).get('h24', 0))
                }
            else:
                return {"success": False, "error": "No price data available"}
        elif response.status_code == 404:
            return {"success": False, "error": "Token not found (likely dead)"}
        else:
            return {"success": False, "error": f"API error: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def fetch_from_dexscreener(contract_address, network):
    """Fallback to DexScreener API if GeckoTerminal fails"""
    url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            pairs = data.get('pairs', [])
            
            if not pairs:
                return {"success": False, "error": "No pairs found"}
            
            # Map network for comparison
            mapped_network = NETWORK_MAP.get(network, network)
            
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
                    "market_cap": float(best_pair.get('marketCap', 0)),
                    "fdv": float(best_pair.get('fdv', 0)),
                    "volume_24h": float(best_pair.get('volume', {}).get('h24', 0)),
                    "dex_name": best_pair.get('dexId', 'Unknown')
                }
            else:
                return {"success": False, "error": "No valid price found"}
        else:
            return {"success": False, "error": f"API error: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_token_price(token_id, price_data):
    """Update token's current price and related fields"""
    current_price = price_data.get('current_price', 0)
    
    update_data = {
        "current_price": current_price,
        "price_updated_at": datetime.now(timezone.utc).isoformat(),
        "current_market_cap": price_data.get('market_cap', None),
        "current_fdv": price_data.get('fdv', None)
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
    print("🚀 Final Current Price Fetcher")
    print("📊 Updates all tokens regardless of current database state\n")
    
    # Get initial statistics
    total_query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&contract_address.not.is.null&network.not.is.null"
    total_resp = requests.get(total_query, headers={**headers, "Prefer": "count=exact"}, params={"limit": 0})
    total_eligible = int(total_resp.headers.get('content-range', '/0').split('/')[-1])
    
    print(f"📊 Total tokens with contract & network: {total_eligible}")
    
    batch_size = 50
    total_processed = 0
    successful = 0
    failed = 0
    dead_tokens = 0
    
    while True:
        # Get next batch
        tokens = get_tokens_to_update(batch_size)
        
        if not tokens:
            print("\n✅ No more tokens to process!")
            break
        
        print(f"\n📦 Processing batch of {len(tokens)} tokens...")
        
        for i, token in enumerate(tokens, 1):
            token_id = token['id']
            ticker = token.get('ticker', 'UNKNOWN')
            contract = token['contract_address']
            network = token['network']
            price_at_call = token.get('price_at_call', 0)
            current_price_old = token.get('current_price')
            krom_id = token.get('krom_id', 'N/A')
            
            print(f"  [{i:2d}/{len(tokens)}] {ticker} ({krom_id}) - {network}...", end='', flush=True)
            
            # Try GeckoTerminal first
            result = fetch_from_geckoterminal(contract, network)
            
            # If GeckoTerminal fails, try DexScreener
            if not result["success"] and "not found" not in result.get("error", ""):
                result = fetch_from_dexscreener(contract, network)
                if result["success"]:
                    result["source"] = "DexScreener"
            else:
                result["source"] = "GeckoTerminal"
            
            if result["success"] and result["current_price"]:
                # Update price
                if update_token_price(token_id, result):
                    # Calculate and update ROI if we have entry price
                    roi = calculate_roi(price_at_call, result["current_price"])
                    if roi is not None:
                        update_roi(token_id, roi)
                        roi_str = f" | ROI: {roi:+.1f}%"
                    else:
                        roi_str = ""
                    
                    source = result.get("source", "Unknown")
                    print(f" ✅ ${result['current_price']:.8f}{roi_str} (via {source})")
                    successful += 1
                else:
                    print(f" ❌ Database update failed")
                    failed += 1
            else:
                error = result.get("error", "Unknown error")
                if "not found" in error or "dead" in error:
                    print(f" 💀 Dead token")
                    dead_tokens += 1
                else:
                    print(f" ❌ {error}")
                failed += 1
            
            total_processed += 1
            
            # Small delay between requests
            time.sleep(0.2)
        
        print(f"\n📊 Batch Complete: {successful} successful, {failed} failed ({dead_tokens} dead)")
        print(f"🔄 Total Processed: {total_processed}/{total_eligible} ({(total_processed/total_eligible*100):.1f}%)")
        
        # Brief pause between batches
        time.sleep(1)
    
    print(f"\n🎉 Completed!")
    print(f"✅ Successfully updated: {successful}")
    print(f"💀 Dead tokens: {dead_tokens}")
    print(f"❌ Other failures: {failed - dead_tokens}")
    print(f"📈 Total processed: {total_processed}")

if __name__ == "__main__":
    main()