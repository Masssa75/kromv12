#!/usr/bin/env python3
"""Debug FIRST token - find exact ATH timing"""
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
call_timestamp = 1753756562  # 2025-07-29 09:36:02

print(f"FIRST Token - Finding exact ATH")
print(f"Call time: {datetime.fromtimestamp(call_timestamp)}")
print("-" * 80)

# The hourly data showed peak at 2025-07-29 18:00:00
# Let's get minute data around that time
peak_hour_ts = int(datetime(2025, 7, 29, 18, 0, 0).timestamp())

print(f"\nFetching minute data around peak hour ({datetime.fromtimestamp(peak_hour_ts)})...")
url = f"{API_BASE}/networks/{network}/pools/{pool_address}/ohlcv/minute"
# Get 2 hours of minute data around the peak
response = requests.get(url, params={'aggregate': 1, 'limit': 120, 'before_timestamp': peak_hour_ts + 3600}, headers=HEADERS)

if response.status_code == 200:
    data = response.json()
    minute_candles = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
    
    # Find candles around the peak hour
    peak_candles = [c for c in minute_candles if abs(c[0] - peak_hour_ts) <= 3600]
    
    if peak_candles:
        highest_minute = max(peak_candles, key=lambda x: x[2])
        dt = datetime.fromtimestamp(highest_minute[0])
        
        print(f"\nHighest minute candle found:")
        print(f"  Time: {dt}")
        print(f"  High (wick): ${highest_minute[2]:.10f}")
        print(f"  Open: ${highest_minute[1]:.10f}")
        print(f"  Close: ${highest_minute[4]:.10f}")
        print(f"  Max(open,close): ${max(highest_minute[1], highest_minute[4]):.10f}")
        print(f"  ROI from wick: {((highest_minute[2] - price_at_call) / price_at_call * 100):.1f}%")
        print(f"  ROI from max(O,C): {((max(highest_minute[1], highest_minute[4]) - price_at_call) / price_at_call * 100):.1f}%")

# Now let's trace through what our algorithm would have done
print("\n" + "-" * 80)
print("ALGORITHM TRACE:")

# Step 1: Daily
print("\n1. DAILY TIER:")
url = f"{API_BASE}/networks/{network}/pools/{pool_address}/ohlcv/day"
response = requests.get(url, params={'aggregate': 1, 'limit': 1000}, headers=HEADERS)
daily_data = response.json()
daily_candles = daily_data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])

daily_after_call = [c for c in daily_candles if c[0] >= call_timestamp and c[2] > 0]
if daily_after_call:
    daily_ath = max(daily_after_call, key=lambda x: x[2])
    print(f"   Daily ATH: {datetime.fromtimestamp(daily_ath[0]).date()} - High: ${daily_ath[2]:.10f}")
    
    # Step 2: Hourly
    print("\n2. HOURLY TIER:")
    before_ts = daily_ath[0] + (86400 + 43200)  # 1.5 days after
    url = f"{API_BASE}/networks/{network}/pools/{pool_address}/ohlcv/hour"
    response = requests.get(url, params={'aggregate': 1, 'limit': 72, 'before_timestamp': before_ts}, headers=HEADERS)
    hourly_data = response.json()
    hourly_candles = hourly_data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
    
    hourly_around = [c for c in hourly_candles if abs(c[0] - daily_ath[0]) <= 86400 and c[2] > 0]
    print(f"   Hourly candles around daily ATH: {len(hourly_around)}")
    
    if hourly_around:
        # Show what hours we're looking at
        print("   Hours being checked:")
        for h in hourly_around[:5]:
            print(f"     {datetime.fromtimestamp(h[0])}: ${h[2]:.10f}")

print("\n" + "-" * 80)
print("ISSUE IDENTIFIED: The daily candle aggregation may be incorrect or")
print("the algorithm is not finding the right hourly window to search.")