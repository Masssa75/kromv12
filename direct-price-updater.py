#!/usr/bin/env python3
"""
Direct price updater - simple and straightforward
"""
import os
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

# Network mapping
NETWORK_MAP = {
    'ethereum': 'eth',
    'solana': 'solana',
    'bsc': 'bsc',
    'polygon': 'polygon',
    'arbitrum': 'arbitrum',
    'base': 'base'
}

def fetch_price(contract_address, network):
    """Fetch current price from DexScreener or GeckoTerminal"""
    # Try DexScreener first
    try:
        resp = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}")
        data = resp.json()
        if data.get('pairs') and len(data['pairs']) > 0:
            return float(data['pairs'][0]['priceUsd']), "DexScreener"
    except:
        pass
    
    # Try GeckoTerminal
    try:
        api_network = NETWORK_MAP.get(network, network)
        resp = requests.get(f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{contract_address}")
        data = resp.json()
        if data.get('data') and data['data'].get('attributes'):
            price = data['data']['attributes'].get('price_usd')
            if price:
                return float(price), "GeckoTerminal"
    except:
        pass
    
    return None, None

def update_price(token_id, price):
    """Update token price in database"""
    update_url = f"{SUPABASE_URL}/rest/v1/crypto_calls?id=eq.{token_id}"
    update_data = {
        "current_price": price,
        "price_updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    resp = requests.patch(update_url, json=update_data, headers=headers)
    return resp.status_code in [200, 204]

def main():
    print("🚀 Direct Price Updater")
    print("=" * 50)
    
    # Get one token at a time
    while True:
        # Get ONE token that needs a price
        query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id,ticker,contract_address,network,price_at_call,current_price&current_price.is.null&contract_address.not.is.null&network.not.is.null&price_at_call.gt.0&order=created_at.asc&limit=1"
        
        resp = requests.get(query, headers=headers)
        if resp.status_code != 200:
            print(f"❌ Query failed: {resp.status_code}")
            break
        
        tokens = resp.json()
        if not tokens:
            print("✅ No more tokens to process!")
            break
        
        token = tokens[0]
        print(f"\n📊 Processing: {token['ticker']} ({token['network']})")
        print(f"   Contract: {token['contract_address'][:20]}...")
        print(f"   Entry price: ${token['price_at_call']:.8f}")
        
        # Fetch price
        price, source = fetch_price(token['contract_address'], token['network'])
        
        if price:
            # Calculate ROI
            roi = ((price - token['price_at_call']) / token['price_at_call'] * 100)
            print(f"   Current price: ${price:.8f} (via {source})")
            print(f"   ROI: {roi:+.1f}%")
            
            # Update database
            if update_price(token['id'], price):
                print("   ✅ Updated successfully")
            else:
                print("   ❌ Update failed")
        else:
            print("   ❌ No price found")
        
        # Rate limiting
        time.sleep(0.5)

if __name__ == "__main__":
    main()