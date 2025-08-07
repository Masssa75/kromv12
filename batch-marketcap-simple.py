#!/usr/bin/env python3
"""
Simple Market Cap Updater - DexScreener API
============================================
Efficiently updates market cap data using DexScreener batch API.
"""

import os
import warnings
warnings.filterwarnings("ignore")

import requests
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

def process_batch(tokens):
    """Process a batch of tokens"""
    # Build comma-separated list of addresses
    addresses = ','.join([t['contract_address'] for t in tokens if t['contract_address']])
    
    if not addresses:
        return 0
    
    print(f"  Fetching {len(tokens)} tokens from DexScreener...")
    
    # Single API call for all tokens
    url = f"https://api.dexscreener.com/latest/dex/tokens/{addresses}"
    response = requests.get(url, timeout=30)
    
    if response.status_code != 200:
        print(f"  ❌ API error: {response.status_code}")
        return 0
    
    data = response.json()
    
    # Map results by contract address
    results = {}
    for pair in data.get('pairs', []):
        addr = pair.get('baseToken', {}).get('address', '').lower()
        if addr and (addr not in results or 
                    float(pair.get('liquidity', {}).get('usd', 0) or 0) > 
                    float(results.get(addr, {}).get('liquidity', {}).get('usd', 0) or 0)):
            results[addr] = pair
    
    # Update each token
    success = 0
    for token in tokens:
        if not token['contract_address']:
            continue
        
        pair = results.get(token['contract_address'].lower())
        if not pair:
            continue
        
        market_cap = pair.get('marketCap')
        fdv = pair.get('fdv')
        price = float(pair.get('priceUsd', 0))
        
        if market_cap and price > 0:
            update_data = {
                'current_market_cap': market_cap,
                'circulating_supply': market_cap / price,
                'supply_updated_at': datetime.utcnow().isoformat()
            }
            
            if fdv:
                update_data['total_supply'] = fdv / price
            
            try:
                supabase.table('crypto_calls').update(update_data).eq('id', token['id']).execute()
                print(f"    ✅ {token['ticker']}: ${market_cap:,.0f}")
                success += 1
            except Exception as e:
                print(f"    ❌ {token['ticker']}: {e}")
    
    return success

def main():
    print("=" * 60)
    print("DexScreener Market Cap Updater")
    print("=" * 60)
    
    # Get all tokens with price but no market cap
    print("\nFetching tokens from database...")
    
    # Get the LATEST 100 tokens (ordered by created_at desc)
    result = supabase.table('crypto_calls').select(
        'id,ticker,contract_address,current_price,current_market_cap,created_at'
    ).not_.is_('current_price', 'null').order('created_at', desc=True).limit(100).execute()
    
    # Filter out ones that already have market cap
    tokens = [t for t in result.data if not t.get('current_market_cap')]
    
    print(f"Getting latest 100 tokens, found {len(result.data)} with prices")
    print(f"After filtering out existing market caps: {len(tokens)} tokens to process")
    
    print(f"Found {len(tokens)} tokens needing market cap")
    
    if not tokens:
        print("No tokens to process")
        return
    
    # Process in batches of 30
    batch_size = 30
    total_success = 0
    
    for i in range(0, len(tokens), batch_size):
        batch = tokens[i:i+batch_size]
        print(f"\n[Batch {i//batch_size + 1}] Processing {len(batch)} tokens...")
        
        success = process_batch(batch)
        total_success += success
        
        print(f"  Batch complete: {success}/{len(batch)} updated")
    
    print("\n" + "=" * 60)
    print(f"Complete! Updated {total_success}/{len(tokens)} tokens")
    print("=" * 60)

if __name__ == "__main__":
    main()