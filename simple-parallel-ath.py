#!/usr/bin/env python3
"""Simple parallel ATH processor"""
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

def process_single_token(token_data):
    """Process one token"""
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
            return None
        
        # Fetch daily OHLCV
        url = f"{API_BASE}/networks/{network}/pools/{pool}/ohlcv/day"
        response = requests.get(url, params={'aggregate': 1, 'limit': 1000}, headers=HEADERS, timeout=30)
        
        if response.status_code != 200:
            return None
            
        data = response.json()
        candles = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
        
        # Find ATH after call
        ath_price = 0
        ath_ts = 0
        
        for candle in candles:
            if candle[0] >= call_ts and candle[2] > ath_price:  # candle[2] is high
                ath_price = candle[2]
                ath_ts = candle[0]
        
        if ath_price == 0:
            return None
        
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
    print("🚀 Starting simple parallel ATH processing", flush=True)
    
    # Get tokens to process
    tokens_query = """
    SELECT id, ticker, network, pool_address, buy_timestamp, price_at_call, raw_data
    FROM crypto_calls
    WHERE pool_address IS NOT NULL 
    AND price_at_call IS NOT NULL
    AND ath_price IS NULL
    ORDER BY created_at ASC
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