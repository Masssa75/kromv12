#!/usr/bin/env python3
"""Debug script to investigate COMPANY token ATH calculation issue"""

import os
import sys
import json
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

# GeckoTerminal API
GECKO_API_KEY = os.getenv("GECKO_TERMINAL_API_KEY")
COINGECKO_PRO_API_BASE = "https://pro-api.coingecko.com/api/v3/onchain"

def fetch_ohlcv(network, pool_address, timeframe, limit=1000, before_timestamp=None):
    """Fetch OHLCV data from GeckoTerminal"""
    url = f"{COINGECKO_PRO_API_BASE}/networks/{network}/pools/{pool_address}/ohlcv/{timeframe}"
    
    params = {
        "aggregate": "1",
        "limit": str(limit)
    }
    if before_timestamp:
        params["before_timestamp"] = str(before_timestamp)
    
    headers = {}
    if GECKO_API_KEY and GECKO_API_KEY.startswith('CG-'):
        headers['x-cg-pro-api-key'] = GECKO_API_KEY
    
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        print(f"API Error: {response.status_code} - {response.text}")
        return []
    
    data = response.json()
    ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
    
    candles = []
    for candle in ohlcv_list:
        candles.append({
            'timestamp': candle[0],
            'open': candle[1] or 0,
            'high': candle[2] or 0,
            'low': candle[3] or 0,
            'close': candle[4] or 0,
            'volume': candle[5] or 0
        })
    
    return candles

