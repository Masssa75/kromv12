#!/usr/bin/env python3
import json
import urllib.request
import time
from datetime import datetime
import concurrent.futures
import threading

# Configuration
PARALLEL_WORKERS = 10
BATCH_SIZE = 30  # Smaller batches for more frequent updates
RATE_LIMIT = 450
rate_limiter = threading.Semaphore(RATE_LIMIT)

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
stats = {'krom': 0, 'gecko': 0, 'dead': 0, 'total': 0}
stats_lock = threading.Lock()

def get_current_count():
    count_url = f"{supabase_url}?select=*&price_at_call=not.is.null"
    count_req = urllib.request.Request(count_url, method='HEAD')
    count_req.add_header('apikey', service_key)
    count_req.add_header('Authorization', f'Bearer {service_key}')
    count_req.add_header('Prefer', 'count=exact')
    
    response = urllib.request.urlopen(count_req)
    content_range = response.headers.get('content-range')
    return int(content_range.split('/')[1])

def process_token(token):
    ticker = token.get('ticker', 'Unknown')
    network = token.get('network', 'unknown')
    pool = token.get('pool_address')
    contract = token.get('contract_address', 'unknown')
    buy_timestamp = token.get('buy_timestamp')
    created_at = token.get('created_at')
    raw_data = token.get('raw_data', {})
    krom_id = token.get('krom_id')
    
    # Check for KROM price
    try:
        krom_price = float(raw_data.get('trade', {}).get('buyPrice', 0))
        if krom_price > 0:
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
                stats['total'] += 1
            return 'krom'
    except:
        pass
    
    if not pool:
        update_data = {
            'price_source': 'NO_POOL',
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
            stats['dead'] += 1
            stats['total'] += 1
        return 'no_pool'
    
    timestamp_to_use = buy_timestamp or created_at
    if not timestamp_to_use:
        return 'error'
    
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
    
    # Map network
    mapped_network = 'eth' if network.lower() == 'ethereum' else network
    
    # Rate limit
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
                stats['total'] += 1
            return 'gecko'
        else:
            update_data = {
                'price_source': 'DEAD_TOKEN',
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
                stats['dead'] += 1
                stats['total'] += 1
            return 'dead'
            
    except:
        update_data = {
            'price_source': 'DEAD_TOKEN',
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
            stats['dead'] += 1
            stats['total'] += 1
        return 'dead'

# Reset rate limit every minute
def reset_rate_limit():
    global rate_limiter
    rate_limiter = threading.Semaphore(RATE_LIMIT)
    timer = threading.Timer(60.0, reset_rate_limit)
    timer.daemon = True
    timer.start()

reset_rate_limit()

# Main processing
initial_count = get_current_count()
print(f"Starting at: {initial_count:,} tokens with prices")
print(f"Using {PARALLEL_WORKERS} parallel workers")
print("="*50)

offset = 0
start_time = time.time()

while True:
    # Get batch
    query_url = f"{supabase_url}?select=krom_id,ticker,network,pool_address,contract_address,buy_timestamp,created_at,raw_data&price_at_call=is.null&order=created_at.asc&limit={BATCH_SIZE}&offset={offset}"
    
    req = urllib.request.Request(query_url)
    req.add_header('apikey', service_key)
    req.add_header('Authorization', f'Bearer {service_key}')
    
    response = urllib.request.urlopen(req)
    tokens = json.loads(response.read().decode())
    
    if not tokens:
        break
    
    # Process in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
        futures = [executor.submit(process_token, token) for token in tokens]
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            result = future.result()
            
            # Update every 10 tokens
            if stats['total'] % 10 == 0:
                current_count = get_current_count()
                elapsed = time.time() - start_time
                rate = (stats['total'] / elapsed * 60) if elapsed > 0 else 0
                print(f"\n📊 Progress: {current_count:,}/5,663 ({current_count/5663*100:.1f}%) | "
                      f"Rate: {rate:.0f}/min | "
                      f"KROM: {stats['krom']} | Gecko: {stats['gecko']} | Dead: {stats['dead']}")
    
    offset += BATCH_SIZE

# Final summary
final_count = get_current_count()
elapsed = time.time() - start_time
print(f"\n{'='*50}")
print(f"COMPLETE! Processed {stats['total']} tokens in {elapsed/60:.1f} minutes")
print(f"Final count: {final_count:,} tokens with prices ({final_count/5663*100:.1f}%)")
print(f"Average rate: {stats['total'] / elapsed * 60:.0f} tokens/minute")