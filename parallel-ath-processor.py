#!/usr/bin/env python3
"""
Parallel ATH processor - runs multiple workers to speed up processing
"""
import requests
import time
from datetime import datetime
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import random

load_dotenv()

# Configuration
MANAGEMENT_TOKEN = "sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7"
PROJECT_REF = "eucfoommxxvqmmwdbkdv"
GECKO_API_KEY = os.getenv("GECKO_TERMINAL_API_KEY", "")
NUM_WORKERS = 6  # Number of parallel workers
BATCH_SIZE = 50  # Tokens per batch

# Use Pro API
API_BASE = "https://pro-api.coingecko.com/api/v3/onchain"
HEADERS = {"x-cg-pro-api-key": GECKO_API_KEY}

NETWORK_MAP = {
    'ethereum': 'eth',
    'solana': 'solana',
    'bsc': 'bsc',
    'polygon': 'polygon',
    'arbitrum': 'arbitrum',
    'base': 'base'
}

# Thread-safe counters
lock = threading.Lock()
total_processed = 0
total_failed = 0
processing_tokens = set()  # Track tokens being processed

def run_query(query):
    """Execute query via Supabase Management API"""
    try:
        response = requests.post(
            f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
            headers={"Authorization": f"Bearer {MANAGEMENT_TOKEN}", "Content-Type": "application/json"},
            json={"query": query},
            timeout=10
        )
        return response.json()
    except Exception as e:
        print(f"Database error: {e}")
        return []

def fetch_ohlcv(network, pool_address, timeframe, limit=1000, before_timestamp=None):
    """Fetch OHLCV data with retry logic"""
    url = f"{API_BASE}/networks/{network}/pools/{pool_address}/ohlcv/{timeframe}"
    params = {'aggregate': 1, 'limit': limit}
    if before_timestamp:
        params['before_timestamp'] = before_timestamp
    
    for attempt in range(3):  # 3 attempts
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=30)
            
            if response.status_code == 429:  # Rate limit
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
                
            if response.status_code != 200:
                return []
            
            data = response.json()
            ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
            
            return [{
                'timestamp': candle[0],
                'open': candle[1] or 0,
                'high': candle[2] or 0,
                'low': candle[3] or 0,
                'close': candle[4] or 0,
                'volume': candle[5] or 0
            } for candle in ohlcv_list]
            
        except Exception:
            if attempt < 2:
                time.sleep(1)
                continue
            return []
    
    return []

def process_token(token, worker_id):
    """Process a single token"""
    global total_processed, total_failed
    
    try:
        network = NETWORK_MAP.get(token['network'], token['network'])
        
        # Get call timestamp
        call_timestamp = None
        if token['buy_timestamp']:
            call_timestamp = int(datetime.fromisoformat(token['buy_timestamp'].replace('Z', '+00:00')).timestamp())
        elif token['raw_data'] and 'timestamp' in token['raw_data']:
            call_timestamp = token['raw_data']['timestamp']
        
        if not call_timestamp:
            return False
        
        # TIER 1: Daily
        daily_data = fetch_ohlcv(network, token['pool_address'], 'day', 1000)
        daily_after_call = [c for c in daily_data if c['timestamp'] >= call_timestamp and c['high'] > 0]
        
        if not daily_after_call:
            return False
        
        daily_ath = max(daily_after_call, key=lambda x: x['high'])
        
        # TIER 2: Hourly
        before_ts = daily_ath['timestamp'] + (86400 + 43200)
        hourly_data = fetch_ohlcv(network, token['pool_address'], 'hour', 72, before_ts)
        
        hourly_around_ath = [c for c in hourly_data 
                            if abs(c['timestamp'] - daily_ath['timestamp']) <= 86400 and c['high'] > 0]
        
        if not hourly_around_ath:
            ath_price = daily_ath['high']
            ath_timestamp = daily_ath['timestamp']
        else:
            hourly_ath = max(hourly_around_ath, key=lambda x: x['high'])
            
            # TIER 3: Minute
            minute_before_ts = hourly_ath['timestamp'] + 3600
            minute_data = fetch_ohlcv(network, token['pool_address'], 'minute', 120, minute_before_ts)
            
            minute_around_ath = [c for c in minute_data 
                                if abs(c['timestamp'] - hourly_ath['timestamp']) <= 3600 
                                and c['high'] > 0 and c['close'] > 0]
            
            if minute_around_ath:
                minute_ath = max(minute_around_ath, key=lambda x: x['high'])
                ath_price = max(minute_ath['open'], minute_ath['close'])
                ath_timestamp = minute_ath['timestamp']
            else:
                ath_price = hourly_ath['high']
                ath_timestamp = hourly_ath['timestamp']
        
        # Calculate ROI
        ath_roi = ((ath_price - float(token['price_at_call'])) / float(token['price_at_call'])) * 100
        ath_roi = max(0, ath_roi)
        
        # Update database
        update_query = f"""
        UPDATE crypto_calls 
        SET ath_price = {ath_price}, 
            ath_timestamp = '{datetime.fromtimestamp(ath_timestamp).isoformat()}',
            ath_roi_percent = {ath_roi}
        WHERE id = '{token['id']}'
        """
        run_query(update_query)
        
        with lock:
            total_processed += 1
            if total_processed % 10 == 0:
                print(f"[Worker {worker_id}] Progress: {total_processed} processed")
        
        return True
        
    except Exception as e:
        with lock:
            total_failed += 1
        return False

