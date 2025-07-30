#!/usr/bin/env python3
"""
Manual ATH processor that mimics edge function logic
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

# Use Pro API if we have a key
if GECKO_API_KEY and GECKO_API_KEY.startswith("CG-"):
    API_BASE = "https://pro-api.coingecko.com/api/v3/onchain"
    HEADERS = {"x-cg-pro-api-key": GECKO_API_KEY}
    DELAY = 0.5  # 500ms for Pro API
    print(f"Using CoinGecko Pro API with key: {GECKO_API_KEY[:10]}...")
else:
    API_BASE = "https://api.geckoterminal.com/api/v2"
    HEADERS = {}
    DELAY = 2  # 2 seconds for free API
    print("Using free GeckoTerminal API")

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
        
        print(f"  Processing {token['ticker']} on {network}")
        print(f"  Entry: ${float(token['price_at_call']):.8f}")
        
        # TIER 1: Daily
        daily_data = fetch_ohlcv(network, token['pool_address'], 'day', 1000)
        daily_after_call = [c for c in daily_data if c['timestamp'] >= call_timestamp and c['high'] > 0]
        
        if not daily_after_call:
            print("  No data after call")
            return None
        
        daily_ath = max(daily_after_call, key=lambda x: x['high'])
        
        # TIER 2: Hourly
        before_ts = daily_ath['timestamp'] + (86400 + 43200)
        hourly_data = fetch_ohlcv(network, token['pool_address'], 'hour', 72, before_ts)
        
        hourly_around_ath = [c for c in hourly_data 
                            if abs(c['timestamp'] - daily_ath['timestamp']) <= 86400 and c['high'] > 0]
        
        if not hourly_around_ath:
            # Use daily
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
        
        print(f"  ATH: ${ath_price:.8f} (ROI: {ath_roi:.1f}%)")
        
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
        print(f"  Error: {e}")
        return False

# Main processing
print("\nFetching tokens to process...")
tokens_query = """
SELECT id, ticker, network, pool_address, buy_timestamp, price_at_call, raw_data
FROM crypto_calls
WHERE pool_address IS NOT NULL 
AND price_at_call IS NOT NULL
AND ath_price IS NULL
ORDER BY created_at ASC
LIMIT 100
"""

tokens_data = run_query(tokens_query)
print(f"Found {len(tokens_data)} tokens to process")

successful = 0
failed = 0

for i, token in enumerate(tokens_data):
    print(f"\n[{i+1}/{len(tokens_data)}]")
    
    if process_token(token):
        successful += 1
    else:
        failed += 1
    
    # Rate limiting
    time.sleep(DELAY)
    
    # Check progress every 10 tokens
    if (i + 1) % 10 == 0:
        count_result = run_query("SELECT COUNT(*) FROM crypto_calls WHERE ath_price IS NOT NULL")
        print(f"\n=== Progress: {count_result[0]['count']} tokens with ATH ===\n")

print(f"\n\nProcessing complete!")
print(f"Successful: {successful}")
print(f"Failed: {failed}")

# Final count
final_count = run_query("SELECT COUNT(*) FROM crypto_calls WHERE ath_price IS NOT NULL")
print(f"Total tokens with ATH: {final_count[0]['count']}")