import requests
from datetime import datetime

# BOOCHIE Ethereum data
pool_address = "0x9392a42AbE7E8131E0956De4F8A0413f2a0e52BF"
call_timestamp = 1747688939  # Earliest call
price_at_call = 8E-10
ticker = "BOOCHIE"
group = "TopCallersChannel"

call_date = datetime.fromtimestamp(call_timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')

print(f"=== {ticker} ATH Analysis (HOURLY CANDLES) ===")
print(f"Group: {group}")
print(f"Call date: {call_date}")
print(f"Price at call: ${price_at_call:.12f}")

# Fetch HOURLY OHLCV data
url = f"https://api.geckoterminal.com/api/v2/networks/eth/pools/{pool_address}/ohlcv/hour"
response = requests.get(url, params={'aggregate': 1, 'limit': 1000})  # Get more hours
data = response.json()

if 'data' in data and 'attributes' in data['data']:
    ohlcv_list = data['data']['attributes']['ohlcv_list']
    
    # Find highest price after call
    prices_after_call = []
    
    for entry in ohlcv_list:
        if entry[0] >= call_timestamp and entry[2]:
            prices_after_call.append({
                'timestamp': entry[0],
                'datetime': datetime.fromtimestamp(entry[0]).strftime('%Y-%m-%d %H:%M'),
                'high': float(entry[2])
            })
    
    if prices_after_call:
        # Sort by high price
        prices_after_call.sort(key=lambda x: x['high'], reverse=True)
        
        # ATH with hourly precision
        ath = prices_after_call[0]
        ath_roi = ((ath['high'] - price_at_call) / price_at_call) * 100
        
        print(f"\n📈 ATH SUMMARY (Hourly Precision):")
        print(f"  Price: ${ath['high']:.12f}")
        print(f"  DateTime: {ath['datetime']}")
        print(f"  ROI: {ath_roi:,.2f}%")
        print(f"  Multiplier: {ath_roi/100 + 1:.1f}x")
        
        print(f"\n🔝 Top 5 hourly highs:")
        for i, price_data in enumerate(prices_after_call[:5]):
            roi = ((price_data['high'] - price_at_call) / price_at_call) * 100
            print(f"  {i+1}. {price_data['datetime']}: ${price_data['high']:.12f} ({roi:+.2f}%)")
