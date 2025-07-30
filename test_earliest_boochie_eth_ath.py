import requests
from datetime import datetime

# Earliest BOOCHIE Ethereum data
pool_address = "0x9392a42AbE7E8131E0956De4F8A0413f2a0e52BF"
call_timestamp_unix = 1747688939
price_at_call = 8E-10  # 0.0000000008
ticker = "BOOCHIE"
network = "eth"

# Convert timestamp to readable date
call_date = datetime.fromtimestamp(call_timestamp_unix).strftime('%Y-%m-%d %H:%M:%S UTC')

print(f"{ticker} (Ethereum - Earliest Call) Analysis:")
print(f"Call date: {call_date}")
print(f"Price at call: ${price_at_call:.12f}")
print(f"Current price: $0.000000000524")

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
                'high': float(entry[2])
            })
    
    # Sort by high price
    prices_after_call.sort(key=lambda x: x['high'], reverse=True)
    
    if prices_after_call:
        print(f"\nTop 5 highest prices after call:")
        for i, price_data in enumerate(prices_after_call[:5]):
            roi = ((price_data['high'] - price_at_call) / price_at_call) * 100
            print(f"{i+1}. {price_data['date']}: ${price_data['high']:.12f} (ROI: {roi:+.2f}%)")
        
        # ATH summary
        ath = prices_after_call[0]
        ath_roi = ((ath['high'] - price_at_call) / price_at_call) * 100
        print(f"\nATH Summary:")
        print(f"  Price: ${ath['high']:.12f}")
        print(f"  Date: {ath['date']}")
        print(f"  ROI: {ath_roi:+.2f}%")
        print(f"  Days tracked: {len(prices_after_call)}")
        
        # Calculate current ROI
        current_price = 5.24E-10
        current_roi = ((current_price - price_at_call) / price_at_call) * 100
        print(f"\nCurrent ROI: {current_roi:+.2f}%")
        
        # Check if ATH is positive
        if ath_roi > 0:
            print(f"\n✅ POSITIVE ATH FOUND\! This token went up {ath_roi:.2f}% from entry\!")
            print(f"   From ${price_at_call:.12f} to ${ath['high']:.12f}")
            print(f"   That's a {ath_roi/100 + 1:.1f}x return\!")
    else:
        print("No OHLCV data found after call date")
else:
    print("Failed to fetch OHLCV data")
