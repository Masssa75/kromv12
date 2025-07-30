import requests
from datetime import datetime

# $ANIBTC data
ticker = "$ANIBTC"
network = "eth"  # GeckoTerminal uses 'eth'
group = "TopCallersChannel"
pool_address = "0x6c8333632509b4E814938D80d81b43789D4193BF"
call_timestamp = 1752760532
price_at_call = 2.279E-7
current_price = 0.0002092051873

# Convert timestamp to readable date
call_date = datetime.fromtimestamp(call_timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')

print(f"=== {ticker} ATH Analysis ===")
print(f"Group: {group}")
print(f"Network: ETHEREUM")
print(f"Call date: {call_date}")
print(f"Price at call: ${price_at_call:.12f}")
print(f"Current price: ${current_price:.10f}")
print(f"Current ROI: {((current_price - price_at_call) / price_at_call) * 100:,.2f}%")

# Fetch OHLCV data
url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/day"
response = requests.get(url, params={'aggregate': 1, 'limit': 365})
data = response.json()

if 'data' in data and 'attributes' in data['data']:
    ohlcv_list = data['data']['attributes']['ohlcv_list']
    
    prices_after_call = []
    for entry in ohlcv_list:
        if entry[0] >= call_timestamp and entry[2]:
            prices_after_call.append({
                'date': datetime.fromtimestamp(entry[0]).strftime('%Y-%m-%d'),
                'high': float(entry[2])
            })
    
    if prices_after_call:
        prices_after_call.sort(key=lambda x: x['high'], reverse=True)
        ath = prices_after_call[0]
        ath_roi = ((ath['high'] - price_at_call) / price_at_call) * 100
        
        print(f"\n📈 ATH SUMMARY:")
        print(f"  Price: ${ath['high']:.10f}")
        print(f"  Date: {ath['date']}")
        print(f"  ROI: {ath_roi:,.2f}%")
        print(f"  Multiplier: {ath_roi/100 + 1:,.1f}x")
