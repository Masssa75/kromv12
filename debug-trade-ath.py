#!/usr/bin/env python3
"""Debug ATH calculation for TRADE token"""
import requests
import time
from datetime import datetime
import os

# Configuration
MANAGEMENT_TOKEN = "sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7"
PROJECT_REF = "eucfoommxxvqmmwdbkdv"
GECKO_API_KEY = os.getenv("GECKO_TERMINAL_API_KEY", "CG-rNYcUB85FxH1tZqqRmU5H8eY")
API_BASE = "https://pro-api.coingecko.com/api/v3/onchain"
HEADERS = {"x-cg-pro-api-key": GECKO_API_KEY}

def run_query(query):
    """Execute query"""
    try:
        response = requests.post(
            f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
            headers={"Authorization": f"Bearer {MANAGEMENT_TOKEN}", "Content-Type": "application/json"},
            json={"query": query},
            timeout=10
        )
        return response.json()
    except Exception as e:
        print(f"Query error: {e}")
        return []

def fetch_ohlcv(network, pool, timeframe, limit=1000, before_timestamp=None):
    """Fetch OHLCV data"""
    url = f"{API_BASE}/networks/{network}/pools/{pool}/ohlcv/{timeframe}"
    params = {'aggregate': 1, 'limit': limit}
    if before_timestamp:
        params['before_timestamp'] = before_timestamp
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            print(f"API error {response.status_code}: {response.text}")
            return []
        
        data = response.json()
        return data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
    except Exception as e:
        print(f"API error: {e}")
        return []

# Get TRADE token data
print("Fetching TRADE token data...")
# Get the hyperevm TRADE token
trade_query = """
SELECT id, ticker, network, pool_address, buy_timestamp, price_at_call, 
       ath_price, ath_timestamp, ath_roi_percent, created_at, raw_data,
       contract_address
FROM crypto_calls
WHERE id = '9a7efa22-d73d-4e12-b67d-d9e8a075740a'
"""

trade_data = run_query(trade_query)
if not trade_data:
    print("TRADE token not found!")
    exit(1)

token = trade_data[0]
print(f"\nTRADE Token Details:")
print(f"  Contract: {token['contract_address']}")
print(f"  Network: {token['network']}")
print(f"  Pool: {token['pool_address']}")
print(f"  Call Time: {token['buy_timestamp'] or token['created_at']}")
print(f"  Entry Price: ${token['price_at_call']}")
print(f"  Current ATH Price: ${token['ath_price']}")
print(f"  Current ATH ROI: {token['ath_roi_percent']}%")
print(f"  ATH Timestamp: {token['ath_timestamp']}")

# Map network name
network = token['network']
if network == 'hyperevm':
    # HyperEVM is still Ethereum-based
    network = 'eth'
print(f"\nUsing network: {network} for API calls")

# Convert timestamps
if token['buy_timestamp']:
    call_ts = int(datetime.fromisoformat(token['buy_timestamp'].replace('Z', '+00:00')).timestamp())
else:
    # Use created_at if buy_timestamp is None
    # Handle PostgreSQL timestamp format
    created_at_str = token['created_at'].replace(' ', 'T')
    if not created_at_str.endswith('+00:00'):
        created_at_str = created_at_str.replace('+00', '+00:00')
    call_ts = int(datetime.fromisoformat(created_at_str).timestamp())
call_date = datetime.fromtimestamp(call_ts)
call_day_start = call_date.replace(hour=0, minute=0, second=0, microsecond=0)
call_day_start_ts = int(call_day_start.timestamp())

print(f"\nCall timestamp: {call_ts} ({call_date})")
print(f"Call day start: {call_day_start_ts} ({call_day_start})")

# TIER 1: Get daily candles from call day
print(f"\nFetching daily OHLCV data...")
daily_data = fetch_ohlcv(network, token['pool_address'], 'day', 1000)
print(f"Got {len(daily_data)} daily candles")

# Filter for candles from call day onwards
daily_from_call = [c for c in daily_data if c[0] >= call_day_start_ts and c[2] > 0]
print(f"Found {len(daily_from_call)} daily candles from call day onwards")

