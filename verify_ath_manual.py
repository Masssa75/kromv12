#!/usr/bin/env python3
"""
Manual ATH verification script - mirrors the exact process used in manual testing
"""
import requests
from datetime import datetime
import json
import sys

def fetch_ohlcv(network, pool_address, timeframe, limit=1000, before_timestamp=None):
    """Fetch OHLCV data from GeckoTerminal"""
    url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/{timeframe}"
    params = {'aggregate': 1, 'limit': limit}
    if before_timestamp:
        params['before_timestamp'] = before_timestamp
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if 'data' in data and 'attributes' in data['data']:
            return data['data']['attributes']['ohlcv_list']
        return []
    except Exception as e:
        print(f"Error fetching {timeframe} data: {e}")
        return []

def manual_ath_calculation(token):
    """
    Manually calculate ATH using 3-tier approach
    This is exactly what I've been doing in the terminal
    """
    print(f"\n{'='*60}")
    print(f"🔍 MANUAL ATH VERIFICATION: {token['ticker']}")
    print(f"Group: {token['group']}")
    print(f"Network: {token['network'].upper()}")
    print(f"Entry: ${token['price_at_call']:.12f}")
    print(f"Call: {datetime.fromtimestamp(token['call_timestamp']).strftime('%Y-%m-%d %H:%M UTC')}")
    
    # TIER 1: Daily candles
    print(f"\n📅 TIER 1: Fetching daily candles...")
    daily_candles = fetch_ohlcv(token['network'], token['pool_address'], 'day')
    
    # Filter for after call timestamp
    daily_after_call = []
    for candle in daily_candles:
        if candle[0] >= token['call_timestamp'] and candle[2]:  # has high price
            daily_after_call.append({
                'timestamp': candle[0],
                'date': datetime.fromtimestamp(candle[0]).strftime('%Y-%m-%d'),
                'high': float(candle[2])
            })
    
    if not daily_after_call:
        print("❌ No data after call date")
        return None
    
    # Find highest daily
    daily_ath = max(daily_after_call, key=lambda x: x['high'])
    print(f"   Daily ATH: ${daily_ath['high']:.12f} on {daily_ath['date']}")
    
    # TIER 2: Hourly candles around ATH day
    print(f"\n🕐 TIER 2: Zooming into hourly candles...")
    before_ts = daily_ath['timestamp'] + (86400 + 43200)  # 1.5 days after
    hourly_candles = fetch_ohlcv(token['network'], token['pool_address'], 'hour', 
                                 limit=72, before_timestamp=before_ts)
    
    # Filter for around ATH day (±1 day)
    hourly_around_ath = []
    for candle in hourly_candles:
        if abs(candle[0] - daily_ath['timestamp']) <= 86400 and candle[2]:
            hourly_around_ath.append({
                'timestamp': candle[0],
                'datetime': datetime.fromtimestamp(candle[0]).strftime('%Y-%m-%d %H:%M'),
                'high': float(candle[2])
            })
    
    if not hourly_around_ath:
        print("❌ No hourly data available")
        return None
        
    hourly_ath = max(hourly_around_ath, key=lambda x: x['high'])
    print(f"   Hourly ATH: ${hourly_ath['high']:.12f} at {hourly_ath['datetime']}")
    
    # TIER 3: Minute candles around ATH hour
    print(f"\n⏱️  TIER 3: Zooming into minute candles...")
    before_ts = hourly_ath['timestamp'] + 3600  # 1 hour after
    minute_candles = fetch_ohlcv(token['network'], token['pool_address'], 'minute',
                                 limit=120, before_timestamp=before_ts)
    
    # Filter for around ATH hour (±1 hour)
    minute_around_ath = []
    for candle in minute_candles:
        if abs(candle[0] - hourly_ath['timestamp']) <= 3600 and candle[2] and candle[4]:
            minute_around_ath.append({
                'timestamp': candle[0],
                'datetime': datetime.fromtimestamp(candle[0]).strftime('%Y-%m-%d %H:%M'),
                'high': float(candle[2]),
                'close': float(candle[4])
            })
    
    if not minute_around_ath:
        print("❌ No minute data available")
        return None
        
    minute_ath = max(minute_around_ath, key=lambda x: x['high'])
    
    # Calculate ROIs
    ath_high_roi = ((minute_ath['high'] - token['price_at_call']) / token['price_at_call']) * 100
    ath_close_roi = ((minute_ath['close'] - token['price_at_call']) / token['price_at_call']) * 100
    
    print(f"\n✅ FINAL ATH RESULTS:")
    print(f"   Peak Wick: ${minute_ath['high']:.12f} (ROI: {ath_high_roi:,.1f}%)")
    print(f"   Close Price: ${minute_ath['close']:.12f} (ROI: {ath_close_roi:,.1f}%)")
    print(f"   Time: {minute_ath['datetime']}")
    print(f"   Multiplier: {ath_close_roi/100 + 1:.1f}x")
    
    return {
        'ath_price': minute_ath['high'],
        'ath_close': minute_ath['close'],
        'ath_timestamp': minute_ath['timestamp'],
        'ath_datetime': minute_ath['datetime'],
        'ath_roi_percent': ath_high_roi,
        'ath_close_roi_percent': ath_close_roi
    }

# Test tokens
if __name__ == "__main__":
    # Example tokens for testing
    test_tokens = [
        {
            'ticker': 'BOOCHIE',
            'network': 'eth',  # GeckoTerminal uses 'eth' not 'ethereum'
            'group': 'TopCallersChannel',
            'pool_address': '0x9392a42AbE7E8131E0956De4F8A0413f2a0e52BF',
            'call_timestamp': 1747688939,
            'price_at_call': 8E-10
        },
        {
            'ticker': 'GREEN',
            'network': 'solana',
            'group': 'TopCallersChannel',
            'pool_address': 'FFs4EJdWKUYShNi6HBiiiUySLsciScEJXTtnXbiKHuAV',
            'call_timestamp': 1753374556,
            'price_at_call': 0.0001201205
        }
    ]
    
    # Process each token
    for token in test_tokens:
        result = manual_ath_calculation(token)
        if result:
            print(f"\n📊 Stored Result: {json.dumps(result, indent=2)}")