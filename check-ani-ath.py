#!/usr/bin/env python3
import requests
import json
from datetime import datetime

# ANI token details from database
POOL_ADDRESS = "8ujpQXxnnWvRohU2oCe3eaSzoL7paU2uj3fEn4Zp72US"
NETWORK = "solana"
PRICE_AT_CALL = 0.0003777616
CALL_TIMESTAMP = "2025-07-14T10:39:03.5257+00:00"

print(f"Checking ATH for ANI token on Solana")
print(f"Pool address: {POOL_ADDRESS}")
print(f"Price at call: ${PRICE_AT_CALL:.8f}")
print(f"Call timestamp: {CALL_TIMESTAMP}")
print("-" * 60)

# Fetch daily OHLCV data from GeckoTerminal
url = f"https://api.geckoterminal.com/api/v2/networks/{NETWORK}/pools/{POOL_ADDRESS}/ohlcv/day"
params = {
    "aggregate": 1,
    "limit": 1000,
    "currency": "usd"
}

response = requests.get(url, params=params)
if response.status_code != 200:
    print(f"Error fetching data: {response.status_code}")
    exit(1)

data = response.json()
ohlcv_list = data.get("data", {}).get("attributes", {}).get("ohlcv_list", [])

if not ohlcv_list:
    print("No OHLCV data found")
    exit(1)

# Convert call timestamp to unix timestamp
# Handle the microseconds properly
call_str = CALL_TIMESTAMP.replace("+00:00", "").split(".")[0]  # Remove microseconds and timezone
call_dt = datetime.strptime(call_str, "%Y-%m-%dT%H:%M:%S")
call_unix = int(call_dt.timestamp())

print(f"Call Unix timestamp: {call_unix}")
print(f"Analyzing {len(ohlcv_list)} daily candles...")
print("-" * 60)

# Find ATH after call
max_high = 0
max_date = None
max_candle = None

for candle in ohlcv_list:
    timestamp, open_price, high, low, close, volume = candle
    
    # Only consider candles after the call
    if timestamp >= call_unix and high > max_high:
        max_high = high
        max_date = datetime.fromtimestamp(timestamp)
        max_candle = candle

if max_candle:
    roi = ((max_high - PRICE_AT_CALL) / PRICE_AT_CALL) * 100
    
    print(f"DAILY ATH FOUND:")
    print(f"  Date: {max_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  High: ${max_high:.8f}")
    print(f"  ROI: {roi:.2f}%")
    print(f"  Full candle: {max_candle}")
    print()
    
    # Now check hourly data around that date for more precision
    print("Fetching hourly data around ATH day...")
    hour_url = f"https://api.geckoterminal.com/api/v2/networks/{NETWORK}/pools/{POOL_ADDRESS}/ohlcv/hour"
    
    # Get timestamp for fetching hourly data (1.5 days after ATH)
    before_ts = max_candle[0] + (86400 + 43200)
    
    hour_params = {
        "aggregate": 1,
        "limit": 72,
        "before_timestamp": before_ts,
        "currency": "usd"
    }
    
    hour_response = requests.get(hour_url, params=hour_params)
    if hour_response.status_code == 200:
        hour_data = hour_response.json()
        hour_list = hour_data.get("data", {}).get("attributes", {}).get("ohlcv_list", [])
        
        # Find hourly ATH around the daily ATH
        hour_max = 0
        hour_date = None
        for candle in hour_list:
            timestamp, open_price, high, low, close, volume = candle
            # Within 24 hours of daily ATH
            if abs(timestamp - max_candle[0]) <= 86400 and high > hour_max:
                hour_max = high
                hour_date = datetime.fromtimestamp(timestamp)
        
        if hour_max > 0:
            hour_roi = ((hour_max - PRICE_AT_CALL) / PRICE_AT_CALL) * 100
            print(f"HOURLY ATH FOUND:")
            print(f"  Date: {hour_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  High: ${hour_max:.8f}")
            print(f"  ROI: {hour_roi:.2f}%")
            
            # Compare with current database value
            print()
            print("-" * 60)
            print("COMPARISON:")
            print(f"  Current DB ATH: $0.03003 (7849.46% ROI)")
            print(f"  Calculated ATH: ${hour_max:.8f} ({hour_roi:.2f}% ROI)")
            
            if hour_max > 0.03003:
                print(f"  ⚠️ ACTUAL ATH IS HIGHER by ${hour_max - 0.03003:.8f}")
            else:
                print(f"  ✓ Current DB ATH matches or exceeds calculated")
else:
    print("No ATH found after call date")