#!/usr/bin/env python3
"""Debug COOL token ATH calculation"""
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
price_at_call = 0.0001088793
call_timestamp = 1753723963  # July 29, 2025

print(f"COOL Token ATH Debug")
print(f"Pool: {pool_address}")
print(f"Entry price: ${price_at_call:.10f}")
print(f"Call timestamp: {call_timestamp} ({datetime.fromtimestamp(call_timestamp)})")
print("-" * 80)

# Fetch daily OHLCV
print("\nFetching daily OHLCV data...")
url = f"{API_BASE}/networks/{network}/pools/{pool_address}/ohlcv/day"
response = requests.get(url, params={'aggregate': 1, 'limit': 1000}, headers=HEADERS)

if response.status_code != 200:
    print(f"Error: {response.status_code} - {response.text}")
    exit(1)

data = response.json()
candles = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
print(f"Got {len(candles)} daily candles")

# Find candles after call
candles_after_call = [c for c in candles if c[0] >= call_timestamp]
print(f"Candles after call: {len(candles_after_call)}")

if not candles_after_call:
    print("No candles found after call timestamp!")
    # Let's check all candles
    print("\nShowing last 10 candles:")
    for candle in candles[-10:]:
        dt = datetime.fromtimestamp(candle[0])
        print(f"  {dt}: O=${candle[1]:.10f} H=${candle[2]:.10f} L=${candle[3]:.10f} C=${candle[4]:.10f}")
else:
    # Find highest
    highest = max(candles_after_call, key=lambda x: x[2])  # x[2] is high
    dt = datetime.fromtimestamp(highest[0])
    print(f"\nHighest daily candle:")
    print(f"  Date: {dt}")
    print(f"  High: ${highest[2]:.10f}")
    print(f"  ROI: {((highest[2] - price_at_call) / price_at_call * 100):.1f}%")

print("\n" + "-" * 80)
print("Issue found: The call timestamp is in the future (July 29, 2025)!")
print("The OHLCV data likely doesn't extend that far into the future.")
print("This is causing the ATH calculation to fail or return incorrect results.")