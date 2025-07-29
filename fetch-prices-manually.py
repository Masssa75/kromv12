#!/usr/bin/env python3
"""
Manual price fetcher - simple and direct
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

def fetch_price_dexscreener(contract_address):
    """Fetch current price from DexScreener"""
    try:
        resp = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}")
        data = resp.json()
        
        if data.get('pairs') and len(data['pairs']) > 0:
            return float(data['pairs'][0]['priceUsd'])
    except:
        pass
    return None

def fetch_price_geckoterminal(contract_address, network):
    """Fetch current price from GeckoTerminal"""
    try:
        api_network = NETWORK_MAP.get(network, network)
        resp = requests.get(f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{contract_address}")
        data = resp.json()
        
        if data.get('data') and data['data'].get('attributes'):
            price = data['data']['attributes'].get('price_usd')
            if price:
                return float(price)
    except:
        pass
    return None

def update_token_price(token_id, price):
    """Update token price in database"""
    update_url = f"{SUPABASE_URL}/rest/v1/crypto_calls?id=eq.{token_id}"
    update_data = {
        "current_price": price,
        "price_updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    resp = requests.patch(update_url, json=update_data, headers=headers)
    return resp.status_code == 200 or resp.status_code == 204

def main():
    print("🚀 Manual Price Fetcher")
    print("=" * 50)
    
    # Get tokens without current prices
    query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id,ticker,contract_address,network,price_at_call&current_price.is.null&contract_address.not.is.null&network.not.is.null&price_at_call.gt.0&order=created_at.asc&limit=50"
    
    resp = requests.get(query, headers=headers)
    tokens = resp.json()
    
    print(f"📊 Found {len(tokens)} tokens needing prices\n")
    
    success_count = 0
    
    for i, token in enumerate(tokens, 1):
        print(f"[{i}/{len(tokens)}] {token['ticker']} ({token['network']})")
        print(f"   Contract: {token['contract_address'][:20]}...")
        
        # Try DexScreener first
        price = fetch_price_dexscreener(token['contract_address'])
        source = "DexScreener"
        
        # If not found, try GeckoTerminal
        if price is None:
            price = fetch_price_geckoterminal(token['contract_address'], token['network'])
            source = "GeckoTerminal"
        
        if price:
            # Calculate ROI
            roi = ((price - token['price_at_call']) / token['price_at_call'] * 100) if token['price_at_call'] > 0 else 0
            print(f"   ✅ Price: ${price:.8f} | ROI: {roi:+.1f}% (via {source})")
            
            # Update database
            if update_token_price(token['id'], price):
                success_count += 1
                print("   ✅ Updated in database")
            else:
                print("   ❌ Failed to update database")
        else:
            print("   ❌ No price found on any platform")
        
        print()
        time.sleep(0.5)  # Rate limiting
    
    print(f"\n✅ Successfully updated {success_count}/{len(tokens)} tokens")

if __name__ == "__main__":
    main()