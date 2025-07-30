import os
from supabase import create_client
from dotenv import load_dotenv
import requests
import time
from datetime import datetime, timedelta
import threading
from queue import Queue
import sys

load_dotenv()
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

# Global counters (thread-safe)
stats_lock = threading.Lock()
stats = {
    'updated': 0,
    'failed': 0,
    'updated_via_dex': 0,
    'updated_via_gecko': 0,
    'start_time': time.time()
}

def create_supabase_client():
    """Create a new Supabase client for each thread"""
    return create_client(url, key)

def process_batch(batch_tokens, worker_id):
    """Process a batch of tokens"""
    supabase = create_supabase_client()
    local_updated = 0
    local_failed = 0
    local_dex = 0
    local_gecko = 0
    
    # Track which tokens we're looking for
    tokens_by_address = {}
    for token in batch_tokens:
        tokens_by_address[token['contract_address'].lower()] = token
    
    # Prepare addresses for DexScreener
    addresses = ','.join([t['contract_address'] for t in batch_tokens])
    
    # Track which tokens were found
    found_in_dexscreener = set()
    
    # Try DexScreener batch API
    try:
        response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{addresses}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Process DexScreener results
            if data.get('pairs'):
                for pair in data['pairs']:
                    contract = pair['baseToken']['address'].lower()
                    if contract in tokens_by_address and contract not in found_in_dexscreener:
                        found_in_dexscreener.add(contract)
                        token = tokens_by_address[contract]
                        new_price = float(pair['priceUsd'])
                        
                        # Update database
                        update_data = {
                            'current_price': new_price,
                            'price_updated_at': datetime.utcnow().isoformat()
                        }
                        
                        if token['price_at_call'] and token['price_at_call'] > 0:
                            roi = ((new_price - token['price_at_call']) / token['price_at_call']) * 100
                            update_data['roi_percent'] = roi
                        
                        result = supabase.table('crypto_calls').update(update_data).eq('krom_id', token['krom_id']).execute()
                        
                        if result.data:
                            local_updated += 1
                            local_dex += 1
    except Exception as e:
        print(f"[Worker {worker_id}] DexScreener error: {str(e)[:50]}")
    
    # Try GeckoTerminal for missing tokens
    missing_tokens = []
    for address, token in tokens_by_address.items():
        if address not in found_in_dexscreener:
            missing_tokens.append(token)
    
    # Process missing tokens with GeckoTerminal
    for token in missing_tokens:
        if token['network']:
            network_map = {'ethereum': 'eth', 'solana': 'solana', 'bsc': 'bsc', 'polygon': 'polygon', 'arbitrum': 'arbitrum', 'base': 'base'}
            api_network = network_map.get(token['network'], token['network'])
            
            # Rate limit for GeckoTerminal
            time.sleep(0.3)
            
            try:
                gecko_response = requests.get(
                    f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{token['contract_address']}/pools"
                )
                
                if gecko_response.status_code == 200:
                    gecko_data = gecko_response.json()
                    pools = gecko_data.get('data', [])
                    
                    if pools:
                        # Sort by liquidity (FIXED logic)
                        sorted_pools = sorted(pools, key=lambda p: float(p['attributes'].get('reserve_in_usd', 0)), reverse=True)
                        best_pool = sorted_pools[0]
                        best_price = float(best_pool['attributes'].get('token_price_usd', 0))
                        
                        if best_price > 0:
                            # Update database
                            update_data = {
                                'current_price': best_price,
                                'price_updated_at': datetime.utcnow().isoformat()
                            }
                            
                            if token['price_at_call'] and token['price_at_call'] > 0:
                                roi = ((best_price - token['price_at_call']) / token['price_at_call']) * 100
                                update_data['roi_percent'] = roi
                            
                            result = supabase.table('crypto_calls').update(update_data).eq('krom_id', token['krom_id']).execute()
                            
                            if result.data:
                                local_updated += 1
                                local_gecko += 1
                        else:
                            local_failed += 1
                    else:
                        local_failed += 1
                elif gecko_response.status_code == 429:
                    print(f"[Worker {worker_id}] GeckoTerminal rate limit - waiting...")
                    time.sleep(30)  # Wait on rate limit
                    local_failed += 1
                else:
                    local_failed += 1
            except Exception as e:
                local_failed += 1
        else:
            local_failed += 1
    
    # Update global stats
    with stats_lock:
        stats['updated'] += local_updated
        stats['failed'] += local_failed
        stats['updated_via_dex'] += local_dex
        stats['updated_via_gecko'] += local_gecko
    
    return local_updated, local_failed

