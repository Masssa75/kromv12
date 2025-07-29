#!/usr/bin/env python3
"""
Batch price fetcher - processes all tokens without current prices
"""
import os
import requests
import time
import sys
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

def get_token_count():
    """Get total count of tokens needing prices"""
    count_query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.is.null&contract_address.not.is.null&network.not.is.null&price_at_call.gt.0&limit=1"
    resp = requests.get(count_query, headers={**headers, "Prefer": "count=exact"})
    
    if 'content-range' in resp.headers:
        return int(resp.headers['content-range'].split('/')[-1])
    return 0

def process_batch(offset=0, limit=50):
    """Process a batch of tokens"""
    query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id,ticker,contract_address,network,price_at_call&current_price.is.null&contract_address.not.is.null&network.not.is.null&price_at_call.gt.0&order=created_at.asc&limit={limit}&offset={offset}"
    
    resp = requests.get(query, headers=headers)
    if resp.status_code != 200:
        return [], 0, 0
    
    tokens = resp.json()
    success_count = 0
    
    for token in tokens:
        # Try DexScreener first
        price = fetch_price_dexscreener(token['contract_address'])
        source = "DexScreener"
        
        # If not found, try GeckoTerminal
        if price is None:
            price = fetch_price_geckoterminal(token['contract_address'], token['network'])
            source = "GeckoTerminal"
        
        if price:
            if update_token_price(token['id'], price):
                success_count += 1
        
        time.sleep(0.3)  # Rate limiting
    
    return tokens, len(tokens), success_count

def main():
    print("🚀 Batch Price Fetcher")
    print("=" * 50)
    
    print("Getting token count...")
    total_count = get_token_count()
    print(f"📊 Total tokens needing prices: {total_count}\n")
    
    if total_count == 0:
        print("✅ All tokens have current prices!")
        return
    
    processed = 0
    total_success = 0
    batch_size = 50
    
    print(f"Processing in batches of {batch_size}...\n")
    
    try:
        while processed < total_count:
            batch_start = time.time()
            
            tokens, batch_processed, batch_success = process_batch(processed, batch_size)
            
            if batch_processed == 0:
                break
            
            processed += batch_processed
            total_success += batch_success
            
            batch_time = time.time() - batch_start
            success_rate = (batch_success / batch_processed * 100) if batch_processed > 0 else 0
            
            print(f"Batch {processed // batch_size}: {batch_success}/{batch_processed} successful ({success_rate:.1f}%) - {batch_time:.1f}s")
            print(f"Overall progress: {processed}/{total_count} ({processed/total_count*100:.1f}%)")
            print(f"Overall success: {total_success}/{processed} ({total_success/processed*100:.1f}%)\n")
            
            # Show current stats
            if processed % 200 == 0:
                # Check actual count in database
                count_query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.gt.0&limit=1"
                resp = requests.get(count_query, headers={**headers, "Prefer": "count=exact"})
                if 'content-range' in resp.headers:
                    db_count = int(resp.headers['content-range'].split('/')[-1])
                    print(f"📈 Database check: {db_count} tokens have current prices\n")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    
    print(f"\n✅ Final results:")
    print(f"   Processed: {processed} tokens")
    print(f"   Successfully updated: {total_success} tokens")
    print(f"   Success rate: {total_success/processed*100:.1f}%")

if __name__ == "__main__":
    main()