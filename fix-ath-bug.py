#!/usr/bin/env python3
"""Fix ATH calculation bug - include call day in search"""
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

print(f"FIRST Token - Fixed ATH Calculation")
print(f"Call time: {datetime.fromtimestamp(call_timestamp)}")
print("-" * 80)

# Get start of call day (midnight)
call_date = datetime.fromtimestamp(call_timestamp).replace(hour=0, minute=0, second=0, microsecond=0)
call_day_start = int(call_date.timestamp())

print(f"\nCall day starts at: {datetime.fromtimestamp(call_day_start)}")

# Fetch daily OHLCV
url = f"{API_BASE}/networks/{network}/pools/{pool_address}/ohlcv/day"
response = requests.get(url, params={'aggregate': 1, 'limit': 1000}, headers=HEADERS)
daily_data = response.json()
daily_candles = daily_data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])

# FIXED: Include candles from the call day onwards (not just after call timestamp)
daily_from_call_day = [c for c in daily_candles if c[0] >= call_day_start and c[2] > 0]
print(f"\nDaily candles from call day onwards: {len(daily_from_call_day)}")

for candle in daily_from_call_day[:3]:
    dt = datetime.fromtimestamp(candle[0])
    print(f"  {dt.date()}: High=${candle[2]:.10f}")

if daily_from_call_day:
    daily_ath = max(daily_from_call_day, key=lambda x: x[2])
    dt = datetime.fromtimestamp(daily_ath[0])
    print(f"\nDaily ATH (including call day): {dt.date()} - High: ${daily_ath[2]:.10f}")
    
    # Now get hourly data around this day
    before_ts = daily_ath[0] + (86400 + 43200)
    url = f"{API_BASE}/networks/{network}/pools/{pool_address}/ohlcv/hour"
    response = requests.get(url, params={'aggregate': 1, 'limit': 72, 'before_timestamp': before_ts}, headers=HEADERS)
    hourly_data = response.json()
    hourly_candles = hourly_data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
    
    # Get hourly candles around the daily ATH
    hourly_around = [c for c in hourly_candles if abs(c[0] - daily_ath[0]) <= 86400 and c[2] > 0]
    
    # FIXED: Only consider hourly candles AFTER the call timestamp
    hourly_after_call = [c for c in hourly_around if c[0] >= call_timestamp]
    print(f"\nHourly candles after call on ATH day: {len(hourly_after_call)}")
    
    if hourly_after_call:
        hourly_ath = max(hourly_after_call, key=lambda x: x[2])
        dt = datetime.fromtimestamp(hourly_ath[0])
        print(f"Hourly ATH: {dt} - High: ${hourly_ath[2]:.10f}")
        
        # Get minute data
        minute_before = hourly_ath[0] + 3600
        url = f"{API_BASE}/networks/{network}/pools/{pool_address}/ohlcv/minute"
        response = requests.get(url, params={'aggregate': 1, 'limit': 120, 'before_timestamp': minute_before}, headers=HEADERS)
        minute_data = response.json()
        minute_candles = minute_data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
        
        minute_around = [c for c in minute_candles if abs(c[0] - hourly_ath[0]) <= 3600 and c[2] > 0]
        
        if minute_around:
            minute_ath = max(minute_around, key=lambda x: x[2])
            dt = datetime.fromtimestamp(minute_ath[0])
            
            ath_price = max(minute_ath[1], minute_ath[4])  # max(open, close)
            roi = ((ath_price - price_at_call) / price_at_call) * 100
            
            print(f"\n✅ FINAL ATH RESULT:")
            print(f"   Time: {dt}")
            print(f"   ATH Price: ${ath_price:.10f}")
            print(f"   ROI: {roi:.1f}%")

print("\n" + "-" * 80)
print("FIX: The algorithm should look at daily candles from the START of the call day,")
print("not from the exact call timestamp, to avoid missing intraday peaks.")