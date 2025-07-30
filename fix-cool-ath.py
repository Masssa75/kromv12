#!/usr/bin/env python3
"""Fix COOL token ATH by using all available data"""
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration
GECKO_API_KEY = os.getenv("GECKO_TERMINAL_API_KEY", "CG-rNYcUB85FxH1tZqqRmU5H8eY")
API_BASE = "https://pro-api.coingecko.com/api/v3/onchain"
HEADERS = {"x-cg-pro-api-key": GECKO_API_KEY}

# Token details
pool_address = "0xC42625e59C6A5cA6a608f43E55F4744e4a9710FB"
network = "eth"
price_at_call = 0.0000597244  # Using the earlier call price

print(f"COOL Token ATH Analysis (Using ALL historical data)")
print(f"Pool: {pool_address}")
print(f"Entry price: ${price_at_call:.10f}")
print("-" * 80)

# Fetch daily OHLCV
print("\nFetching ALL daily OHLCV data...")
url = f"{API_BASE}/networks/{network}/pools/{pool_address}/ohlcv/day"
response = requests.get(url, params={'aggregate': 1, 'limit': 1000}, headers=HEADERS)

if response.status_code != 200:
    print(f"Error: {response.status_code}")
    exit(1)

data = response.json()
candles = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
print(f"Got {len(candles)} daily candles")

# Find absolute highest
if candles:
    highest = max(candles, key=lambda x: x[2])  # x[2] is high
    dt = datetime.fromtimestamp(highest[0])
    print(f"\nHighest daily candle (ALL TIME):")
    print(f"  Date: {dt}")
    print(f"  High: ${highest[2]:.10f}")
    print(f"  Open: ${highest[1]:.10f}")
    print(f"  Close: ${highest[4]:.10f}")
    print(f"  ROI from entry: {((highest[2] - price_at_call) / price_at_call * 100):.1f}%")
    
    # Get hourly around this date
    print(f"\nFetching hourly data around {dt.date()}...")
    before_ts = highest[0] + (86400 + 43200)  # 1.5 days after
    url = f"{API_BASE}/networks/{network}/pools/{pool_address}/ohlcv/hour"
    response = requests.get(url, params={'aggregate': 1, 'limit': 72, 'before_timestamp': before_ts}, headers=HEADERS)
    
    if response.status_code == 200:
        hourly_data = response.json()
        hourly_candles = hourly_data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
        
        # Find candles around the daily ATH
        hourly_around = [c for c in hourly_candles 
                        if abs(c[0] - highest[0]) <= 86400 and c[2] > 0]
        
        if hourly_around:
            hourly_highest = max(hourly_around, key=lambda x: x[2])
            hdt = datetime.fromtimestamp(hourly_highest[0])
            print(f"\nHighest hourly candle:")
            print(f"  Time: {hdt}")
            print(f"  High: ${hourly_highest[2]:.10f}")
            
            # Get minute data
            print(f"\nFetching minute data around {hdt}...")
            minute_before = hourly_highest[0] + 3600
            url = f"{API_BASE}/networks/{network}/pools/{pool_address}/ohlcv/minute"
            response = requests.get(url, params={'aggregate': 1, 'limit': 120, 'before_timestamp': minute_before}, headers=HEADERS)
            
            if response.status_code == 200:
                minute_data = response.json()
                minute_candles = minute_data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
                
                minute_around = [c for c in minute_candles 
                               if abs(c[0] - hourly_highest[0]) <= 3600 and c[2] > 0]
                
                if minute_around:
                    minute_highest = max(minute_around, key=lambda x: x[2])
                    mdt = datetime.fromtimestamp(minute_highest[0])
                    
                    print(f"\nHighest minute candle:")
                    print(f"  Time: {mdt}")
                    print(f"  High (wick): ${minute_highest[2]:.10f}")
                    print(f"  Open: ${minute_highest[1]:.10f}")
                    print(f"  Close: ${minute_highest[4]:.10f}")
                    
                    # Use max(open, close) as per our methodology
                    realistic_ath = max(minute_highest[1], minute_highest[4])
                    print(f"\n✅ REALISTIC ATH: ${realistic_ath:.10f}")
                    print(f"   ROI: {((realistic_ath - price_at_call) / price_at_call * 100):.1f}%")

print("\n" + "-" * 80)
print("RECOMMENDATION: The ATH calculation should use created_at timestamp")
print("instead of the raw_data timestamp to avoid future date issues.")