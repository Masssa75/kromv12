#!/usr/bin/env python3
"""
Verify ATH calculation by manually fetching OHLCV data from GeckoTerminal
"""
import requests
import sys
from datetime import datetime

def verify_token_ath(network, pool_address, entry_price, entry_timestamp=None):
    """Manually verify ATH calculation for a token"""
    
    # Fetch daily OHLCV
    daily_url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/day?aggregate=1&limit=1000"
    
    print(f"Fetching daily OHLCV data...")
    response = requests.get(daily_url)
    
    if response.status_code != 200:
        print(f"Error: API returned {response.status_code}")
        return
    
    data = response.json()
    ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
    
    if not ohlcv_list:
        print("No OHLCV data found")
        return
    
    # Find highest price after entry
    entry_ts = entry_timestamp or 0
    highest_price = 0
    highest_date = None
    
    for candle in ohlcv_list:
        timestamp = candle[0]
        high = candle[2]
        
        if timestamp >= entry_ts and high > highest_price:
            highest_price = high
            highest_date = datetime.fromtimestamp(timestamp)
    
    if highest_price > 0:
        roi = ((highest_price - entry_price) / entry_price) * 100
        print(f"\nResults:")
        print(f"Entry Price: ${entry_price:.8f}")
        print(f"ATH Price: ${highest_price:.8f}")
        print(f"ATH Date: {highest_date}")
        print(f"ROI: {roi:.2f}%")
    else:
        print("No price data found after entry")

if __name__ == "__main__":
    # Example: VIRAL token
    verify_token_ath(
        network="solana",
        pool_address="4wpVnSwRJzUDXgQaUM3xZfnJSdYfQiiQXgPTiPb7kLm5",
        entry_price=0.0024224336
    )