def worker_process_batch(worker_id):
    """Worker function that processes tokens"""
    print(f"[Worker {worker_id}] Started")
    
    while True:
        # Get batch of tokens to process
        # Build exclusion clause
        if processing_tokens:
            token_list = ','.join([f"'{tid}'" for tid in processing_tokens])
            exclusion = f"AND id NOT IN ({token_list})"
        else:
            exclusion = ""
        
        tokens_query = f"""
        SELECT id, ticker, network, pool_address, buy_timestamp, price_at_call, raw_data
        FROM crypto_calls
        WHERE pool_address IS NOT NULL 
        AND price_at_call IS NOT NULL
        AND ath_price IS NULL
        {exclusion}
        ORDER BY created_at ASC
        LIMIT {BATCH_SIZE}
        """
        
        with lock:
            tokens_data = run_query(tokens_query)
            if not tokens_data:
                print(f"[Worker {worker_id}] No more tokens to process")
                break
            
            # Mark tokens as being processed
            for token in tokens_data:
                processing_tokens.add(token['id'])
        
        # Process tokens
        for token in tokens_data:
            success = process_token(token, worker_id)
            
            # Remove from processing set
            with lock:
                processing_tokens.discard(token['id'])
            
            # Small random delay to avoid thundering herd
            time.sleep(random.uniform(0.1, 0.3))
        
        print(f"[Worker {worker_id}] Completed batch of {len(tokens_data)} tokens")

# Main execution
print(f"🚀 Starting parallel ATH processing with {NUM_WORKERS} workers")
print(f"Using CoinGecko Pro API")
print(f"Batch size per worker: {BATCH_SIZE}\n")

# Check initial count
initial_count = run_query("SELECT COUNT(*) FROM crypto_calls WHERE ath_price IS NOT NULL")[0]['count']
total_count = run_query("SELECT COUNT(*) FROM crypto_calls WHERE pool_address IS NOT NULL AND price_at_call IS NOT NULL")[0]['count']
print(f"Starting count: {initial_count}/{total_count}")
print(f"Tokens to process: {total_count - initial_count}\n")

start_time = time.time()

# Create thread pool
with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
    # Submit worker tasks
    futures = [executor.submit(worker_process_batch, i+1) for i in range(NUM_WORKERS)]
    
    # Wait for all workers to complete
    for future in as_completed(futures):
        try:
            future.result()
        except Exception as e:
            print(f"Worker error: {e}")

# Final summary
elapsed = time.time() - start_time
final_count = run_query("SELECT COUNT(*) FROM crypto_calls WHERE ath_price IS NOT NULL")[0]['count']
new_processed = final_count - initial_count

print(f"\n🎉 PARALLEL PROCESSING COMPLETE!")
print(f"Time elapsed: {elapsed/60:.1f} minutes")
print(f"New tokens processed: {new_processed}")
print(f"Total with ATH: {final_count}/{total_count} ({final_count/total_count*100:.1f}%)")
print(f"Processing rate: {new_processed/(elapsed/60):.1f} tokens/minute")
print(f"Speed improvement: {NUM_WORKERS}x")