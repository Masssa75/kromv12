#!/usr/bin/env python3
import json
import urllib.request
import concurrent.futures
import threading
import time
from datetime import datetime

print("=== Processing ALL Tokens Without Prices (Including Dead Tokens) ===")
print(f"Started: {datetime.now()}")
print()

# Configuration
PARALLEL_WORKERS = 10
BATCH_SIZE = 100
RATE_LIMIT = 450
rate_limiter = threading.Semaphore(RATE_LIMIT)
rate_reset_timer = None

# Get service key
service_key = None
with open('.env', 'r') as f:
    for line in f:
        if line.startswith('SUPABASE_SERVICE_ROLE_KEY='):
            service_key = line.split('=', 1)[1].strip()
            break

supabase_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls"
edge_function_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-historical"

# Stats tracking
stats = {
    'krom': 0,
    'gecko': 0,
    'dead': 0,
    'no_pool': 0,
    'errors': 0,
    'revived': 0  # Tokens that were dead but now have prices
}
stats_lock = threading.Lock()

def reset_rate_limit():
    """Reset rate limit every minute"""
    global rate_limiter, rate_reset_timer
    rate_limiter = threading.Semaphore(RATE_LIMIT)
    rate_reset_timer = threading.Timer(60.0, reset_rate_limit)
    rate_reset_timer.daemon = True
    rate_reset_timer.start()

def get_current_count():
    """Get current count of tokens with prices"""
    count_url = f"{supabase_url}?select=*&price_at_call=not.is.null"
    count_req = urllib.request.Request(count_url, method='HEAD')
    count_req.add_header('apikey', service_key)
    count_req.add_header('Authorization', f'Bearer {service_key}')
    count_req.add_header('Prefer', 'count=exact')
    
    try:
        response = urllib.request.urlopen(count_req)
        content_range = response.headers.get('content-range')
        if content_range:
            return int(content_range.split('/')[1])
    except:
        pass
    return 0

