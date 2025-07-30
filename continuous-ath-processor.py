#!/usr/bin/env python3
"""
Continuous ATH processor - processes all remaining tokens
"""
import requests
import time
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
MANAGEMENT_TOKEN = "sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7"
PROJECT_REF = "eucfoommxxvqmmwdbkdv"
GECKO_API_KEY = os.getenv("GECKO_TERMINAL_API_KEY", "")
BATCH_SIZE = 500  # Process 500 at a time

# Use Pro API
API_BASE = "https://pro-api.coingecko.com/api/v3/onchain"
HEADERS = {"x-cg-pro-api-key": GECKO_API_KEY}
DELAY = 0.5  # 500ms for Pro API

NETWORK_MAP = {
    'ethereum': 'eth',
    'solana': 'solana',
    'bsc': 'bsc',
    'polygon': 'polygon',
    'arbitrum': 'arbitrum',
    'base': 'base'
}

def run_query(query):
    """Execute query via Supabase Management API"""
    response = requests.post(
        f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
        headers={"Authorization": f"Bearer {MANAGEMENT_TOKEN}", "Content-Type": "application/json"},
        json={"query": query}
    )
    return response.json()

def fetch_ohlcv(network, pool_address, timeframe, limit=1000, before_timestamp=None):
    """Fetch OHLCV data"""
    url = f"{API_BASE}/networks/{network}/pools/{pool_address}/ohlcv/{timeframe}"
    params = {'aggregate': 1, 'limit': limit}
    if before_timestamp:
        params['before_timestamp'] = before_timestamp
    
    response = requests.get(url, params=params, headers=HEADERS)
    if response.status_code == 429:
        print("  Rate limit hit, waiting 60s...")
        time.sleep(60)
        return fetch_ohlcv(network, pool_address, timeframe, limit, before_timestamp)
    
    if response.status_code != 200:
        raise Exception(f"API error {response.status_code}")
    
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

def process_token(token):
    """Process a single token"""
    try:
        network = NETWORK_MAP.get(token['network'], token['network'])
        
        # Get call timestamp
        call_timestamp = None
        if token['buy_timestamp']:
            call_timestamp = int(datetime.fromisoformat(token['buy_timestamp'].replace('Z', '+00:00')).timestamp())
        elif token['raw_data'] and 'timestamp' in token['raw_data']:
            call_timestamp = token['raw_data']['timestamp']
        
        if not call_timestamp:
            return None
        
        # TIER 1: Daily
        daily_data = fetch_ohlcv(network, token['pool_address'], 'day', 1000)
        daily_after_call = [c for c in daily_data if c['timestamp'] >= call_timestamp and c['high'] > 0]
        
        if not daily_after_call:
            return None
        
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
                # Use max(open, close) as designed
                ath_price = max(minute_ath['open'], minute_ath['close'])
                ath_timestamp = minute_ath['timestamp']
            else:
                ath_price = hourly_ath['high']
                ath_timestamp = hourly_ath['timestamp']
        
        # Calculate ROI
        ath_roi = ((ath_price - float(token['price_at_call'])) / float(token['price_at_call'])) * 100
        ath_roi = max(0, ath_roi)  # Never negative
        
        # Update database
        update_query = f"""
        UPDATE crypto_calls 
        SET ath_price = {ath_price}, 
            ath_timestamp = '{datetime.fromtimestamp(ath_timestamp).isoformat()}',
            ath_roi_percent = {ath_roi}
        WHERE id = '{token['id']}'
        """
        run_query(update_query)
        
        return True
        
    except Exception as e:
        return False

# Main processing loop
print("🚀 Starting continuous ATH processing")
print(f"Using CoinGecko Pro API")
print(f"Batch size: {BATCH_SIZE}")
print(f"Delay between tokens: {DELAY}s\n")

total_processed = 0
total_failed = 0
start_time = time.time()

while True:
    # Get next batch
    tokens_query = f"""
    SELECT id, ticker, network, pool_address, buy_timestamp, price_at_call, raw_data
    FROM crypto_calls
    WHERE pool_address IS NOT NULL 
    AND price_at_call IS NOT NULL
    AND ath_price IS NULL
    ORDER BY created_at ASC
    LIMIT {BATCH_SIZE}
    """
    
    tokens_data = run_query(tokens_query)
    
    if not tokens_data:
        print("\n✅ All tokens processed!")
        break
    
    print(f"\n📊 Processing batch of {len(tokens_data)} tokens...")
    batch_start = time.time()
    batch_success = 0
    batch_failed = 0
    
    for i, token in enumerate(tokens_data):
        success = process_token(token)
        
        if success:
            batch_success += 1
            total_processed += 1
        else:
            batch_failed += 1
            total_failed += 1
        
        # Progress update every 10 tokens
        if (i + 1) % 10 == 0:
            elapsed = time.time() - start_time
            rate = total_processed / (elapsed / 60) if elapsed > 0 else 0
            print(f"  Progress: {i+1}/{len(tokens_data)} | "
                  f"Success: {batch_success} | "
                  f"Rate: {rate:.1f}/min")
        
        # Rate limiting
        time.sleep(DELAY)
    
    # Batch summary
    batch_time = time.time() - batch_start
    print(f"\n✅ Batch complete in {batch_time/60:.1f} minutes")
    print(f"   Success: {batch_success}")
    print(f"   Failed: {batch_failed}")
    
    # Overall progress
    count_result = run_query("SELECT COUNT(*) FROM crypto_calls WHERE ath_price IS NOT NULL")
    total_count = count_result[0]['count']
    
    total_result = run_query("SELECT COUNT(*) FROM crypto_calls WHERE pool_address IS NOT NULL AND price_at_call IS NOT NULL")
    total_tokens = total_result[0]['count']
    
    print(f"\n📈 Overall Progress: {total_count}/{total_tokens} ({total_count/total_tokens*100:.1f}%)")
    print(f"   Total processed: {total_processed}")
    print(f"   Total failed: {total_failed}")
    print(f"   Remaining: {total_tokens - total_count}")

# Final summary
total_time = time.time() - start_time
print(f"\n🎉 PROCESSING COMPLETE!")
print(f"Total time: {total_time/3600:.1f} hours")
print(f"Total processed: {total_processed}")
print(f"Total failed: {total_failed}")
print(f"Average rate: {total_processed/(total_time/60):.1f} tokens/minute")