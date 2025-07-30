import os
from supabase import create_client, Client
from dotenv import load_dotenv
import requests
import time
from datetime import datetime
import concurrent.futures
import threading

load_dotenv()

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=== COMPREHENSIVE PRICE REFRESH ===")
print("This will refresh ALL token prices to ensure accuracy\n")

# Get count of tokens to update
count_result = supabase.table('crypto_calls').select('count', count='exact').not_.is_('contract_address', 'null').execute()
total_tokens = count_result.count

print(f"Total tokens to refresh: {total_tokens:,}\n")

if input("This will take ~30-60 minutes. Continue? (y/n): ").lower() != 'y':
    print("Aborted.")
    exit()

# Thread-safe counters
processed = 0
updated = 0
errors = 0
lock = threading.Lock()

start_time = datetime.now()

network_map = {
    'ethereum': 'eth',
    'solana': 'solana',
    'bsc': 'bsc',
    'polygon': 'polygon',
    'arbitrum': 'arbitrum',
    'base': 'base'
}

def fetch_and_update_price(token):
    global processed, updated, errors
    
    try:
        actual_price = None
        source = None
        
        # Try DexScreener first (no rate limit)
        try:
            response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('pairs') and len(data['pairs']) > 0:
                    actual_price = float(data['pairs'][0]['priceUsd'])
                    source = 'DexScreener'
        except:
            pass
        
        # If not found, try GeckoTerminal
        if actual_price is None and token['network']:
            try:
                api_network = network_map.get(token['network'], token['network'])
                response = requests.get(
                    f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{token['contract_address']}/pools",
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data') and len(data['data']) > 0:
                        pool_price = data['data'][0]['attributes'].get('token_price_usd')
                        if pool_price:
                            actual_price = float(pool_price)
                            source = 'GeckoTerminal'
                time.sleep(0.2)  # Rate limit for GeckoTerminal
            except:
                pass
        
        # Update if we got a price
        if actual_price and actual_price > 0:
            # Calculate ROI
            roi = None
            if token['price_at_call'] and token['price_at_call'] > 0:
                roi = ((actual_price - token['price_at_call']) / token['price_at_call']) * 100
            
            # Update database
            update_data = {
                'current_price': actual_price,
                'price_updated_at': datetime.utcnow().isoformat()
            }
            if roi is not None:
                update_data['roi_percent'] = roi
            
            supabase.table('crypto_calls').update(update_data).eq('krom_id', token['krom_id']).execute()
            
            with lock:
                updated += 1
        else:
            with lock:
                errors += 1
                
    except Exception as e:
        with lock:
            errors += 1
    
    with lock:
        processed += 1
        if processed % 100 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = processed / elapsed
            eta = (total_tokens - processed) / rate / 60
            print(f"Progress: {processed:,}/{total_tokens:,} ({processed/total_tokens*100:.1f}%) - "
                  f"Updated: {updated:,} - Rate: {rate:.1f}/s - ETA: {eta:.1f} min")

# Process in batches with parallel execution
batch_size = 1000
max_workers = 10

for offset in range(0, total_tokens, batch_size):
    # Get batch
    batch = supabase.table('crypto_calls').select(
        'krom_id, ticker, contract_address, network, price_at_call, current_price'
    ).not_.is_('contract_address', 'null').offset(offset).limit(batch_size).execute()
    
    if not batch.data:
        break
    
    # Process batch in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(fetch_and_update_price, batch.data)

# Final summary
elapsed = (datetime.now() - start_time).total_seconds()
print(f"\n=== COMPLETE ===")
print(f"Total processed: {processed:,}")
print(f"Successfully updated: {updated:,} ({updated/processed*100:.1f}%)")
print(f"Failed/No data: {errors:,} ({errors/processed*100:.1f}%)")
print(f"Total time: {elapsed/60:.1f} minutes")
print(f"Average rate: {processed/elapsed:.1f} tokens/second")