if daily_from_call:
    # Find the daily ATH
    daily_ath = max(daily_from_call, key=lambda x: x[2])
    daily_ath_date = datetime.fromtimestamp(daily_ath[0])
    print(f"\nDaily ATH found:")
    print(f"  Date: {daily_ath_date}")
    print(f"  High: ${daily_ath[2]:.8f}")
    print(f"  Open: ${daily_ath[1]:.8f}")
    print(f"  Close: ${daily_ath[4]:.8f}")
    
    # Check if this is the same day as the call
    if daily_ath[0] == call_day_start_ts:
        print(f"\n⚠️  ATH is on the SAME DAY as the call!")
        print(f"  This could miss intraday pumps before the call time")
    
    # TIER 2: Get hourly data around the ATH day
    print(f"\nFetching hourly data around ATH day...")
    before_ts = daily_ath[0] + (86400 + 43200)  # 1.5 days after
    hourly_data = fetch_ohlcv(network, token['pool_address'], 'hour', 72, before_ts)
    
    hourly_around_ath = [c for c in hourly_data 
                        if abs(c[0] - daily_ath[0]) <= 86400 and c[2] > 0]
    print(f"Found {len(hourly_around_ath)} hourly candles around ATH day")
    
    if hourly_around_ath:
        hourly_ath = max(hourly_around_ath, key=lambda x: x[2])
        hourly_ath_time = datetime.fromtimestamp(hourly_ath[0])
        print(f"\nHourly ATH:")
        print(f"  Time: {hourly_ath_time}")
        print(f"  High: ${hourly_ath[2]:.8f}")
        
        # TIER 3: Get minute data
        print(f"\nFetching minute data around hourly ATH...")
        minute_before_ts = hourly_ath[0] + 3600
        minute_data = fetch_ohlcv(network, token['pool_address'], 'minute', 120, minute_before_ts)
        
        # Check minutes AFTER the call
        minute_after_call = [c for c in minute_data 
                            if c[0] >= call_ts and c[2] > 0 and c[4] > 0]
        print(f"Found {len(minute_after_call)} minute candles after call time")
        
        # Also check minutes around the hourly ATH
        minute_around_ath = [c for c in minute_data 
                            if abs(c[0] - hourly_ath[0]) <= 3600 
                            and c[0] >= call_ts
                            and c[2] > 0 and c[4] > 0]
        print(f"Found {len(minute_around_ath)} minute candles around hourly ATH and after call")
        
        if minute_around_ath:
            minute_ath = max(minute_around_ath, key=lambda x: x[2])
            minute_ath_time = datetime.fromtimestamp(minute_ath[0])
            realistic_ath = max(minute_ath[1], minute_ath[4])  # max(open, close)
            
            print(f"\nMinute ATH:")
            print(f"  Time: {minute_ath_time}")
            print(f"  High (wick): ${minute_ath[2]:.8f}")
            print(f"  Open: ${minute_ath[1]:.8f}")
            print(f"  Close: ${minute_ath[4]:.8f}")
            print(f"  Realistic ATH (max of open/close): ${realistic_ath:.8f}")
            
            # Calculate ROI
            entry_price = float(token['price_at_call'])
            roi = max(0, ((realistic_ath - entry_price) / entry_price) * 100)
            
            print(f"\nCalculated ATH ROI: {roi:.1f}%")
            print(f"Current DB ATH ROI: {token['ath_roi_percent']}%")
            
            if abs(roi - float(token['ath_roi_percent'])) > 1:
                print(f"\n⚠️  MISMATCH: Calculated ROI differs from DB!")

# Now let's also check what the chart shows around the call time
print(f"\n\nChecking price action immediately after call...")
print(f"Call was at: {call_date}")

# Get minute data for the first few hours after the call
after_call_ts = call_ts + (4 * 3600)  # 4 hours after call
minute_data_after = fetch_ohlcv(network, token['pool_address'], 'minute', 240, after_call_ts)

if minute_data_after:
    # Filter for minutes right after the call
    first_hours = [c for c in minute_data_after if c[0] >= call_ts and c[0] <= call_ts + (4 * 3600)]
    
    if first_hours:
        print(f"\nFirst 4 hours after call ({len(first_hours)} candles):")
        for i, candle in enumerate(first_hours[:10]):  # Show first 10
            candle_time = datetime.fromtimestamp(candle[0])
            print(f"  {candle_time.strftime('%H:%M')} - O: ${candle[1]:.6f}, H: ${candle[2]:.6f}, C: ${candle[4]:.6f}")
        
        # Find the highest point in first 4 hours
        first_hours_ath = max(first_hours, key=lambda x: x[2])
        first_hours_realistic = max(first_hours_ath[1], first_hours_ath[4])
        first_hours_roi = max(0, ((first_hours_realistic - entry_price) / entry_price) * 100)
        
        print(f"\nHighest in first 4 hours: ${first_hours_realistic:.6f} (ROI: {first_hours_roi:.1f}%)")