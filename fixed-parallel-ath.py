#!/usr/bin/env python3
"""Fixed parallel ATH processor with proper day boundary handling"""
import requests
import time
from datetime import datetime
import os
from multiprocessing import Pool, current_process
import sys

# Flush output immediately
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

# Configuration
MANAGEMENT_TOKEN = "sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7"
PROJECT_REF = "eucfoommxxvqmmwdbkdv"
GECKO_API_KEY = os.getenv("GECKO_TERMINAL_API_KEY", "CG-rNYcUB85FxH1tZqqRmU5H8eY")
API_BASE = "https://pro-api.coingecko.com/api/v3/onchain"
HEADERS = {"x-cg-pro-api-key": GECKO_API_KEY}
NETWORK_MAP = {'ethereum': 'eth', 'solana': 'solana', 'bsc': 'bsc', 'polygon': 'polygon'}

def run_query(query):
    """Execute query"""
    try:
        response = requests.post(
            f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
            headers={"Authorization": f"Bearer {MANAGEMENT_TOKEN}", "Content-Type": "application/json"},
            json={"query": query},
            timeout=10
        )
        return response.json()
    except:
        return []

def fetch_ohlcv(network, pool, timeframe, limit=1000, before_timestamp=None):
    """Fetch OHLCV data"""
    url = f"{API_BASE}/networks/{network}/pools/{pool}/ohlcv/{timeframe}"
    params = {'aggregate': 1, 'limit': limit}
    if before_timestamp:
        params['before_timestamp'] = before_timestamp
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            return []
        
        data = response.json()
        return data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
    except:
        return []

def process_single_token(token_data):
    """Process one token with fixed ATH logic"""
    worker = current_process().name
    token_id, ticker, network, pool, timestamp, price, raw_data = token_data
    
    try:
        print(f"[{worker}] Processing {ticker}...", flush=True)
        
        # Get network and timestamp
        network = NETWORK_MAP.get(network, network)
        if timestamp:
            call_ts = int(datetime.fromisoformat(timestamp.replace('Z', '+00:00')).timestamp())
        elif raw_data and 'timestamp' in raw_data:
            call_ts = raw_data['timestamp']
        else:
            # Use created_at if no other timestamp available
            return None
        
        # FIX: Get start of call day (midnight)
        call_date = datetime.fromtimestamp(call_ts).replace(hour=0, minute=0, second=0, microsecond=0)
        call_day_start = int(call_date.timestamp())
        
        # TIER 1: Daily - fetch from START of call day
        daily_data = fetch_ohlcv(network, pool, 'day', 1000)
        daily_from_call_day = [c for c in daily_data if c[0] >= call_day_start and c[2] > 0]
        
        if not daily_from_call_day:
            return None
        
        daily_ath = max(daily_from_call_day, key=lambda x: x[2])
        
        # TIER 2: Hourly
        before_ts = daily_ath[0] + (86400 + 43200)  # 1.5 days after
        hourly_data = fetch_ohlcv(network, pool, 'hour', 72, before_ts)
        
        hourly_around_ath = [c for c in hourly_data 
                            if abs(c[0] - daily_ath[0]) <= 86400 and c[2] > 0]
        
        if not hourly_around_ath:
            # If no hourly data, use daily high
            ath_price = daily_ath[2]
            ath_ts = daily_ath[0]
        else:
            hourly_ath = max(hourly_around_ath, key=lambda x: x[2])
            
            # TIER 3: Minute
            minute_before_ts = hourly_ath[0] + 3600
            minute_data = fetch_ohlcv(network, pool, 'minute', 120, minute_before_ts)
            
            # FIX: Only consider minutes AFTER the actual call timestamp
            minute_around_ath = [c for c in minute_data 
                                if abs(c[0] - hourly_ath[0]) <= 3600 
                                and c[0] >= call_ts  # Only minutes after call
                                and c[2] > 0 and c[4] > 0]  # c[4] is close
            
            if minute_around_ath:
                minute_ath = max(minute_around_ath, key=lambda x: x[2])
                # Use max(open, close) for realistic ATH
                ath_price = max(minute_ath[1], minute_ath[4])
                ath_ts = minute_ath[0]
            else:
                ath_price = hourly_ath[2]
                ath_ts = hourly_ath[0]
        
        # Calculate ROI
        roi = max(0, ((ath_price - float(price)) / float(price)) * 100)
        
        # Update database
        update_query = f"""
        UPDATE crypto_calls 
        SET ath_price = {ath_price}, 
            ath_timestamp = '{datetime.fromtimestamp(ath_ts).isoformat()}',
            ath_roi_percent = {roi}
        WHERE id = '{token_id}'
        """
        run_query(update_query)
        
        print(f"[{worker}] ✅ {ticker}: ATH ${ath_price:.8f} (ROI: {roi:.1f}%)", flush=True)
        return 1
        
    except Exception as e:
        print(f"[{worker}] ❌ {ticker}: {str(e)}", flush=True)
        return 0

# Main
if __name__ == '__main__':
    print("🚀 Starting FIXED parallel ATH processing", flush=True)
    
    # Get tokens to process
    tokens_query = """
    SELECT id, ticker, network, pool_address, buy_timestamp, price_at_call, raw_data
    FROM crypto_calls
    WHERE pool_address IS NOT NULL 
    AND price_at_call IS NOT NULL
    AND ath_price IS NULL
    ORDER BY created_at DESC
    LIMIT 500
    """
    
    tokens = run_query(tokens_query)
    print(f"Found {len(tokens)} tokens to process", flush=True)
    
    if not tokens:
        print("No tokens to process!")
        exit(0)
    
    # Prepare data for multiprocessing
    token_data = [(t['id'], t['ticker'], t['network'], t['pool_address'], 
                   t['buy_timestamp'], t['price_at_call'], t['raw_data']) for t in tokens]
    
    # Process in parallel with 6 workers
    start_time = time.time()
    with Pool(processes=6) as pool:
        results = pool.map(process_single_token, token_data)
    
    # Summary
    successful = sum(1 for r in results if r == 1)
    elapsed = time.time() - start_time
    
    print(f"\n✅ Processed {successful}/{len(tokens)} tokens in {elapsed/60:.1f} minutes", flush=True)
    print(f"Rate: {successful/(elapsed/60):.1f} tokens/minute", flush=True)