def worker(queue, worker_id):
    """Worker thread that processes batches from queue"""
    while True:
        batch = queue.get()
        if batch is None:
            break
        
        updated, failed = process_batch(batch, worker_id)
        print(f"[Worker {worker_id}] Batch complete: {updated} updated, {failed} failed")
        
        queue.task_done()

def main():
    print("=== PARALLEL PRICE REFRESH ===")
    print(f"Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Number of worker threads
    NUM_WORKERS = 5  # Adjust based on rate limits
    
    # Get initial Supabase client for queries
    supabase = create_supabase_client()
    
    # Get count of tokens to update
    count_result = supabase.table('crypto_calls').select('id', count='exact').not_.is_('current_price', 'null').not_.is_('contract_address', 'null').lt('price_updated_at', datetime.utcnow() - timedelta(hours=2)).execute()
    total_to_update = count_result.count
    
    print(f"Found {total_to_update} tokens needing updates")
    print(f"Using {NUM_WORKERS} parallel workers")
    print("Processing in batches of 30...\n")
    
    # Create queue and worker threads
    queue = Queue()
    threads = []
    
    for i in range(NUM_WORKERS):
        t = threading.Thread(target=worker, args=(queue, i+1))
        t.start()
        threads.append(t)
    
    # Load batches into queue
    offset = 0
    batch_count = 0
    
    while offset < total_to_update:
        # Get next batch
        tokens = supabase.table('crypto_calls').select(
            'krom_id, ticker, contract_address, network, price_at_call'
        ).not_.is_('current_price', 'null').not_.is_('contract_address', 'null').order('price_updated_at', desc=False).range(offset, offset + 29).execute()
        
        if not tokens.data:
            break
        
        queue.put(tokens.data)
        batch_count += 1
        offset += 30
        
        # Progress update every 20 batches
        if batch_count % 20 == 0:
            with stats_lock:
                elapsed = time.time() - stats['start_time']
                rate = stats['updated'] / elapsed * 60 if elapsed > 0 else 0
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Loaded {batch_count} batches")
                print(f"Progress: {stats['updated']}/{offset} tokens")
                print(f"Rate: {rate:.1f} tokens/minute")
    
    print(f"\nAll {batch_count} batches loaded. Waiting for workers to finish...")
    
    # Wait for all batches to be processed
    queue.join()
    
    # Stop workers
    for i in range(NUM_WORKERS):
        queue.put(None)
    
    for t in threads:
        t.join()
    
    # Final summary
    elapsed_total = time.time() - stats['start_time']
    print(f"\n\n=== FINAL SUMMARY ===")
    print(f"Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total time: {elapsed_total/60:.1f} minutes")
    print(f"Total processed: {stats['updated'] + stats['failed']}")
    print(f"Successfully updated: {stats['updated']} tokens")
    print(f"  - Via DexScreener: {stats['updated_via_dex']}")
    print(f"  - Via GeckoTerminal: {stats['updated_via_gecko']}")
    print(f"Failed/Dead tokens: {stats['failed']}")
    print(f"Success rate: {stats['updated']/(stats['updated']+stats['failed'])*100:.1f}%" if stats['updated']+stats['failed'] > 0 else "N/A")
    print(f"Average rate: {stats['updated']/elapsed_total*60:.1f} tokens/minute")

if __name__ == "__main__":
    main()