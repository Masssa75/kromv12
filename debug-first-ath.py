#!/usr/bin/env python3
"""Debug FIRST token ATH calculation"""
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
pool_address = "HWqsR2EZdnr6xptXNA43uK6UQ7FAApgpZUyWCo9w1tP1"
network = "solana"
price_at_call = 0.0000497015
created_at = "2025-07-29 02:36:02.863981+00"
raw_timestamp = 1753756555  # From raw_data

print(f"FIRST Token ATH Debug")
print(f"Pool: {pool_address}")
print(f"Entry price: ${price_at_call:.10f}")
print(f"Created at: {created_at}")
print(f"Raw timestamp: {raw_timestamp} ({datetime.fromtimestamp(raw_timestamp)})")
print("-" * 80)

# Use created_at timestamp since it's more reliable
call_timestamp = int(datetime.fromisoformat(created_at.replace('+00', '+00:00')).timestamp())
print(f"Using created_at timestamp: {call_timestamp} ({datetime.fromtimestamp(call_timestamp)})")

# Fetch daily OHLCV
print("\nFetching daily OHLCV data...")
url = f"{API_BASE}/networks/{network}/pools/{pool_address}/ohlcv/day"
response = requests.get(url, params={'aggregate': 1, 'limit': 100}, headers=HEADERS)

if response.status_code != 200:
    print(f"Error: {response.status_code} - {response.text}")
    exit(1)

data = response.json()
candles = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
print(f"Got {len(candles)} daily candles")

# Show ALL candles to understand the data
print("\nALL daily candles:")
for i, candle in enumerate(candles):
    dt = datetime.fromtimestamp(candle[0])
    print(f"{i}: {dt}: O=${candle[1]:.10f} H=${candle[2]:.10f} L=${candle[3]:.10f} C=${candle[4]:.10f}")

# Find candles after call
candles_after_call = [c for c in candles if c[0] >= call_timestamp]
print(f"\nCandles after call ({datetime.fromtimestamp(call_timestamp)}): {len(candles_after_call)}")

if candles_after_call:
    for candle in candles_after_call[:5]:  # Show first 5
        dt = datetime.fromtimestamp(candle[0])
        print(f"  {dt}: H=${candle[2]:.10f}")
    
    highest = max(candles_after_call, key=lambda x: x[2])
    dt = datetime.fromtimestamp(highest[0])
    print(f"\nHighest daily after call:")
    print(f"  Date: {dt}")
    print(f"  High: ${highest[2]:.10f}")
    print(f"  Expected ROI: {((highest[2] - price_at_call) / price_at_call * 100):.1f}%")

# Now fetch hourly data for the day of the call
print(f"\nFetching hourly data for call day...")
url = f"{API_BASE}/networks/{network}/pools/{pool_address}/ohlcv/hour"
# Get 48 hours of data
response = requests.get(url, params={'aggregate': 1, 'limit': 48, 'before_timestamp': call_timestamp + 172800}, headers=HEADERS)

if response.status_code == 200:
    data = response.json()
    hourly_candles = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
    
    hourly_after_call = [c for c in hourly_candles if c[0] >= call_timestamp]
    print(f"Hourly candles after call: {len(hourly_after_call)}")
    
    if hourly_after_call:
        # Show first 10 hourly candles after call
        print("\nFirst 10 hourly candles after call:")
        for candle in hourly_after_call[:10]:
            dt = datetime.fromtimestamp(candle[0])
            print(f"  {dt}: H=${candle[2]:.10f}")
        
        highest_hourly = max(hourly_after_call, key=lambda x: x[2])
        dt = datetime.fromtimestamp(highest_hourly[0])
        print(f"\nHighest hourly after call:")
        print(f"  Time: {dt}")
        print(f"  High: ${highest_hourly[2]:.10f}")
        print(f"  Expected ROI: {((highest_hourly[2] - price_at_call) / price_at_call * 100):.1f}%")

print("\n" + "-" * 80)
print("ANALYSIS: Checking why ATH calculation returned wrong value...")