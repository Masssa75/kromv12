#!/usr/bin/env python3
"""
Fix script to recalculate ATH for tokens where daily candle includes pre-call wicks.
This addresses the fundamental issue where daily candles aggregate full days and can
include prices from before the actual call time.
"""

import os
import sys
import json
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

# GeckoTerminal API
GECKO_API_KEY = os.getenv("GECKO_TERMINAL_API_KEY")
COINGECKO_PRO_API_BASE = "https://pro-api.coingecko.com/api/v3/onchain"

def fetch_ohlcv(network, pool_address, timeframe, limit=1000, before_timestamp=None):
    """Fetch OHLCV data from GeckoTerminal"""
    url = f"{COINGECKO_PRO_API_BASE}/networks/{network}/pools/{pool_address}/ohlcv/{timeframe}"
    
    params = {
        "aggregate": "1",
        "limit": str(limit)
    }
    if before_timestamp:
        params["before_timestamp"] = str(before_timestamp)
    
    headers = {}
    if GECKO_API_KEY and GECKO_API_KEY.startswith('CG-'):
        headers['x-cg-pro-api-key'] = GECKO_API_KEY
    
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        print(f"API Error: {response.status_code} - {response.text}")
        return []
    
    data = response.json()
    ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
    
    candles = []
    for candle in ohlcv_list:
        candles.append({
            'timestamp': candle[0],
            'open': candle[1] or 0,
            'high': candle[2] or 0,
            'low': candle[3] or 0,
            'close': candle[4] or 0,
            'volume': candle[5] or 0
        })
    
    return candles

def calculate_ath_properly(token):
    """Calculate ATH using only post-call data, without relying on daily candles"""
    
    # Determine call timestamp
    call_timestamp = None
    if token['buy_timestamp']:
        call_timestamp = datetime.fromisoformat(token['buy_timestamp'].replace('Z', '+00:00')).timestamp()
    elif token['raw_data'] and 'timestamp' in token['raw_data']:
        call_timestamp = token['raw_data']['timestamp']
    
    if not call_timestamp or not token['pool_address'] or not token['price_at_call']:
        return None
    
    call_datetime = datetime.fromtimestamp(call_timestamp, tz=timezone.utc)
    
    # Map network names
    network = token['network']
    if network == 'ethereum':
        network = 'eth'
    
    print(f"\nProcessing {token['ticker']} - Call at {call_datetime.isoformat()}")
    
    try:
        # NEW APPROACH: Start with hourly data instead of daily
        # This avoids the daily candle contamination issue
        
        # Fetch hourly data from call time forward (up to 30 days = 720 hours)
        now_timestamp = int(datetime.now(timezone.utc).timestamp())
        hourly_data = fetch_ohlcv(network, token['pool_address'], 'hour', 720, now_timestamp)
        
        # Filter to only hours after the call
        hourly_after_call = [c for c in hourly_data if c['timestamp'] >= call_timestamp and c['high'] > 0]
        
        if not hourly_after_call:
            print(f"  No hourly data after call")
            return None
        
        # Sort by high price to find ATH hour
        hourly_after_call.sort(key=lambda x: x['high'], reverse=True)
        hourly_ath = hourly_after_call[0]
        hourly_ath_time = datetime.fromtimestamp(hourly_ath['timestamp'], tz=timezone.utc)
        
        print(f"  Hourly ATH: ${hourly_ath['high']} at {hourly_ath_time.isoformat()}")
        
        # Now fetch minute data around that hour
        minute_before_ts = hourly_ath['timestamp'] + 3600  # 1 hour after
        minute_data = fetch_ohlcv(network, token['pool_address'], 'minute', 120, minute_before_ts)
        
        # Filter minutes around the ATH hour AND after call time
        minute_around_ath = [
            c for c in minute_data 
            if abs(c['timestamp'] - hourly_ath['timestamp']) <= 3600 
            and c['timestamp'] >= call_timestamp  # Must be after call
            and c['high'] > 0 
            and c['close'] > 0
        ]
        
        if minute_around_ath:
            # Find minute with highest price
            minute_around_ath.sort(key=lambda x: x['high'], reverse=True)
            minute_ath = minute_around_ath[0]
            
            # Use max of open/close as the realistic ATH
            best_price = max(minute_ath['open'], minute_ath['close'])
            ath_roi = ((best_price - token['price_at_call']) / token['price_at_call']) * 100
            
            minute_ath_time = datetime.fromtimestamp(minute_ath['timestamp'], tz=timezone.utc)
            print(f"  Minute ATH: ${minute_ath['high']} at {minute_ath_time.isoformat()}")
            print(f"  Using best price: ${best_price} (max of open/close)")
            print(f"  ATH ROI: {ath_roi:.2f}%")
            
            return {
                'ath_price': best_price,
                'ath_timestamp': minute_ath['timestamp'],
                'ath_roi_percent': max(0, ath_roi)
            }
        else:
            # Fall back to hourly data
            hourly_roi = ((hourly_ath['high'] - token['price_at_call']) / token['price_at_call']) * 100
            
            return {
                'ath_price': hourly_ath['high'],
                'ath_timestamp': hourly_ath['timestamp'],
                'ath_roi_percent': max(0, hourly_roi)
            }
            
    except Exception as e:
        print(f"  Error: {str(e)}")
        return None

def main():
    # Specifically check COMPANY token
    print("Checking COMPANY token with 73,193% ROI...")
    
    # Query COMPANY token with the specific ROI
    response = supabase.table('crypto_calls').select('*').eq('ticker', 'COMPANY').gte('ath_roi_percent', 73000).lte('ath_roi_percent', 74000).execute()
    
    if not response.data:
        print("COMPANY token not found with expected ROI")
        return
    
    print(f"Found {len(response.data)} COMPANY tokens with ROI around 73,193%")
    
    for token in response.data:  # Process all matching tokens
        print(f"\n{'='*60}")
        print(f"Token: {token['ticker']} - Current ATH ROI: {token['ath_roi_percent']:.2f}%")
        print(f"Contract: {token['contract_address']}")
        
        # Recalculate ATH properly
        new_ath = calculate_ath_properly(token)
        
        if new_ath:
            print(f"\nComparison:")
            print(f"  Current ATH: ${token['ath_price']} (ROI: {token['ath_roi_percent']:.2f}%)")
            print(f"  New ATH: ${new_ath['ath_price']} (ROI: {new_ath['ath_roi_percent']:.2f}%)")
            
            if abs(new_ath['ath_roi_percent'] - token['ath_roi_percent']) > 100:
                print(f"  SIGNIFICANT DIFFERENCE! Would update database.")
                
                # Uncomment to actually update:
                # supabase.table('crypto_calls').update({
                #     'ath_price': new_ath['ath_price'],
                #     'ath_timestamp': datetime.fromtimestamp(new_ath['ath_timestamp'], tz=timezone.utc).isoformat(),
                #     'ath_roi_percent': new_ath['ath_roi_percent']
                # }).eq('id', token['id']).execute()

if __name__ == "__main__":
    main()