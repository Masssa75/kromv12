import requests
from datetime import datetime

# BOOCHIE Solana data
pool_address = "3YVbTqHctR7SKCfdYSAJJACriMTfi5AC4uVtUcvCTtdY"
call_timestamp_unix = 1747738968
price_at_call = 0.0001078409
ticker = "BOOCHIE"
network = "solana"

# Convert timestamp to readable date
call_date = datetime.fromtimestamp(call_timestamp_unix).strftime('%Y-%m-%d %H:%M:%S UTC')

print(f"{ticker} (Solana) Analysis:")
print(f"Call date: {call_date}")
print(f"Price at call: ${price_at_call:.10f}")

# Fetch OHLCV data
url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/day"
response = requests.get(url, params={'aggregate': 1, 'limit': 365})
data = response.json()

if 'data' in data and 'attributes' in data['data']:
    ohlcv_list = data['data']['attributes']['ohlcv_list']
    
    # Find all prices after call
    prices_after_call = []
    
    for entry in ohlcv_list:
        if entry[0] >= call_timestamp_unix and entry[2]:
            prices_after_call.append({
                'timestamp': entry[0],
                'date': datetime.fromtimestamp(entry[0]).strftime('%Y-%m-%d'),
                'high': float(entry[2]),
                'low': float(entry[3]) if entry[3] else 0,
                'close': float(entry[4]) if entry[4] else 0
            })
    
    # Sort by high price
    prices_after_call.sort(key=lambda x: x['high'], reverse=True)
    
    if prices_after_call:
        print(f"\nTop 5 highest prices after call:")
        for i, price_data in enumerate(prices_after_call[:5]):
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
        
        # Check if ATH is positive
        if ath_roi > 0:
            print(f"\n✅ POSITIVE ATH FOUND\! This token went up {ath_roi:.2f}% from entry\!")
    else:
        print("No data found after call date")
else:
    print("Failed to fetch OHLCV data")
