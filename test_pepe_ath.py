import requests
from datetime import datetime

# PEPE data
pool_address = "0x67F3Bc3B3EcBd68c79dffD22666a04e6d3f35b15"
call_timestamp_str = "2025-05-18T20:08:00+00:00"
price_at_call = 0.0011986615
ticker = "PEPE"
network = "eth"  # GeckoTerminal uses 'eth' not 'ethereum'

call_dt = datetime.fromisoformat(call_timestamp_str.replace('+00:00', ''))
call_timestamp_unix = int(call_dt.timestamp())

print(f"{ticker} Analysis:")
print(f"Network: {network}")
print(f"Call date: {call_timestamp_str}")
print(f"Price at call: ${price_at_call:.10f}")

# Fetch OHLCV data
url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/day"
response = requests.get(url, params={'aggregate': 1, 'limit': 365})
data = response.json()

if 'data' in data and 'attributes' in data['data']:
    ohlcv_list = data['data']['attributes']['ohlcv_list']
    
    # Find top 3 highest prices after call
    prices_after_call = []
    
    for entry in ohlcv_list:
        if entry[0] >= call_timestamp_unix and entry[2]:
            prices_after_call.append({
                'date': datetime.fromtimestamp(entry[0]).strftime('%Y-%m-%d'),
                'high': float(entry[2])
            })
    
    # Sort by price
    prices_after_call.sort(key=lambda x: x['high'], reverse=True)
    
    if prices_after_call:
        print(f"\nTop 3 prices after call:")
        for i, price_data in enumerate(prices_after_call[:3]):
            roi = ((price_data['high'] - price_at_call) / price_at_call) * 100
            print(f"{i+1}. {price_data['date']}: ${price_data['high']:.10f} (ROI: {roi:+.2f}%)")
        
        # ATH summary
        ath = prices_after_call[0]
        ath_roi = ((ath['high'] - price_at_call) / price_at_call) * 100
        print(f"\nATH Summary:")
        print(f"  Price: ${ath['high']:.10f}")
        print(f"  Date: {ath['date']}")
        print(f"  ROI: {ath_roi:+.2f}%")
        print(f"  Days tracked: {len(prices_after_call)}")
else:
    print("Failed to fetch OHLCV data")
    print(f"Response: {data}")
