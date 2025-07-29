#!/usr/bin/env python3
"""
Simple batch price fetcher
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
    """Try to fetch price from DexScreener or GeckoTerminal"""
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

def main():
    print("🚀 Simple Batch Price Fetcher")
    print("=" * 50)
    
    # Get tokens needing prices - simple query
    offset = 0
    batch_size = 25
    total_processed = 0
    total_success = 0
    
    while True:
        print(f"\n📦 Fetching batch at offset {offset}...")
        
        # Simple query without complex filters
        query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id,ticker,contract_address,network,price_at_call,current_price&offset={offset}&limit={batch_size}&order=created_at.asc"
        
        resp = requests.get(query, headers=headers)
        if resp.status_code != 200:
            print(f"❌ Query failed: {resp.status_code}")
            break
        
        tokens = resp.json()
        if not tokens:
            print("✅ No more tokens to process")
            break
        
        batch_success = 0
        
        for i, token in enumerate(tokens):
            # Skip if no contract address or already has price
            if not token.get('contract_address') or token.get('current_price') is not None:
                continue
            
            # Skip if no entry price
            if not token.get('price_at_call') or token['price_at_call'] <= 0:
                continue
            
            total_processed += 1
            
            print(f"  [{i+1}/{len(tokens)}] {token['ticker']} - ", end='')
            
            price, source = fetch_price(token['contract_address'], token['network'])
            
            if price:
                # Update in database
                update_url = f"{SUPABASE_URL}/rest/v1/crypto_calls?id=eq.{token['id']}"
                update_data = {
                    "current_price": price,
                    "price_updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                update_resp = requests.patch(update_url, json=update_data, headers=headers)
                
                if update_resp.status_code in [200, 204]:
                    batch_success += 1
                    total_success += 1
                    roi = ((price - token['price_at_call']) / token['price_at_call'] * 100)
                    print(f"✅ ${price:.8f} | ROI: {roi:+.1f}% (via {source})")
                else:
                    print(f"❌ Update failed")
            else:
                print(f"❌ No price found")
            
            time.sleep(0.2)  # Rate limiting
        
        print(f"\nBatch summary: {batch_success} successful updates")
        print(f"Total progress: {total_success}/{total_processed} ({total_success/total_processed*100:.1f}% success rate)")
        
        offset += batch_size
        
        # Safety limit
        if offset >= 500:
            print("\n⚠️  Reached 500 token limit for this run")
            break
    
    print(f"\n✅ Final results:")
    print(f"   Processed: {total_processed} tokens")
    print(f"   Successfully updated: {total_success} tokens")
    if total_processed > 0:
        print(f"   Success rate: {total_success/total_processed*100:.1f}%")

if __name__ == "__main__":
    main()