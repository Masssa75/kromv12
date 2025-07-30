import requests
from datetime import datetime

# BIP177 data from our query
pool_address = "BVGfgtnn7Lyv5zP2LZJQa9zvYM9XoeShN3CHp1gEtj4d"
call_timestamp_str = "2025-05-18T15:39:00+00:00"
price_at_call = 0.0003666600
ticker = "BIP177"

# Convert to unix timestamp
call_dt = datetime.fromisoformat(call_timestamp_str.replace('+00:00', ''))
call_timestamp_unix = int(call_dt.timestamp())

print(f"{ticker} Analysis:")
print(f"Call date: {call_timestamp_str}")
print(f"Price at call: ${price_at_call:.10f}")

# Fetch OHLCV data
url = f"https://api.geckoterminal.com/api/v2/networks/solana/pools/{pool_address}/ohlcv/day"
response = requests.get(url, params={'aggregate': 1, 'limit': 365})
data = response.json()

if 'data' in data and 'attributes' in data['data']:
    ohlcv_list = data['data']['attributes']['ohlcv_list']
    
    # Find highest price after call
    ath_price = 0
    ath_date = None
    total_entries = 0
    
    for entry in ohlcv_list:
        if entry[0] >= call_timestamp_unix:
            total_entries += 1
            high = float(entry[2]) if entry[2] else 0
            if high > ath_price:
                ath_price = high
                ath_date = datetime.fromtimestamp(entry[0]).strftime('%Y-%m-%d')
    
    if ath_price > 0:
        ath_roi = ((ath_price - price_at_call) / price_at_call) * 100
        print(f"\nATH after call:")
        print(f"  Price: ${ath_price:.10f}")
        print(f"  Date: {ath_date}")
        print(f"  ROI: {ath_roi:+.2f}%")
        print(f"  Total days tracked: {total_entries}")
    else:
        print("No data found after call date")
else:
    print("Failed to fetch OHLCV data")
