import requests
import json
from datetime import datetime

def find_ath_since_call(pool_address, network, call_timestamp, ticker):
    """Find ATH since call timestamp using GeckoTerminal OHLCV data"""
    
    # Convert call timestamp to unix timestamp if it's a string
    if isinstance(call_timestamp, str):
        call_dt = datetime.fromisoformat(call_timestamp.replace('+00:00', '+00:00'))
        call_timestamp_unix = int(call_dt.timestamp())
    else:
        call_timestamp_unix = call_timestamp
    
    # Fetch OHLCV data
    url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/day"
    params = {
        'aggregate': 1,
        'limit': 365  # Get up to 1 year of data
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'data' not in data or 'attributes' not in data['data']:
            print(f"No data found for {ticker}")
            return None
            
        ohlcv_list = data['data']['attributes'].get('ohlcv_list', [])
        
        if not ohlcv_list:
            print(f"No OHLCV data for {ticker}")
            return None
        
        # Filter for entries after call timestamp
        ath_price = 0
        ath_timestamp = None
        entries_after_call = 0
        
        for entry in ohlcv_list:
            timestamp = entry[0]
            high = float(entry[2]) if entry[2] else 0
            
            if timestamp >= call_timestamp_unix:
                entries_after_call += 1
                if high > ath_price:
                    ath_price = high
                    ath_timestamp = timestamp
        
        if ath_price > 0:
            ath_date = datetime.fromtimestamp(ath_timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')
            return {
                'ath_price': ath_price,
                'ath_timestamp': ath_timestamp,
                'ath_date': ath_date,
                'entries_after_call': entries_after_call
            }
        else:
            print(f"No data found after call date for {ticker}")
            return None
            
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

# Test with TCM
result = find_ath_since_call(
    pool_address="FPDxQgk3vDJnQM1HH2D5SuLsmCDNTBRgSU5PZA5EkZDr",
    network="solana",
    call_timestamp="2025-05-18T15:11:00+00:00",
    ticker="TCM"
)

if result:
    print(f"\nTCM ATH since call:")
    print(f"  ATH Price: ${result['ath_price']:.10f}")
    print(f"  ATH Date: {result['ath_date']}")
    print(f"  Data points after call: {result['entries_after_call']}")
    
    # Calculate ROI
    price_at_call = 0.0000951165
    ath_roi = ((result['ath_price'] - price_at_call) / price_at_call) * 100
    print(f"  ATH ROI: {ath_roi:.2f}%")
