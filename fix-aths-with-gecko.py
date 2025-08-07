#!/usr/bin/env python3
"""
Fix incorrect ATHs using GeckoTerminal OHLCV data
Based on the working archived ATH update function
"""
import requests
import json
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
GECKO_API_KEY = os.getenv('GECKO_TERMINAL_API_KEY')
SUPABASE_ACCESS_TOKEN = os.getenv('SUPABASE_ACCESS_TOKEN')

print("ATH Fix Script using GeckoTerminal")
print("=" * 60)

# Network mapping for GeckoTerminal
NETWORK_MAP = {
    'ethereum': 'eth',
    'solana': 'solana',
    'bsc': 'bsc',
    'polygon': 'polygon',
    'arbitrum': 'arbitrum',
    'base': 'base',
    'avalanche': 'avalanche-c'
}

def fetch_ohlcv(network, pool_address, timeframe='day', limit=1000):
    """Fetch OHLCV data from GeckoTerminal"""
    url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/{timeframe}"
    params = {"aggregate": 1, "limit": limit, "currency": "usd"}
    headers = {"x-cg-pro-api-key": GECKO_API_KEY} if GECKO_API_KEY else {}
    
    response = requests.get(url, params=params, headers=headers, timeout=10)
    if response.status_code != 200:
        return []
    
    data = response.json()
    ohlcv_list = data.get("data", {}).get("attributes", {}).get("ohlcv_list", [])
    
    # Parse into candles
    candles = []
    for item in ohlcv_list:
        timestamp, open_price, high, low, close, volume = item
        candles.append({
            'timestamp': timestamp,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    return candles

def calculate_ath_from_ohlcv(token):
    """Calculate true ATH using 3-tier precision like the archived function"""
    ticker = token['ticker']
    network = token['network']
    pool_address = token['pool_address']
    price_at_call = token['price_at_call']
    
    # Get network name for GeckoTerminal
    gecko_network = NETWORK_MAP.get(network, network)
    
    # Parse call timestamp
    call_timestamp = token.get('buy_timestamp') or token.get('created_at')
    if call_timestamp:
        call_str = call_timestamp.replace("+00:00", "").split(".")[0]
        call_dt = datetime.strptime(call_str, "%Y-%m-%dT%H:%M:%S")
        call_unix = int(call_dt.timestamp())
    else:
        return None
    
    print(f"\n{ticker}: Fetching OHLCV data...")
    
    # Get start of call day (midnight) to avoid missing intraday peaks
    call_date = datetime.fromtimestamp(call_unix)
    call_date = call_date.replace(hour=0, minute=0, second=0, microsecond=0)
    call_day_start = int(call_date.timestamp())
    
    # TIER 1: Daily candles
    daily_data = fetch_ohlcv(gecko_network, pool_address, 'day', 1000)
    if not daily_data:
        print(f"  ⚠️ No daily data available")
        return None
    
    # Filter candles after call and find highest
    daily_after_call = [c for c in daily_data if c['timestamp'] >= call_day_start and c['high'] > 0]
    if not daily_after_call:
        print(f"  ⚠️ No daily data after call")
        return None
    
    # Sort by high price to find peak day
    daily_after_call.sort(key=lambda x: x['high'], reverse=True)
    peak_day = daily_after_call[0]
    
    print(f"  Peak day: ${peak_day['high']:.8f} on {datetime.fromtimestamp(peak_day['timestamp']).strftime('%Y-%m-%d')}")
    
    # TIER 2: Hourly precision around peak day
    time.sleep(0.5)  # Rate limit
    hourly_data = fetch_ohlcv(gecko_network, pool_address, 'hour', 168)  # 7 days of hourly
    
    if hourly_data:
        # Filter hourly data around peak day (±1 day)
        hourly_around_peak = [
            c for c in hourly_data 
            if abs(c['timestamp'] - peak_day['timestamp']) <= 86400
            and c['timestamp'] >= call_unix
            and c['high'] > 0
        ]
        
        if hourly_around_peak:
            hourly_around_peak.sort(key=lambda x: x['high'], reverse=True)
            peak_hour = hourly_around_peak[0]
            
            print(f"  Peak hour: ${peak_hour['high']:.8f} at {datetime.fromtimestamp(peak_hour['timestamp']).strftime('%Y-%m-%d %H:%M')}")
            
            # TIER 3: Minute precision around peak hour
            time.sleep(0.5)  # Rate limit
            minute_before_ts = peak_hour['timestamp'] + 3600
            minute_data = fetch_ohlcv(gecko_network, pool_address, 'minute', 120)
            
            if minute_data:
                # Filter minutes around peak hour
                minute_around_peak = [
                    c for c in minute_data
                    if abs(c['timestamp'] - peak_hour['timestamp']) <= 3600
                    and c['timestamp'] >= call_unix
                    and c['high'] > 0
                    and c['close'] > 0
                ]
                
                if minute_around_peak:
                    minute_around_peak.sort(key=lambda x: x['high'], reverse=True)
                    peak_minute = minute_around_peak[0]
                    
                    # Use the better of open or close as actual trading price
                    best_price = max(peak_minute['open'], peak_minute['close'])
                    
                    print(f"  Peak minute: ${best_price:.8f} at {datetime.fromtimestamp(peak_minute['timestamp']).strftime('%Y-%m-%d %H:%M')}")
                    
                    return {
                        'ath_price': best_price,
                        'ath_timestamp': datetime.fromtimestamp(peak_minute['timestamp']).isoformat() + 'Z',
                        'ath_roi_percent': max(0, ((best_price - price_at_call) / price_at_call) * 100)
                    }
            
            # Fallback to hourly precision
            best_price = max(peak_hour['open'], peak_hour['close'])
            return {
                'ath_price': best_price,
                'ath_timestamp': datetime.fromtimestamp(peak_hour['timestamp']).isoformat() + 'Z',
                'ath_roi_percent': max(0, ((best_price - price_at_call) / price_at_call) * 100)
            }
    
    # Fallback to daily precision
    best_price = max(peak_day['open'], peak_day['close'])
    return {
        'ath_price': best_price,
        'ath_timestamp': datetime.fromtimestamp(peak_day['timestamp']).isoformat() + 'Z',
        'ath_roi_percent': max(0, ((best_price - price_at_call) / price_at_call) * 100)
    }

# Fetch tokens with potentially incorrect ATHs
print("Fetching tokens to check...")
headers = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Content-Type": "application/json"
}

# Get top ROI tokens to verify
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
params = "?select=id,ticker,network,pool_address,price_at_call,ath_price,ath_roi_percent,buy_timestamp,created_at"
params += "&pool_address=not.is.null&price_at_call=not.is.null"
params += "&order=ath_roi_percent.desc.nullslast&limit=20"

response = requests.get(url + params, headers=headers)
if response.status_code != 200:
    print(f"Error fetching tokens: {response.status_code}")
    exit(1)

tokens = response.json()
if isinstance(tokens, str):
    print(f"Unexpected response: {tokens}")
    exit(1)

print(f"Checking {len(tokens)} top ROI tokens for accuracy...")
print("-" * 60)

fixed_count = 0
checked_count = 0

for token in tokens:
    if not token.get('pool_address') or not token.get('price_at_call'):
        continue
    
    checked_count += 1
    current_ath = token.get('ath_price', 0)
    current_roi = token.get('ath_roi_percent', 0)
    
    print(f"\n[{checked_count}/{len(tokens)}] {token['ticker']}")
    print(f"  Current ATH: ${current_ath:.8f} ({current_roi:.0f}% ROI)")
    
    # Calculate true ATH from OHLCV
    true_ath = calculate_ath_from_ohlcv(token)
    
    if true_ath:
        # Check if there's a significant difference (>5%)
        if abs(true_ath['ath_price'] - current_ath) / max(current_ath, 0.000001) > 0.05:
            print(f"  ✅ FIXING: True ATH is ${true_ath['ath_price']:.8f} ({true_ath['ath_roi_percent']:.0f}% ROI)")
            
            # Update using Management API for reliability
            update_query = f"""
                UPDATE crypto_calls 
                SET ath_price = {true_ath['ath_price']},
                    ath_roi_percent = {true_ath['ath_roi_percent']},
                    ath_timestamp = '{true_ath['ath_timestamp']}'::timestamptz,
                    ath_last_checked = NOW()
                WHERE id = '{token['id']}'
            """
            
            api_response = requests.post(
                "https://api.supabase.com/v1/projects/eucfoommxxvqmmwdbkdv/database/query",
                headers={
                    "Authorization": f"Bearer {SUPABASE_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={"query": update_query}
            )
            
            if api_response.status_code == 200:
                fixed_count += 1
                print(f"  ✅ Updated successfully!")
            else:
                print(f"  ❌ Update failed: {api_response.status_code}")
        else:
            print(f"  ✓ ATH is accurate")
    
    # Rate limiting
    time.sleep(2)  # Be conservative with API calls

print("\n" + "=" * 60)
print(f"Summary: Checked {checked_count} tokens, fixed {fixed_count} incorrect ATHs")
print("Script completed!")