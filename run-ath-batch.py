#!/usr/bin/env python3
"""
Run ATH processing locally to bypass edge function auth issues
"""
import requests
import psycopg2
from datetime import datetime
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
conn = psycopg2.connect(
    host="db.eucfoommxxvqmmwdbkdv.supabase.co",
    database="postgres",
    user="postgres",
    password=os.getenv("SUPABASE_DB_PASSWORD", ""),
    port=5432
)

# GeckoTerminal configuration
GECKO_API_BASE = 'https://pro-api.coingecko.com/api/v3/onchain'
API_KEY = os.getenv("GECKO_TERMINAL_API_KEY")
HEADERS = {'x-cg-pro-api-key': API_KEY} if API_KEY else {}

NETWORK_MAP = {
    'ethereum': 'eth',
    'solana': 'solana',
    'bsc': 'bsc',
    'polygon': 'polygon',
    'arbitrum': 'arbitrum',
    'base': 'base'
}

def fetch_ohlcv(network, pool_address, timeframe, limit=1000, before_timestamp=None):
    """Fetch OHLCV data from GeckoTerminal Pro API"""
    url = f"{GECKO_API_BASE}/networks/{network}/pools/{pool_address}/ohlcv/{timeframe}"
    params = {'aggregate': 1, 'limit': limit}
    if before_timestamp:
        params['before_timestamp'] = before_timestamp
    
    try:
        response = requests.get(url, params=params, headers=HEADERS)
        if response.status_code != 200:
            print(f"API error {response.status_code}: {response.text}")
            return []
        data = response.json()
        if 'data' in data and 'attributes' in data['data']:
            return data['data']['attributes']['ohlcv_list']
        return []
    except Exception as e:
        print(f"Error fetching {timeframe} data: {e}")
        return []

def process_token(token):
    """Process a single token for ATH calculation"""
    try:
        # Get network name for GeckoTerminal
        geckoNetwork = NETWORK_MAP.get(token['network'], token['network'])
        
        # Use buy_timestamp or fall back to raw_data timestamp
        call_timestamp = None
        if token['buy_timestamp']:
            call_timestamp = token['buy_timestamp'].timestamp()
        elif token['raw_data'] and 'timestamp' in token['raw_data']:
            call_timestamp = token['raw_data']['timestamp']
        
        if not call_timestamp:
            print(f"No valid timestamp for {token['ticker']}")
            return None
            
        print(f"\nProcessing {token['ticker']} on {geckoNetwork}")
        print(f"Entry: ${token['price_at_call']:.8f}")
        
        # TIER 1: Daily candles
        daily_data = fetch_ohlcv(geckoNetwork, token['pool_address'], 'day', 1000)
        daily_after_call = [c for c in daily_data if c[0] >= call_timestamp and c[2] > 0]
        
        if not daily_after_call:
            print("No price data after call date")
            return None
            
        daily_ath = max(daily_after_call, key=lambda x: x[2])
        
        # TIER 2: Hourly candles
        before_ts = daily_ath[0] + (86400 + 43200)  # 1.5 days after
        hourly_data = fetch_ohlcv(geckoNetwork, token['pool_address'], 'hour', 72, before_ts)
        
        hourly_around_ath = [c for c in hourly_data 
                            if abs(c[0] - daily_ath[0]) <= 86400 and c[2] > 0]
        
        if not hourly_around_ath:
            # Fallback to daily
            ath_price = daily_ath[2]
            ath_timestamp = daily_ath[0]
        else:
            hourly_ath = max(hourly_around_ath, key=lambda x: x[2])
            
            # TIER 3: Minute candles
            minute_before_ts = hourly_ath[0] + 3600
            minute_data = fetch_ohlcv(geckoNetwork, token['pool_address'], 'minute', 120, minute_before_ts)
            
            minute_around_ath = [c for c in minute_data 
                                if abs(c[0] - hourly_ath[0]) <= 3600 and c[2] > 0 and c[4] > 0]
            
            if minute_around_ath:
                minute_ath = max(minute_around_ath, key=lambda x: x[2])
                # Use max of open/close
                ath_price = max(minute_ath[1], minute_ath[4])
                ath_timestamp = minute_ath[0]
            else:
                ath_price = hourly_ath[2]
                ath_timestamp = hourly_ath[0]
        
        # Calculate ROI
        ath_roi = ((ath_price - token['price_at_call']) / token['price_at_call']) * 100
        ath_roi = max(0, ath_roi)  # Never negative
        
        print(f"ATH: ${ath_price:.8f} (ROI: {ath_roi:.1f}%)")
        
        return {
            'id': token['id'],
            'ath_price': ath_price,
            'ath_timestamp': datetime.fromtimestamp(ath_timestamp),
            'ath_roi_percent': ath_roi
        }
        
    except Exception as e:
        print(f"Error processing {token['ticker']}: {e}")
        return None

# Main processing
print("Starting ATH batch processing...")
print(f"Using API key: {API_KEY[:10]}...")

# Get tokens to process
cur = conn.cursor()
cur.execute("""
    SELECT id, ticker, network, pool_address, buy_timestamp, price_at_call, raw_data
    FROM crypto_calls
    WHERE pool_address IS NOT NULL 
    AND price_at_call IS NOT NULL
    AND ath_price IS NULL
    ORDER BY created_at ASC
    LIMIT 100
""")

tokens = []
for row in cur.fetchall():
    tokens.append({
        'id': row[0],
        'ticker': row[1],
        'network': row[2],
        'pool_address': row[3],
        'buy_timestamp': row[4],
        'price_at_call': float(row[5]),
        'raw_data': row[6]
    })

print(f"Found {len(tokens)} tokens to process")

# Process tokens
successful = 0
failed = 0

for i, token in enumerate(tokens):
    print(f"\n[{i+1}/{len(tokens)}] Processing {token['ticker']}...")
    
    result = process_token(token)
    
    if result:
        # Update database
        cur.execute("""
            UPDATE crypto_calls 
            SET ath_price = %s, ath_timestamp = %s, ath_roi_percent = %s
            WHERE id = %s
        """, (result['ath_price'], result['ath_timestamp'], result['ath_roi_percent'], result['id']))
        conn.commit()
        successful += 1
    else:
        failed += 1
    
    # Rate limiting (0.5 seconds between tokens for Pro API)
    time.sleep(0.5)

print(f"\n\nProcessing complete!")
print(f"Successful: {successful}")
print(f"Failed: {failed}")

cur.close()
conn.close()