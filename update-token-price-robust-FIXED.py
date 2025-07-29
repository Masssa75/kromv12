#!/usr/bin/env python3
"""
Robust token price updater - handles one token at a time with proper fallback
Based on manual testing findings: DexScreener first, then GeckoTerminal pools
FIXED VERSION: Proper Supabase query syntax and timestamp orphan avoidance
"""
import os
import sys
import requests
import time
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

# Network mapping for GeckoTerminal API
NETWORK_MAP = {
    'ethereum': 'eth',
    'solana': 'solana',
    'bsc': 'bsc',
    'polygon': 'polygon',
    'arbitrum': 'arbitrum',
    'base': 'base'
}

def get_next_token():
    """Get the next token that needs a price update - FIXED QUERY SYNTAX"""
    query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id,ticker,contract_address,network,price_at_call,current_price&contract_address=not.is.null&network=not.is.null&price_at_call=gt.0&current_price=is.null&price_updated_at=is.null&order=id.asc&limit=1"
    
    resp = requests.get(query, headers=headers)
    if resp.status_code != 200:
        print(f"❌ Query failed: {resp.status_code}")
        return None
    
    tokens = resp.json()
    if not tokens:
        print("✅ No more tokens to process!")
        return None
    
    return tokens[0]

def fetch_price_dexscreener(contract_address):
    """Try to fetch price from DexScreener (fast, no rate limits)"""
    try:
        resp = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}")
        if resp.status_code == 200:
            data = resp.json()
            if data.get('pairs') and len(data['pairs']) > 0:
                price = float(data['pairs'][0]['priceUsd'])
                return price, "DexScreener"
    except Exception as e:
        print(f"   DexScreener error: {e}")
    
    return None, None

def fetch_price_geckoterminal(contract_address, network):
    """Try to fetch price from GeckoTerminal pools (fallback method)"""
    try:
        api_network = NETWORK_MAP.get(network, network)
        resp = requests.get(f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{contract_address}/pools")
        
        if resp.status_code == 429:
            print(f"   GeckoTerminal: Rate limited")
            return None, None
        
        if resp.status_code == 200:
            data = resp.json()
            pools = data.get('data', [])
            
            if pools:
                # Find the pool with highest price (most liquid usually)
                best_price = 0
                for pool in pools:
                    pool_price_str = pool['attributes'].get('token_price_usd')
                    if pool_price_str:
                        pool_price = float(pool_price_str)
                        if pool_price > best_price:
                            best_price = pool_price
                
                if best_price > 0:
                    return best_price, "GeckoTerminal"
    except Exception as e:
        print(f"   GeckoTerminal error: {e}")
    
    return None, None

def update_token_price(token_id, price):
    """Update token price in database"""
    update_url = f"{SUPABASE_URL}/rest/v1/crypto_calls?id=eq.{token_id}"
    update_data = {
        "current_price": price,
        "price_updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    resp = requests.patch(update_url, json=update_data, headers=headers)
    return resp.status_code in [200, 204]

def main():
    print("🔄 Robust Token Price Updater (FIXED)")
    print("=" * 50)
    
    # Get next token
    token = get_next_token()
    if not token:
        return
    
    print(f"\n📊 Processing: {token['ticker']} ({token['network']})")
    print(f"   Contract: {token['contract_address'][:20]}...")
    print(f"   Entry price: ${token['price_at_call']:.8f}")
    
    # Try DexScreener first (fast, no rate limits)
    print(f"   🔍 Trying DexScreener...")
    price, source = fetch_price_dexscreener(token['contract_address'])
    
    # If DexScreener fails, try GeckoTerminal pools
    if price is None:
        print(f"   🔍 DexScreener failed, trying GeckoTerminal pools...")
        price, source = fetch_price_geckoterminal(token['contract_address'], token['network'])
    
    if price:
        # Calculate ROI
        roi = ((price - token['price_at_call']) / token['price_at_call'] * 100)
        roi_symbol = "📈" if roi > 0 else "📉"
        
        print(f"   💰 Found price: ${price:.8f} (via {source})")
        print(f"   {roi_symbol} ROI: {roi:+.1f}%")
        
        # Update database
        if update_token_price(token['id'], price):
            print(f"   ✅ Updated successfully")
            
            # Print summary for easy tracking
            print(f"\n📋 SUMMARY:")
            print(f"   Token: {token['ticker']}")
            print(f"   CA: {token['contract_address']}")
            print(f"   Entry → Current: ${token['price_at_call']:.8f} → ${price:.8f}")
            print(f"   ROI: {roi:+.1f}%")
            print(f"   Source: {source}")
        else:
            print(f"   ❌ Database update failed")
    else:
        print(f"   ❌ No price found on any platform")
        print(f"   📝 CA for manual check: {token['contract_address']}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Stopped by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")