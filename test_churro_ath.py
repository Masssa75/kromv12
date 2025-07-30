import requests
from datetime import datetime

# CHURRO data
ticker = "CHURRO"
network = "solana"
group = "shitcoinneverland"
pool_address = "538XqnWJKY8QNDGiJz6FvsbhUA14owbLS9NEJJkz72Mr"
call_timestamp = 1753630948
price_at_call = 0.0000236802
current_price = 0.08552382910328012

# Convert timestamp to readable date
call_date = datetime.fromtimestamp(call_timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')

print(f"=== {ticker} ATH Analysis ===")
print(f"Group: {group}")
print(f"Network: {network.upper()}")
print(f"Call date: {call_date}")
print(f"Price at call: ${price_at_call:.10f}")
print(f"Current price: ${current_price:.10f}")
print(f"Current ROI: {((current_price - price_at_call) / price_at_call) * 100:,.2f}%")

# Fetch OHLCV data
url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/day"
response = requests.get(url, params={'aggregate': 1, 'limit': 365})
data = response.json()

if 'data' in data and 'attributes' in data['data']:
    ohlcv_list = data['data']['attributes']['ohlcv_list']
    
    # Find all prices after call
    prices_after_call = []
    
    for entry in ohlcv_list:
        if entry[0] >= call_timestamp and entry[2]:
            prices_after_call.append({
                'timestamp': entry[0],
                'date': datetime.fromtimestamp(entry[0]).strftime('%Y-%m-%d'),
                'high': float(entry[2])
            })
    
    # Sort by high price
    prices_after_call.sort(key=lambda x: x['high'], reverse=True)
    
    if prices_after_call:
        # ATH summary
        ath = prices_after_call[0]
        ath_roi = ((ath['high'] - price_at_call) / price_at_call) * 100
        
        print(f"\n📈 ATH SUMMARY:")
        print(f"  Price: ${ath['high']:.10f}")
        print(f"  Date: {ath['date']}")
        print(f"  ROI: {ath_roi:,.2f}%")
        print(f"  Multiplier: {ath_roi/100 + 1:,.1f}x")
        
        # Check if current price is ATH
        if abs(ath['high'] - current_price) < 0.01:
            print(f"  🚀 Currently at/near ATH\!")