def process_token(token):
    """Process a single token"""
    ticker = token.get('ticker', 'Unknown')
    network = token.get('network', 'unknown')
    pool = token.get('pool_address')
    contract = token.get('contract_address', 'unknown')
    buy_timestamp = token.get('buy_timestamp')
    created_at = token.get('created_at')
    raw_data = token.get('raw_data', {})
    krom_id = token.get('krom_id')
    previous_source = token.get('price_source')
    
    # First check for KROM price
    krom_price = None
    try:
        krom_price = float(raw_data.get('trade', {}).get('buyPrice', 0))
        if krom_price > 0:
            # Update with KROM price
            update_data = {
                'price_at_call': krom_price,
                'price_source': 'KROM',
                'price_updated_at': datetime.now().isoformat()
            }
            
            update_url = f"{supabase_url}?krom_id=eq.{krom_id}"
            update_req = urllib.request.Request(
                update_url,
                data=json.dumps(update_data).encode('utf-8'),
                headers={
                    'apikey': service_key,
                    'Authorization': f'Bearer {service_key}',
                    'Content-Type': 'application/json',
                    'Prefer': 'return=minimal'
                },
                method='PATCH'
            )
            
            urllib.request.urlopen(update_req)
            with stats_lock:
                stats['krom'] += 1
                if previous_source == 'DEAD_TOKEN':
                    stats['revived'] += 1
            return f"✅ {ticker}: KROM ${krom_price:.8f}"
    except:
        pass
    
    # No KROM price - check if we can fetch from Gecko
    if not pool:
        # Keep existing status
        with stats_lock:
            stats['no_pool'] += 1
        return f"❌ {ticker}: No pool"
    
    # Determine which timestamp to use
    timestamp_to_use = buy_timestamp or created_at
    
    if not timestamp_to_use:
        with stats_lock:
            stats['errors'] += 1
        return f"❌ {ticker}: No timestamp"
    
    # Convert timestamp
    try:
        if 'Z' in timestamp_to_use:
            unix_timestamp = int(datetime.fromisoformat(timestamp_to_use.replace('Z', '+00:00')).timestamp())
        elif '+' in timestamp_to_use:
            unix_timestamp = int(datetime.fromisoformat(timestamp_to_use).timestamp())
        else:
            unix_timestamp = int(datetime.fromisoformat(timestamp_to_use + '+00:00').timestamp())
    except:
        clean_timestamp = timestamp_to_use.split('.')[0] + '+00:00'
        unix_timestamp = int(datetime.fromisoformat(clean_timestamp).timestamp())
    
    # Map network if needed
    mapped_network = network
    if network.lower() == 'ethereum':
        mapped_network = 'eth'
    
    # Rate limit before API call
    rate_limiter.acquire()
    
    request_data = {
        "contractAddress": contract,
        "network": mapped_network,
        "poolAddress": pool,
        "timestamp": unix_timestamp
    }
    
    edge_req = urllib.request.Request(
        edge_function_url,
        data=json.dumps(request_data).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {service_key}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    
    try:
        edge_response = urllib.request.urlopen(edge_req)
        edge_data = json.loads(edge_response.read().decode())
        
        if edge_data.get('price'):
            fetched_price = float(edge_data['price'])
            
            update_data = {
                'price_at_call': fetched_price,
                'price_source': 'GECKO',
                'price_updated_at': datetime.now().isoformat()
            }
            
            update_url = f"{supabase_url}?krom_id=eq.{krom_id}"
            update_req = urllib.request.Request(
                update_url,
                data=json.dumps(update_data).encode('utf-8'),
                headers={
                    'apikey': service_key,
                    'Authorization': f'Bearer {service_key}',
                    'Content-Type': 'application/json',
                    'Prefer': 'return=minimal'
                },
                method='PATCH'
            )
            
            urllib.request.urlopen(update_req)
            with stats_lock:
                stats['gecko'] += 1
                if previous_source == 'DEAD_TOKEN':
                    stats['revived'] += 1
            return f"🦎 {ticker} ({network}): ${fetched_price:.8f} {'(REVIVED!)' if previous_source == 'DEAD_TOKEN' else ''}"
        else:
            # Still dead
            with stats_lock:
                stats['dead'] += 1
            return f"💀 {ticker} ({network}): Still dead"
            
    except Exception as e:
        # Still dead
        with stats_lock:
            stats['dead'] += 1
        return f"💀 {ticker} ({network}): Still dead"

def process_batch(batch_number, offset):
    """Process a batch of tokens in parallel"""
    # Get ALL tokens without prices (including dead ones)
    query_url = f"{supabase_url}?select=*&price_at_call=is.null&order=created_at.asc&limit={BATCH_SIZE}&offset={offset}"
    
    req = urllib.request.Request(query_url)
    req.add_header('apikey', service_key)
    req.add_header('Authorization', f'Bearer {service_key}')
    
    try:
        response = urllib.request.urlopen(req)
        tokens = json.loads(response.read().decode())
        
        if not tokens:
            return 0
        
        print(f"\n{'='*60}")
        print(f"BATCH {batch_number} - Processing {len(tokens)} tokens")
        print(f"{'='*60}")
        
        # Check how many are previously marked dead
        dead_count = sum(1 for t in tokens if t.get('price_source') == 'DEAD_TOKEN')
        if dead_count > 0:
            print(f"📊 Including {dead_count} previously dead tokens")
        
        # Process tokens in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
            # Submit all tokens for processing
            future_to_token = {executor.submit(process_token, token): token for token in tokens}
            
            # Track progress
            completed = 0
            
            for future in concurrent.futures.as_completed(future_to_token):
                completed += 1
                result = future.result()
                
                # Print progress every 10 tokens
                if completed % 10 == 0:
                    print(f"Progress: {completed}/{len(tokens)} - KROM:{stats['krom']} Gecko:{stats['gecko']} Dead:{stats['dead']} Revived:{stats['revived']}")
        
        return len(tokens)
        
    except Exception as e:
        print(f"❌ Error processing batch: {e}")
        return 0

# Start rate limit reset timer
reset_rate_limit()

# Main processing
initial_count = get_current_count()
print(f"\n📊 Starting count: {initial_count:,} tokens have prices")
print(f"🎯 Processing ALL tokens without prices (including dead ones)")

batch_number = 1
offset = 0
total_processed = 0
start_time = time.time()

while True:
    processed = process_batch(batch_number, offset)
    
    if processed == 0:
        print("\n✅ No more tokens to process!")
        break
    
    total_processed += processed
    current_count = get_current_count()
    elapsed = time.time() - start_time
    rate = (current_count - initial_count) / elapsed * 60 if elapsed > 0 else 0
    
    print(f"\n📊 Batch {batch_number} Summary:")
    print(f"   Total progress: {current_count:,} tokens with prices")
    print(f"   Processed this session: {current_count - initial_count}")
    print(f"   Rate: {rate:.0f} tokens/minute")
    
    with stats_lock:
        print(f"\n📈 Session Stats:")
        print(f"   KROM prices: {stats['krom']}")
        print(f"   Gecko prices: {stats['gecko']}")
        print(f"   Still dead: {stats['dead']}")
        print(f"   🎉 REVIVED: {stats['revived']} (were dead, now have prices!)")
    
    batch_number += 1
    offset += BATCH_SIZE

# Cleanup
if rate_reset_timer:
    rate_reset_timer.cancel()

final_count = get_current_count()
print(f"\n{'='*60}")
print("FINAL SUMMARY")
print(f"{'='*60}")
print(f"Total batches: {batch_number - 1}")
print(f"Tokens processed: {final_count - initial_count}")
print(f"Final count: {final_count:,} tokens with prices")
print(f"Total time: {(time.time() - start_time) / 60:.1f} minutes")

with stats_lock:
    print(f"\nFinal Stats:")
    print(f"   KROM prices found: {stats['krom']}")
    print(f"   Gecko prices fetched: {stats['gecko']}")
    print(f"   Still dead: {stats['dead']}")
    print(f"   No pool: {stats['no_pool']}")
    print(f"   🎉 TOKENS REVIVED: {stats['revived']}")
    
if stats['revived'] > 0:
    print(f"\n🎉 Amazing! {stats['revived']} tokens that were marked dead now have prices!")