def main():
    # Search for COMPANY tokens
    print("Searching for COMPANY tokens in database...")
    
    response = supabase.table('crypto_calls').select('*').eq('ticker', 'COMPANY').execute()
    
    if not response.data:
        print("No COMPANY tokens found")
        return
    
    print(f"\nFound {len(response.data)} COMPANY tokens:")
    
    for i, token in enumerate(response.data):
        print(f"\n[{i+1}] Contract: {token['contract_address']}")
        print(f"    Created: {token['created_at']}")
        print(f"    Buy Time: {token['buy_timestamp'] or 'N/A'}")
        print(f"    Price at Call: ${token['price_at_call']}")
        print(f"    ATH Price: ${token['ath_price']}")
        print(f"    ATH Time: {token['ath_timestamp']}")
        print(f"    ATH ROI: {token['ath_roi_percent']}%")
    
    # Focus on the token that matches the screenshot
    # Looking for the one with ATH ROI around 73193%
    target_token = None
    for token in response.data:
        if token['ath_roi_percent'] and abs(token['ath_roi_percent'] - 73193) < 100:
            target_token = token
            break
    
    if not target_token:
        print("\nCouldn't find the specific token from the screenshot")
        return
    
    print(f"\n{'='*60}")
    print(f"INVESTIGATING TOKEN: {target_token['ticker']}")
    print(f"Contract: {target_token['contract_address']}")
    print(f"{'='*60}")
    
    # Determine call timestamp
    call_timestamp = None
    if target_token['buy_timestamp']:
        call_timestamp = datetime.fromisoformat(target_token['buy_timestamp'].replace('Z', '+00:00')).timestamp()
    elif target_token['raw_data'] and 'timestamp' in target_token['raw_data']:
        call_timestamp = target_token['raw_data']['timestamp']
    
    if not call_timestamp:
        print("ERROR: No valid timestamp found")
        return
    
    call_datetime = datetime.fromtimestamp(call_timestamp, tz=timezone.utc)
    print(f"\nCall Time: {call_datetime.isoformat()}")
    print(f"Price at Call: ${target_token['price_at_call']}")
    
    # Debug: Show all timestamp sources
    print(f"\nDEBUG - Timestamp sources:")
    print(f"  buy_timestamp: {target_token['buy_timestamp']}")
    print(f"  raw_data.timestamp: {target_token['raw_data'].get('timestamp') if target_token['raw_data'] else 'N/A'}")
    print(f"  created_at: {target_token['created_at']}")
    print(f"  Calculated call_timestamp: {call_timestamp}")
    
    # Get the start of the call day (midnight)
    call_day_start = call_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
    print(f"Call Day Start: {call_day_start.isoformat()}")
    
    # Fetch minute data for the entire call day
    print(f"\nFetching minute data for the call day...")
    
    if not target_token['pool_address']:
        print("ERROR: No pool address found")
        return
    
    network = target_token['network']
    if network == 'ethereum':
        network = 'eth'
    
    # Fetch 24 hours of minute data from the start of the call day
    end_of_day = call_day_start.timestamp() + 86400  # 24 hours later
    minute_data = fetch_ohlcv(network, target_token['pool_address'], 'minute', 1000, int(end_of_day))
    
    if not minute_data:
        print("No minute data retrieved")
        return
    
    print(f"Retrieved {len(minute_data)} minute candles")
    
    # Find candles before the call
    pre_call_candles = []
    post_call_candles = []
    
    for candle in minute_data:
        candle_time = datetime.fromtimestamp(candle['timestamp'], tz=timezone.utc)
        if candle['timestamp'] < call_timestamp:
            pre_call_candles.append(candle)
        else:
            post_call_candles.append(candle)
    
    print(f"\nCandles before call: {len(pre_call_candles)}")
    print(f"Candles after call: {len(post_call_candles)}")
    
    # Find the highest price before the call
    if pre_call_candles:
        pre_call_high = max(pre_call_candles, key=lambda x: x['high'])
        pre_call_time = datetime.fromtimestamp(pre_call_high['timestamp'], tz=timezone.utc)
        print(f"\nHighest price BEFORE call:")
        print(f"  Time: {pre_call_time.isoformat()}")
        print(f"  High: ${pre_call_high['high']}")
        print(f"  Open: ${pre_call_high['open']}")
        print(f"  Close: ${pre_call_high['close']}")
    
    # Find the highest price after the call
    if post_call_candles:
        post_call_high = max(post_call_candles, key=lambda x: x['high'])
        post_call_time = datetime.fromtimestamp(post_call_high['timestamp'], tz=timezone.utc)
        print(f"\nHighest price AFTER call:")
        print(f"  Time: {post_call_time.isoformat()}")
        print(f"  High: ${post_call_high['high']}")
        print(f"  Open: ${post_call_high['open']}")
        print(f"  Close: ${post_call_high['close']}")
        
        # Calculate correct ROI
        best_price = max(post_call_high['open'], post_call_high['close'])
        correct_roi = ((best_price - target_token['price_at_call']) / target_token['price_at_call']) * 100
        print(f"\nCorrect ATH calculation:")
        print(f"  Best Price (max of open/close): ${best_price}")
        print(f"  Correct ROI: {correct_roi:.2f}%")
        print(f"  Current DB ROI: {target_token['ath_roi_percent']}%")
    
    # Show some candles around the call time
    print(f"\n{'='*60}")
    print("CANDLES AROUND CALL TIME:")
    print(f"{'='*60}")
    
    around_call = [c for c in minute_data if abs(c['timestamp'] - call_timestamp) < 3600]  # Within 1 hour
    around_call.sort(key=lambda x: x['timestamp'])
    
    for candle in around_call[:10]:  # Show first 10
        candle_time = datetime.fromtimestamp(candle['timestamp'], tz=timezone.utc)
        is_before = "BEFORE" if candle['timestamp'] < call_timestamp else "AFTER"
        print(f"{candle_time.isoformat()} [{is_before}] - High: ${candle['high']:.6f}, Open: ${candle['open']:.6f}, Close: ${candle['close']:.6f}")
    
    # SIMULATE EDGE FUNCTION LOGIC
    print(f"\n{'='*60}")
    print("SIMULATING EDGE FUNCTION LOGIC:")
    print(f"{'='*60}")
    
    # Step 1: Fetch daily candles
    print("\nStep 1: Fetching daily candles...")
    daily_data = fetch_ohlcv(network, target_token['pool_address'], 'day', 1000)
    
    # Filter daily candles from call day start
    daily_after_call = [c for c in daily_data if c['timestamp'] >= call_day_start.timestamp() and c['high'] > 0]
    daily_after_call.sort(key=lambda x: x['high'], reverse=True)
    
    if daily_after_call:
        daily_ath = daily_after_call[0]
        daily_ath_time = datetime.fromtimestamp(daily_ath['timestamp'], tz=timezone.utc)
        print(f"Daily ATH: ${daily_ath['high']} on {daily_ath_time.isoformat()}")
        print(f"Daily candle details - Open: ${daily_ath['open']}, Close: ${daily_ath['close']}")
        
        # Check if this daily candle includes pre-call time
        daily_start = datetime.fromtimestamp(daily_ath['timestamp'], tz=timezone.utc)
        daily_end = daily_start.replace(hour=23, minute=59, second=59)
        print(f"Daily candle covers: {daily_start.isoformat()} to {daily_end.isoformat()}")
        print(f"Call was at: {call_datetime.isoformat()}")
        
        if daily_start <= call_datetime <= daily_end:
            print("WARNING: Daily ATH candle includes the call time!")

if __name__ == "__main__":
    main()